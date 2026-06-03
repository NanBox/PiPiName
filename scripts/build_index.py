#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pipiname.stroke import StrokeLookupError, get_stroke_number, get_stroke_number_traditional  # noqa: E402
from pipiname.text import is_chinese, split_sentences, to_simplified, to_traditional  # noqa: E402

SOURCE_COLUMNS = {
    "shijing": ("data/诗经.json", "content"),
    "lunyu": ("data/论语.json", "paragraphs"),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="构建 PiPiName SQLite 索引")
    parser.add_argument("--data-dir", default=str(ROOT / "data"), help="原始 data 目录")
    parser.add_argument(
        "--output",
        default=str(ROOT / "src" / "pipiname" / "data" / "pipiname.sqlite3"),
        help="输出 SQLite 路径",
    )
    parser.add_argument(
        "--full-char-index",
        action="store_true",
        help="保留全量 sentence_chars。默认只保留候选命中字，减小发布索引体积。",
    )
    args = parser.parse_args()
    build_index(Path(args.data_dir), Path(args.output), full_char_index=args.full_char_index)
    return 0


def build_index(data_dir: Path, output: Path, full_char_index: bool = False) -> None:
    start = time.perf_counter()
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(".sqlite3.tmp")
    if tmp.exists():
        tmp.unlink()
    conn = sqlite3.connect(tmp)
    try:
        create_schema(conn)
        stats = {"sources": 0, "sentence_chars": 0, "valid_names": 0, "missing_chars": 0}
        valid_names = insert_valid_names(conn, data_dir)
        stats["valid_names"] = len(valid_names)
        candidate_counts: dict[tuple[str, str], int] = {}
        for source_type, path, column in iter_source_files(data_dir):
            inserted_sources, inserted_chars, missing_chars = insert_source_file(
                conn, source_type, path, column, valid_names, full_char_index, candidate_counts
            )
            stats["sources"] += inserted_sources
            stats["sentence_chars"] += inserted_chars
            stats["missing_chars"] += missing_chars
        conn.commit()
        create_indexes(conn)
        conn.commit()
    finally:
        conn.close()

    for data_name in ["stoke.dat", "chaizi-ft.dat"]:
        shutil.copy2(data_dir / data_name, output.parent / data_name)
    tmp.replace(output)
    elapsed = time.perf_counter() - start
    print(
        "索引构建完成: "
        f"sources={stats['sources']} "
        f"sentence_chars={stats['sentence_chars']} "
        f"valid_names={stats['valid_names']} "
        f"missing_chars={stats['missing_chars']} "
        f"output={output} "
        f"elapsed={elapsed:.2f}s"
    )


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        pragma journal_mode = off;
        pragma synchronous = off;
        drop table if exists sources;
        drop table if exists sentence_chars;
        drop table if exists valid_names;

        create table sources (
            id integer primary key,
            source_type text not null,
            title text not null,
            author text not null default '',
            sentence text not null
        );

        create table sentence_chars (
            sentence_id integer not null,
            position integer not null,
            char_trad text not null,
            char_simp text not null,
            stroke integer not null,
            primary key (sentence_id, position)
        );

        create table valid_names (
            name_simp text primary key,
            gender text not null,
            stroke1 integer not null,
            stroke2 integer not null
        );

        create table name_candidates (
            first_name text not null,
            stroke1 integer not null,
            stroke2 integer not null,
            sentence_id integer not null,
            first_position integer not null,
            second_position integer not null,
            first_char_trad text not null,
            second_char_trad text not null,
            first_char_simp text not null,
            second_char_simp text not null,
            primary key (first_name, sentence_id, first_position, second_position)
        );
        """
    )


def create_indexes(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        create index idx_sources_type on sources(source_type);
        create index idx_sentence_chars_stroke_sentence_position
            on sentence_chars(stroke, sentence_id, position);
        create index idx_sentence_chars_char_sentence_position
            on sentence_chars(char_simp, sentence_id, position);
        create index idx_valid_names_strokes on valid_names(stroke1, stroke2);
        create index idx_valid_names_gender on valid_names(gender);
        create index idx_name_candidates_strokes on name_candidates(stroke1, stroke2);
        create index idx_name_candidates_first_name on name_candidates(first_name);
        create index idx_name_candidates_sentence on name_candidates(sentence_id);
        create index idx_name_candidates_name_strokes on name_candidates(first_name, stroke1, stroke2);
        analyze;
        vacuum;
        """
    )


def insert_valid_names(conn: sqlite3.Connection, data_dir: Path) -> dict[str, tuple[str, int, int]]:
    names: dict[str, str] = {}
    with (data_dir / "Chinese_Names.dat").open(encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw_name, gender = line.split(",", 1)
            first_name = raw_name if len(raw_name) == 2 else raw_name[1:]
            first_name = to_simplified(first_name)
            if len(first_name) != 2:
                continue
            if first_name in names:
                if gender != names[first_name] or gender == "未知":
                    names[first_name] = "双"
            else:
                names[first_name] = gender

    rows = []
    for name, gender in sorted(names.items()):
        try:
            strokes = (get_stroke_number(name[0]), get_stroke_number(name[1]))
        except StrokeLookupError:
            continue
        rows.append((name, gender, strokes[0], strokes[1]))
    conn.executemany(
        "insert into valid_names(name_simp, gender, stroke1, stroke2) values (?, ?, ?, ?)",
        rows,
    )
    return {name: (gender, stroke1, stroke2) for name, gender, stroke1, stroke2 in rows}


def iter_source_files(data_dir: Path):
    yield "shijing", data_dir / "诗经.json", "content"
    yield "chuci", data_dir / "楚辞.txt", "txt"
    yield "lunyu", data_dir / "论语.json", "paragraphs"
    yield "zhouyi", data_dir / "周易.txt", "txt"
    for path in sorted((data_dir / "唐诗").glob("poet.tang.*.json")):
        yield "tangshi", path, "paragraphs"
    for path in sorted((data_dir / "宋诗").glob("poet.song.*.json")):
        yield "songshi", path, "paragraphs"
    for path in sorted((data_dir / "宋词").glob("ci.song.*.json")):
        yield "songci", path, "paragraphs"


def insert_source_file(
    conn: sqlite3.Connection,
    source_type: str,
    path: Path,
    column: str,
    valid_names: dict[str, tuple[str, int, int]],
    full_char_index: bool,
    candidate_counts: dict[tuple[str, str], int],
) -> tuple[int, int, int]:
    source_rows: list[tuple[str, str, str, str]] = []
    if column == "txt":
        title = {"chuci": "楚辞", "zhouyi": "周易"}[source_type]
        for text in path.read_text(encoding="utf-8-sig").splitlines():
            for sentence in split_sentences(to_traditional(text)):
                source_rows.append((source_type, title, "", sentence))
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data:
            title, author = source_title(source_type, item)
            for text in item.get(column, []):
                for sentence in split_sentences(to_traditional(text)):
                    source_rows.append((source_type, title, author, sentence))

    inserted_sources = 0
    inserted_chars = 0
    missing_chars = 0
    for row in source_rows:
        chars = []
        for position, ch in enumerate(row[3]):
            if not is_chinese(ch):
                continue
            try:
                stroke = get_stroke_number_traditional(ch)
            except StrokeLookupError:
                missing_chars += 1
                continue
            chars.append((position, ch, to_simplified(ch), stroke))
        if len(chars) < 2:
            continue
        candidate_rows_without_id = build_candidate_rows(source_type, chars, valid_names, candidate_counts)
        if not full_char_index and not candidate_rows_without_id:
            continue
        cursor = conn.execute(
            "insert into sources(source_type, title, author, sentence) values (?, ?, ?, ?)",
            row,
        )
        sentence_id = cursor.lastrowid
        candidate_rows = [
            (
                name,
                stroke1,
                stroke2,
                sentence_id,
                first_pos,
                second_pos,
                first_trad,
                second_trad,
                first_simp,
                second_simp,
            )
            for name, stroke1, stroke2, first_pos, second_pos, first_trad, second_trad, first_simp, second_simp
            in candidate_rows_without_id
        ]
        if candidate_rows:
            conn.executemany(
                """
                insert or ignore into name_candidates(
                    first_name, stroke1, stroke2, sentence_id, first_position, second_position,
                    first_char_trad, second_char_trad, first_char_simp, second_char_simp
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                candidate_rows,
            )
        char_rows = chars if full_char_index else chars_for_candidates(chars, candidate_rows)
        if char_rows:
            conn.executemany(
                """
                insert into sentence_chars(sentence_id, position, char_trad, char_simp, stroke)
                values (?, ?, ?, ?, ?)
                """,
                [(sentence_id, *char_row) for char_row in char_rows],
            )
        inserted_sources += 1
        inserted_chars += len(char_rows)
    return inserted_sources, inserted_chars, missing_chars


def build_candidate_rows(
    source_type: str,
    chars: list[tuple[int, str, str, int]],
    valid_names: dict[str, tuple[str, int, int]],
    candidate_counts: dict[tuple[str, str], int],
) -> list[tuple[str, int, int, int, int, str, str, str, str]]:
    rows: list[tuple[str, int, int, int, int, str, str, str, str]] = []
    for first_index, first in enumerate(chars):
        for second in chars[first_index + 1 :]:
            name = first[2] + second[2]
            valid = valid_names.get(name)
            if valid is None:
                continue
            count_key = (source_type, name)
            if candidate_counts.get(count_key, 0) >= 3:
                continue
            candidate_counts[count_key] = candidate_counts.get(count_key, 0) + 1
            rows.append((name, valid[1], valid[2], first[0], second[0], first[1], second[1], first[2], second[2]))
    return rows


def chars_for_candidates(
    chars: list[tuple[int, str, str, int]],
    candidate_rows: list[tuple[str, int, int, int, int, int, str, str, str, str]],
) -> list[tuple[int, str, str, int]]:
    if not candidate_rows:
        return []
    by_position = {item[0]: item for item in chars}
    positions = set()
    for row in candidate_rows:
        positions.add(row[4])
        positions.add(row[5])
    return [by_position[position] for position in sorted(positions) if position in by_position]


def source_title(source_type: str, item: dict[str, object]) -> tuple[str, str]:
    if source_type == "shijing":
        return f"诗经 {item.get('title', '')} {item.get('chapter', '')} {item.get('section', '')}".strip(), ""
    if source_type == "lunyu":
        return f"论语 {item.get('chapter', '')}".strip(), ""
    if source_type == "tangshi":
        return f"唐诗 {item.get('title', '')}".strip(), str(item.get("author", ""))
    if source_type == "songshi":
        return f"宋诗 {item.get('title', '')}".strip(), str(item.get("author", ""))
    if source_type == "songci":
        return f"宋词 {item.get('rhythmic', '')}".strip(), str(item.get("author", ""))
    return source_type, ""


if __name__ == "__main__":
    raise SystemExit(main())

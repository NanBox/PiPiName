from __future__ import annotations

import sqlite3
from importlib import resources
from pathlib import Path
from typing import Iterable

from .models import (
    NAME_GENDER_ANY,
    SOURCE_LABELS,
    TEXT_SOURCE_TYPES,
    GenerateOptions,
    NameCandidate,
    NameResource,
)
from .text import highlight, to_simplified

PACKAGE_DATA = resources.files("pipiname").joinpath("data")
REPO_DATA = Path(__file__).resolve().parents[2] / "data"
DEFAULT_DB_NAME = "pipiname.sqlite3"


def default_db_path() -> Path:
    package_db = PACKAGE_DATA.joinpath(DEFAULT_DB_NAME)
    if package_db.is_file():
        return Path(str(package_db))
    repo_db = Path(__file__).resolve().parent / "data" / DEFAULT_DB_NAME
    if repo_db.exists():
        return repo_db
    return REPO_DATA.parent / "src" / "pipiname" / "data" / DEFAULT_DB_NAME


class NameIndex:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path else default_db_path()
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"未找到 SQLite 索引: {self.db_path}。请先运行 python scripts/build_index.py"
            )

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def health(self) -> dict[str, object]:
        with self.connect() as conn:
            sources = conn.execute("select count(*) from sources").fetchone()[0]
            chars = conn.execute("select count(*) from sentence_chars").fetchone()[0]
            valid_names = conn.execute("select count(*) from valid_names").fetchone()[0]
        return {
            "ok": True,
            "db_path": str(self.db_path),
            "sources": sources,
            "sentence_chars": chars,
            "valid_names": valid_names,
        }

    def source_summary(self) -> list[dict[str, object]]:
        with self.connect() as conn:
            counts = dict(
                conn.execute(
                    "select source_type, count(*) as count from sources group by source_type"
                ).fetchall()
            )
        result = []
        for key, label in SOURCE_LABELS.items():
            if key in {"default", "all"}:
                continue
            result.append({"source": key, "label": label, "sentences": counts.get(key, 0)})
        result.append({"source": "default", "label": SOURCE_LABELS["default"], "sentences": 0})
        result.append({"source": "all", "label": SOURCE_LABELS["all"], "sentences": sum(counts.values())})
        return result

    def find_candidates(
        self,
        options: GenerateOptions,
        stroke_pairs: Iterable[tuple[int, int]],
    ) -> list[NameCandidate]:
        pair_values = list(stroke_pairs)
        if not pair_values:
            return []
        source_filter = self._source_filter(options.source)
        dislike = set(options.dislike_words)
        results: list[NameCandidate] = []
        seen: set[tuple[str, str, str, int, int]] = set()
        with self.connect() as conn:
            if options.source == "default":
                rows = self._query_default_names(conn, options, pair_values)
                for row in rows:
                    first_name = row["name_simp"]
                    if self._skip_name(first_name, dislike):
                        continue
                    results.append(
                        NameCandidate(
                            full_name=options.last_name + first_name,
                            first_name=first_name,
                            gender=row["gender"],
                            first_char=first_name[0],
                            second_char=first_name[1],
                            stroke1=row["stroke1"],
                            stroke2=row["stroke2"],
                            source_type="default",
                            source_title="常见姓名库",
                            author="",
                            sentence="",
                        )
                    )
                    if len(results) >= options.offset + options.limit:
                        break
                return results[options.offset : options.offset + options.limit]

            if options.validate_name:
                return self._query_validated_text_candidates(conn, options, pair_values, source_filter, dislike)

            # 发布版索引默认只保留常见姓名命中的字符位置。关闭姓名库筛选时仍返回
            # 预聚合候选，避免回退到全量字符 join 造成索引体积和查询成本失控。
            for stroke1, stroke2 in pair_values:
                rows = conn.execute(
                    f"""
                    select
                        s.source_type,
                        s.title,
                        s.author,
                        s.sentence,
                        nc.first_name,
                        nc.stroke1,
                        nc.stroke2,
                        nc.first_char_simp as first_char,
                        nc.second_char_simp as second_char,
                        nc.first_char_trad as first_char_trad,
                        nc.second_char_trad as second_char_trad,
                        v.gender as gender
                    from name_candidates nc
                    join sources s on s.id = nc.sentence_id
                    left join valid_names v on v.name_simp = nc.first_name
                    where nc.stroke1 = ?
                      and nc.stroke2 = ?
                      {source_filter}
                    order by nc.sentence_id, nc.first_position, nc.second_position
                    """,
                    (stroke1, stroke2),
                )
                for row in rows:
                    first_name = row["first_name"]
                    if self._skip_name(first_name, dislike):
                        continue
                    if options.validate_name and row["gender"] is None:
                        continue
                    gender = row["gender"] or ""
                    if not self._gender_matches(options.gender, gender):
                        continue
                    key = (first_name, row["source_type"], row["sentence"], row["stroke1"], row["stroke2"])
                    if key in seen:
                        continue
                    seen.add(key)
                    sentence = highlight(row["sentence"], row["first_char_trad"], row["second_char_trad"])
                    results.append(
                        NameCandidate(
                            full_name=options.last_name + first_name,
                            first_name=first_name,
                            gender=gender,
                            first_char=row["first_char"],
                            second_char=row["second_char"],
                            stroke1=row["stroke1"],
                            stroke2=row["stroke2"],
                            source_type=row["source_type"],
                            source_title=row["title"],
                            author=row["author"] or "",
                            sentence=sentence,
                        )
                    )
                    if len(results) >= options.offset + options.limit:
                        return results[options.offset : options.offset + options.limit]
        return results[options.offset : options.offset + options.limit]

    def _query_validated_text_candidates(
        self,
        conn: sqlite3.Connection,
        options: GenerateOptions,
        pair_values: list[tuple[int, int]],
        source_filter: str,
        dislike: set[str],
    ) -> list[NameCandidate]:
        pairs_sql = ",".join(["(?, ?)"] * len(pair_values))
        params: list[object] = [value for pair in pair_values for value in pair]
        gender_sql = ""
        if options.gender:
            gender_sql = "and (v.gender = ? or v.gender in ('双', '未知'))"
            params.append(options.gender)
        dislike_sql = ""
        if dislike:
            dislike_sql = "and " + " and ".join(["nc.first_name not like ?"] * len(dislike))
            params.extend([f"%{word}%" for word in dislike])
        rows = conn.execute(
            f"""
            select
                s.source_type,
                s.title,
                s.author,
                s.sentence,
                nc.first_name,
                nc.stroke1,
                nc.stroke2,
                nc.first_char_simp as first_char,
                nc.second_char_simp as second_char,
                nc.first_char_trad as first_char_trad,
                nc.second_char_trad as second_char_trad,
                v.gender as gender
            from name_candidates nc
            join valid_names v on v.name_simp = nc.first_name
            join sources s on s.id = nc.sentence_id
            where (nc.stroke1, nc.stroke2) in ({pairs_sql})
              {source_filter}
              {gender_sql}
              {dislike_sql}
            order by nc.sentence_id, nc.first_position, nc.second_position
            limit ?
            offset ?
            """,
            [*params, options.limit, options.offset],
        )
        results: list[NameCandidate] = []
        for row in rows:
            first_name = row["first_name"]
            if self._skip_name(first_name, dislike):
                continue
            sentence = highlight(row["sentence"], row["first_char_trad"], row["second_char_trad"])
            results.append(
                NameCandidate(
                    full_name=options.last_name + first_name,
                    first_name=first_name,
                    gender=row["gender"] or "",
                    first_char=row["first_char"],
                    second_char=row["second_char"],
                    stroke1=row["stroke1"],
                    stroke2=row["stroke2"],
                    source_type=row["source_type"],
                    source_title=row["title"],
                    author=row["author"] or "",
                    sentence=sentence,
                )
            )
        return results

    def find_resources(self, first_name: str, limit: int = 50) -> list[NameResource]:
        first = to_simplified(first_name[0])
        second = to_simplified(first_name[1])
        resources: list[NameResource] = []
        with self.connect() as conn:
            rows = conn.execute(
                """
                select s.source_type, s.title, s.author, s.sentence,
                       nc.first_char_trad as first_trad, nc.second_char_trad as second_trad
                from name_candidates nc
                join sources s on s.id = nc.sentence_id
                where nc.first_name = ?
                order by s.source_type, s.id, nc.first_position, nc.second_position
                limit ?
                """,
                (first + second, limit),
            )
            for row in rows:
                resources.append(
                    NameResource(
                        source_type=row["source_type"],
                        source_title=row["title"],
                        author=row["author"] or "",
                        sentence=highlight(row["sentence"], row["first_trad"], row["second_trad"]),
                    )
                )
        return resources

    def _source_filter(self, source: str) -> str:
        if source == "all":
            return ""
        if source not in TEXT_SOURCE_TYPES:
            return ""
        return f"and s.source_type = '{source}'"

    def _query_default_names(
        self,
        conn: sqlite3.Connection,
        options: GenerateOptions,
        stroke_pairs: list[tuple[int, int]],
    ) -> list[sqlite3.Row]:
        pairs_sql = ",".join(["(?, ?)"] * len(stroke_pairs))
        params: list[object] = [value for pair in stroke_pairs for value in pair]
        gender_sql = ""
        if options.gender:
            gender_sql = "and (gender = ? or gender in ('双', '未知'))"
            params.append(options.gender)
        return conn.execute(
            f"""
            select name_simp, gender, stroke1, stroke2
            from valid_names
            where (stroke1, stroke2) in ({pairs_sql})
              {gender_sql}
            order by name_simp
            """,
            params,
        ).fetchall()

    def _skip_name(self, first_name: str, dislike_words: set[str]) -> bool:
        return any(ch in dislike_words for ch in first_name)

    def _gender_matches(self, requested: str, gender: str) -> bool:
        if not requested:
            return True
        return gender == requested or gender in NAME_GENDER_ANY

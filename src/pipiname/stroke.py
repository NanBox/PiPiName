from __future__ import annotations

import re
from functools import lru_cache
from importlib import resources
from pathlib import Path

from .text import to_traditional

DATA_ROOT = Path(__file__).resolve().parents[2] / "data"
NUMBER_STROKES = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


class StrokeLookupError(ValueError):
    def __init__(self, chars: list[str]):
        self.chars = chars
        super().__init__("无法查到笔画: " + ", ".join(chars))


def _data_path(name: str) -> Path:
    package_path = resources.files("pipiname").joinpath("data", name)
    if package_path.is_file():
        return Path(str(package_path))
    return DATA_ROOT / name


@lru_cache(maxsize=1)
def load_stroke_dict() -> dict[str, int]:
    result: dict[str, int] = {}
    with _data_path("stoke.dat").open(encoding="utf-8") as f:
        for line in f:
            code, char, count = line.rstrip("\n").split("|")
            if code:
                result[char] = int(count)
    return result


@lru_cache(maxsize=1)
def load_split_dict() -> dict[str, tuple[str, ...]]:
    result: dict[str, tuple[str, ...]] = {}
    with _data_path("chaizi-ft.dat").open(encoding="utf-8") as f:
        for line in f:
            parts = re.split(r"\s+", line.strip())
            if len(parts) >= 2:
                result[parts[0]] = tuple(parts[1:])
    return result


@lru_cache(maxsize=20000)
def get_stroke_number(char_or_text: str) -> int:
    text = to_traditional(char_or_text)
    return get_stroke_number_traditional(text)


@lru_cache(maxsize=20000)
def get_stroke_number_traditional(text: str) -> int:
    stroke_dict = load_stroke_dict()
    missing: list[str] = []
    total = 0
    for ch in text:
        if ch in NUMBER_STROKES:
            total += NUMBER_STROKES[ch]
        elif ch in stroke_dict:
            total += stroke_dict[ch]
        else:
            missing.append(ch)
    if missing:
        raise StrokeLookupError(missing)
    return _apply_radical_rules(text, total)


def _apply_radical_rules(text: str, number: int) -> int:
    split_dict = load_split_dict()
    for ch in text:
        splits = split_dict.get(ch)
        if not splits:
            continue
        if "氵" in splits:
            number += 1
        if "扌" in splits:
            number += 1
        if splits[0] == "月":
            number += 2
        if "艹" in splits:
            number += 3
        if "辶" in splits:
            number += 4
        if splits[0] == "阜":
            number += 6
        if "邑" in splits and "阝" in splits:
            number += 5
        if splits[0] == "玉":
            number += 1
        if splits[0] == "示":
            number += 1
        if splits[0] == "衣":
            number += 1
        if splits[0] == "犬" or "犭" in splits:
            number += 1
        if splits[0] == "心":
            number += 1
    return number


def get_strokes_for_text(text: str) -> tuple[int, ...]:
    traditional = to_traditional(text)
    return tuple(get_stroke_number_traditional(ch) for ch in traditional)

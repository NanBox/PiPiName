from __future__ import annotations

import re
from functools import lru_cache

from opencc import OpenCC

SENTENCE_SPLIT_RE = re.compile(r"[！？，。,.?!\s]+")


@lru_cache(maxsize=4)
def _converter(config: str) -> OpenCC:
    return OpenCC(config)


def to_traditional(text: str) -> str:
    return _converter("s2t").convert(text)


def to_simplified(text: str) -> str:
    return _converter("t2s").convert(text)


def is_chinese(ch: str) -> bool:
    return "\u4e00" <= ch <= "\u9fff"


def split_sentences(text: str) -> list[str]:
    return [part.strip() for part in SENTENCE_SPLIT_RE.split(text) if part.strip()]


def highlight(sentence: str, first: str, second: str) -> str:
    return sentence.replace(first, f"「{first}」").replace(second, f"「{second}」")

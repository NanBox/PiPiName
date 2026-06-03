from __future__ import annotations

from dataclasses import asdict, dataclass


SOURCE_LABELS = {
    "default": "默认",
    "shijing": "诗经",
    "chuci": "楚辞",
    "lunyu": "论语",
    "zhouyi": "周易",
    "tangshi": "唐诗",
    "songshi": "宋诗",
    "songci": "宋词",
    "all": "全部",
}

DEFAULT_SOURCE = "shijing"
DEFAULT_OUTPUT_FORMAT = "tsv"
DEFAULT_OUTPUT_BY_FORMAT = {
    "tsv": "names.tsv",
    "csv": "names.csv",
    "json": "names.json",
}

TEXT_SOURCE_TYPES = tuple(k for k in SOURCE_LABELS if k not in {"default", "all"})

VALID_GENDERS = {"", "男", "女"}
NAME_GENDER_ANY = {"双", "未知"}


@dataclass(frozen=True)
class GenerateOptions:
    last_name: str
    source: str = DEFAULT_SOURCE
    gender: str = ""
    min_stroke: int = 3
    max_stroke: int = 30
    allow_general: bool = False
    validate_name: bool = True
    dislike_words: tuple[str, ...] = ()
    limit: int = 500
    offset: int = 0


@dataclass(frozen=True)
class NameCandidate:
    full_name: str
    first_name: str
    gender: str
    first_char: str
    second_char: str
    stroke1: int
    stroke2: int
    source_type: str
    source_title: str
    author: str
    sentence: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class GridItem:
    value: int
    kind: str


@dataclass(frozen=True)
class WugeReport:
    name: str
    complex_name: str
    strokes: tuple[int, int, int]
    tian: GridItem
    ren: GridItem
    di: GridItem
    zong: GridItem
    wai: GridItem
    sancai: str
    sancai_kind: str

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "complex_name": self.complex_name,
            "strokes": self.strokes,
            "tian": asdict(self.tian),
            "ren": asdict(self.ren),
            "di": asdict(self.di),
            "zong": asdict(self.zong),
            "wai": asdict(self.wai),
            "sancai": self.sancai,
            "sancai_kind": self.sancai_kind,
        }


@dataclass(frozen=True)
class NameResource:
    source_type: str
    source_title: str
    author: str
    sentence: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class CheckResult:
    report: WugeReport
    resources: tuple[NameResource, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "report": self.report.as_dict(),
            "resources": [resource.as_dict() for resource in self.resources],
        }

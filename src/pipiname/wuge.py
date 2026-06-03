from __future__ import annotations

from functools import lru_cache

from .models import GridItem, WugeReport
from .stroke import get_stroke_number, get_stroke_number_traditional
from .text import to_traditional

STROKE_GOODS = {
    1, 3, 5, 6, 7, 8, 11, 13, 15, 16, 17, 18, 21, 23, 24, 25, 29, 31, 32, 33,
    35, 37, 39, 41, 45, 47, 48, 52, 57, 61, 63, 65, 67, 68, 81,
}
STROKE_GENERALS = {27, 38, 42, 55, 58, 71, 72, 73, 77, 78}
STROKE_BADS = {
    2, 4, 9, 10, 12, 14, 19, 20, 22, 26, 28, 30, 34, 36, 40, 43, 44, 46,
    49, 50, 51, 53, 54, 56, 59, 60, 62, 64, 66, 69, 70, 74, 75, 76, 79, 80,
}

WUXING_GOODS = {
    "木木木", "木木火", "木木土", "木火木", "木火土", "木水木", "木水金", "木水水",
    "火木木", "火木火", "火木土", "火火木", "火火土", "火土火", "火土土", "火土金",
    "土火木", "土火火", "土火土", "土土火", "土土土", "土土金", "土金土", "土金金",
    "土金水", "金土火", "金土土", "金土金", "金金土", "金水木", "金水金", "水木木",
    "水木火", "水木土", "水木水", "水金土", "水金水", "水水木", "水水金",
}
WUXING_GENERALS = {
    "木火火", "木土火", "火木水", "火火火", "土木木", "土木火", "土土木", "金土木",
    "金金金", "金金水", "金水水", "水火木", "水土火", "水土土", "水土金", "水金金",
    "水水水",
}
WUXING_BADS = {
    "木木金", "木火金", "木火水", "木土木", "木土水", "木金木", "木金火", "木金土",
    "木金金", "木金水", "木水火", "木水土", "火木金", "火火金", "火火水", "火金木",
    "火金火", "火金金", "火金水", "火水木", "火水火", "火水土", "火水金", "火水水",
    "土木土", "土木金", "土木水", "土火水", "土土水", "土金木", "土金火", "土水木",
    "土水火", "土水土", "土水水", "金木木", "金木火", "金木土", "金木金", "金木水",
    "金火木", "金火金", "金火水", "金金木", "金水火", "水木金", "水火火", "水火土",
    "水火金", "水火水", "水土木", "水水土", "水金木", "水金火", "水水火", "木木水",
    "木土金", "火土木", "火土水", "土火金", "金土水", "火金土", "土水金", "金火火",
    "金火土", "木土土", "金水土",
}


def validate_single_last_double_name(name: str) -> None:
    if len(name) != 3:
        raise ValueError("仅支持单姓双字名，请输入 3 个汉字")


def get_wuxing(count: int) -> str:
    value = count % 10
    if value in {1, 2}:
        return "木"
    if value in {3, 4}:
        return "火"
    if value in {5, 6}:
        return "土"
    if value in {7, 8}:
        return "金"
    return "水"


def get_sancai_config(counts: tuple[int, int, int] | list[int]) -> str:
    return "".join(get_wuxing(count) for count in counts)


def get_stroke_type(stroke: int) -> str:
    if stroke in STROKE_GOODS:
        return "大吉"
    if stroke in STROKE_GENERALS:
        return "中吉"
    if stroke in STROKE_BADS:
        return "凶"
    return ""


def get_sancai_type(config: str) -> str:
    if config in WUXING_GOODS:
        return "大吉"
    if config in WUXING_GENERALS:
        return "中吉"
    if config in WUXING_BADS:
        return "凶"
    return ""


def check_sancai_good(counts: tuple[int, int, int] | list[int], allow_general: bool) -> bool:
    config = get_sancai_config(counts)
    return config in WUXING_GOODS or (allow_general and config in WUXING_GENERALS)


@lru_cache(maxsize=256)
def get_stroke_pairs(last_name: str, allow_general: bool = False) -> tuple[tuple[int, int], ...]:
    last_name_trad = to_traditional(last_name)
    n = get_stroke_number(last_name_trad)
    result: list[tuple[int, int]] = []
    for first in range(1, 82):
        for second in range(1, 82):
            tian = n + 1
            ren = n + first
            di = first + second
            zong = n + first + second
            wai = zong - ren + 1
            all_good = ren in STROKE_GOODS and di in STROKE_GOODS and zong in STROKE_GOODS and wai in STROKE_GOODS
            general_ok = (
                allow_general
                and ren in STROKE_GOODS | STROKE_GENERALS
                and di in STROKE_GOODS | STROKE_GENERALS
                and zong in STROKE_GOODS | STROKE_GENERALS
                and wai in STROKE_GOODS | STROKE_GENERALS
            )
            if (all_good or general_ok) and check_sancai_good((tian, ren, di), allow_general):
                result.append((first, second))
    return tuple(result)


def check_wuge(name: str) -> WugeReport:
    validate_single_last_double_name(name)
    complex_name = to_traditional(name)
    xing = get_stroke_number_traditional(complex_name[0])
    ming1 = get_stroke_number_traditional(complex_name[1])
    ming2 = get_stroke_number_traditional(complex_name[2])
    tian = xing + 1
    ren = xing + ming1
    di = ming1 + ming2
    zong = xing + ming1 + ming2
    wai = zong - ren + 1
    sancai = get_sancai_config((tian, ren, di))
    return WugeReport(
        name=name,
        complex_name=complex_name,
        strokes=(xing, ming1, ming2),
        tian=GridItem(tian, get_stroke_type(tian)),
        ren=GridItem(ren, get_stroke_type(ren)),
        di=GridItem(di, get_stroke_type(di)),
        zong=GridItem(zong, get_stroke_type(zong)),
        wai=GridItem(wai, get_stroke_type(wai)),
        sancai=sancai,
        sancai_kind=get_sancai_type(sancai),
    )

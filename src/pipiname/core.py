from __future__ import annotations

from .index import NameIndex
from .models import CheckResult, GenerateOptions, NameCandidate, SOURCE_LABELS, VALID_GENDERS
from .stroke import StrokeLookupError, get_stroke_number
from .wuge import check_wuge, get_stroke_pairs


class ValidationError(ValueError):
    pass


def normalize_dislike_words(words: tuple[str, ...]) -> tuple[str, ...]:
    chars: list[str] = []
    seen: set[str] = set()
    for word in words:
        for ch in word.strip():
            if ch.isspace() or ch in seen:
                continue
            chars.append(ch)
            seen.add(ch)
    return tuple(chars)


def validate_generate_options(options: GenerateOptions) -> None:
    if len(options.last_name) != 1:
        raise ValidationError("v1 仅支持单姓，请输入 1 个姓氏汉字")
    if options.source not in SOURCE_LABELS:
        raise ValidationError(f"未知词库: {options.source}")
    if options.gender not in VALID_GENDERS:
        raise ValidationError("gender 只能是空字符串、男或女")
    if options.gender and not options.validate_name:
        raise ValidationError("gender 非空时必须启用 validate_name")
    if options.min_stroke < 1 or options.max_stroke < options.min_stroke:
        raise ValidationError("笔画范围不合法")
    if options.limit < 1 or options.limit > 5000:
        raise ValidationError("limit 必须在 1 到 5000 之间")
    if options.offset < 0:
        raise ValidationError("offset 不能小于 0")
    try:
        get_stroke_number(options.last_name)
    except StrokeLookupError as exc:
        raise ValidationError(str(exc)) from exc


def normalize_generate_options(options: GenerateOptions) -> GenerateOptions:
    return GenerateOptions(
        last_name=options.last_name.strip(),
        source=options.source.strip(),
        gender=options.gender.strip(),
        min_stroke=options.min_stroke,
        max_stroke=options.max_stroke,
        allow_general=options.allow_general,
        validate_name=options.validate_name,
        dislike_words=normalize_dislike_words(options.dislike_words),
        limit=options.limit,
        offset=options.offset,
    )


def validate_check_name(name: str) -> None:
    name = name.strip()
    if len(name) != 3:
        raise ValidationError("仅支持单姓双字名，请输入 3 个汉字")
    try:
        for ch in name:
            get_stroke_number(ch)
    except StrokeLookupError as exc:
        raise ValidationError(str(exc)) from exc


def generate_names(options: GenerateOptions, index: NameIndex | None = None) -> list[NameCandidate]:
    options = normalize_generate_options(options)
    validate_generate_options(options)
    stroke_pairs = get_stroke_pairs(options.last_name, options.allow_general)
    filtered_pairs = tuple(
        pair for pair in stroke_pairs
        if options.min_stroke <= pair[0] <= options.max_stroke
        and options.min_stroke <= pair[1] <= options.max_stroke
    )
    return (index or NameIndex()).find_candidates(options, filtered_pairs)


def check_name(name: str, with_resource: bool = True, index: NameIndex | None = None) -> CheckResult:
    name = name.strip()
    validate_check_name(name)
    report = check_wuge(name)
    resources = ()
    if with_resource:
        resources = tuple((index or NameIndex()).find_resources(name[1:]))
    return CheckResult(report=report, resources=resources)

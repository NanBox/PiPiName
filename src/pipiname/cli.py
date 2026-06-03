from __future__ import annotations

import argparse
import csv
import json
import sys
import webbrowser
from pathlib import Path

from .api import create_app
from .core import ValidationError, check_name, generate_names
from .models import DEFAULT_OUTPUT_BY_FORMAT, DEFAULT_OUTPUT_FORMAT, GenerateOptions, NameCandidate, SOURCE_LABELS


def main(argv: list[str] | None = None, prog: str = "pipiname") -> int:
    parser = build_parser(prog=prog)
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ValidationError, FileNotFoundError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2


def build_parser(prog: str = "pipiname") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog, description="根据三才五格和古诗文生成中文双字名候选")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="生成名字候选")
    generate.add_argument("--last-name", required=True, help="单字姓氏，例如 林")
    generate.add_argument("--source", choices=SOURCE_LABELS.keys(), default="shijing", help="词库")
    generate.add_argument("--gender", choices=["", "男", "女"], default="", help="性别筛选")
    generate.add_argument("--min-stroke", type=int, default=3, help="名字单字最小笔画")
    generate.add_argument("--max-stroke", type=int, default=30, help="名字单字最大笔画")
    generate.add_argument("--allow-general", action="store_true", help="允许三才/五格中吉组合")
    generate.add_argument("--validate", dest="validate_name", action="store_true", default=True, help="启用常见姓名库筛选")
    generate.add_argument("--no-validate", dest="validate_name", action="store_false", help="关闭常见姓名库筛选")
    generate.add_argument("--dislike-words", default="", help="不想出现在名字中的字，例如 凶病")
    generate.add_argument("--limit", type=int, default=500, help="最多返回数量")
    generate.add_argument("--offset", type=int, default=0, help="跳过数量")
    generate.add_argument("--format", choices=["tsv", "csv", "json"], default=DEFAULT_OUTPUT_FORMAT, help="输出格式")
    generate.add_argument("--output", help="输出文件路径，使用 - 输出到 stdout；默认随格式选择 names.tsv/csv/json")
    generate.set_defaults(func=run_generate)

    check = subparsers.add_parser("check", help="查看姓名三才五格和来源")
    check.add_argument("name", help="单姓双字名，例如 周杰伦")
    check.add_argument("--with-resource", action="store_true", default=True, help="显示名字来源")
    check.add_argument("--no-resource", dest="with_resource", action="store_false", help="不显示名字来源")
    check.add_argument("--format", choices=["text", "json"], default="text", help="输出格式")
    check.set_defaults(func=run_check)

    web = subparsers.add_parser("web", help="启动本地 Web/API")
    web.add_argument("--host", default="localhost", help="监听地址")
    web.add_argument("--port", type=int, default=9191, help="监听端口")
    web.add_argument("--open", action="store_true", help="启动后打开浏览器")
    web.set_defaults(func=run_web)
    return parser


def run_generate(args: argparse.Namespace) -> int:
    options = GenerateOptions(
        last_name=args.last_name,
        source=args.source,
        gender=args.gender,
        min_stroke=args.min_stroke,
        max_stroke=args.max_stroke,
        allow_general=args.allow_general,
        validate_name=args.validate_name,
        dislike_words=tuple(args.dislike_words),
        limit=args.limit,
        offset=args.offset,
    )
    candidates = generate_names(options)
    text = format_candidates(candidates, args.format)
    output = args.output or DEFAULT_OUTPUT_BY_FORMAT[args.format]
    if output == "-":
        print(text, end="" if text.endswith("\n") else "\n")
    else:
        Path(output).write_text(text, encoding="utf-8")
        print(f"已输出 {len(candidates)} 条结果到 {output}")
    return 0


def run_check(args: argparse.Namespace) -> int:
    result = check_name(args.name, with_resource=args.with_resource)
    if args.format == "json":
        print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    else:
        print(format_check_result(result))
    return 0


def run_web(args: argparse.Namespace) -> int:
    import uvicorn

    url = f"http://{args.host}:{args.port}"
    if args.open:
        webbrowser.open(url)
    uvicorn.run(create_app(), host=args.host, port=args.port)
    return 0


def format_candidates(candidates: list[NameCandidate], output_format: str) -> str:
    rows = [candidate.as_dict() for candidate in candidates]
    if output_format == "json":
        return json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
    headers = [
        "full_name", "gender", "first_char", "second_char", "stroke1", "stroke2",
        "source_type", "source_title", "author", "sentence",
    ]
    delimiter = "\t" if output_format == "tsv" else ","
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers, delimiter=delimiter, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def format_check_result(result) -> str:
    report = result.report
    lines = [
        "",
        report.name,
        "",
        f"{report.complex_name} {report.strokes[0]} {report.strokes[1]} {report.strokes[2]}",
        "",
        f"天格\t{report.tian.value}\t{report.tian.kind}",
        f"人格\t{report.ren.value}\t{report.ren.kind}",
        f"地格\t{report.di.value}\t{report.di.kind}",
        f"总格\t{report.zong.value}\t{report.zong.kind}",
        f"外格\t{report.wai.value}\t{report.wai.kind}",
        "",
        f"三才\t{report.sancai}\t{report.sancai_kind}",
    ]
    if result.resources:
        lines.append("")
        for resource in result.resources:
            title = resource.source_title
            if resource.author:
                title += f" {resource.author}"
            lines.append(title)
            lines.append(resource.sentence)
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    raise SystemExit(main())

import argparse
import csv
import json
import os
import sys
from typing import Optional, List

from .parser import parse_casespecs_yaml, load_yaml
from .generator import to_excel_rows, TestCase, llm_items_to_cases, cases_to_json
from .llm_client import generate_llm_cases

try:
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
except Exception:  # pragma: no cover - optional import guard
    openpyxl = None


def _read_input(path: Optional[str]) -> str:
    if path:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return sys.stdin.read()

def _print_banner() -> None:
    banner = r"""
    _         _              _
   / \\  _   _| |_ ___   ___ | |___  ___
  / _ \\| | | | __/ _ \\ / _ \\| / __|/ _ \\
 / ___ \\ |_| | || (_) | (_) | \\__ \\  __/
/_/   \\_\\__,_|\\__\\___/ \\___/|_|___/\\___|
    """
    if sys.stdout.isatty():
        blue = "\033[94m"
        reset = "\033[0m"
        print(blue + banner + reset)
    else:
        print(banner)


def main() -> int:
    parser = argparse.ArgumentParser(description="AutoCase - 生成标准测试用例表格(Excel/CSV)")
    parser.add_argument("-f", "--file", help="输入YAML文件路径，不提供则从STDIN读取")
    parser.add_argument(
        "--llm-config",
        default="config/llm.yaml",
        help="大模型参数配置文件路径（当前版本仅读取校验）",
    )
    parser.add_argument(
        "--prompt",
        default="config/system_prompt.txt",
        help="系统级prompt文件路径（可编辑）",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="output.xlsx",
        help="输出文件路径（支持 .xlsx 或 .csv，默认 .xlsx）",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="关闭启动Banner显示",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="仅输出JSON到STDOUT，不生成Excel",
    )
    args = parser.parse_args()

    if len(sys.argv) == 1:
        _print_banner()
        parser.print_help()
        return 0

    if not args.no_banner:
        _print_banner()

    input_path = args.file
    if input_path is None and sys.stdin.isatty():
        parser.print_help()
        return 2

    input_dir = "inputs"
    output_dir = "outputs"

    if input_path and not os.path.isabs(input_path):
        if not os.path.exists(input_path):
            candidate = os.path.join(input_dir, input_path)
            if os.path.exists(candidate):
                input_path = candidate
    if input_path and not os.path.exists(input_path):
        print(f"输入文件不存在: {input_path}", file=sys.stderr)
        return 2

    output_path = args.output
    if output_path == "output.xlsx" and input_path:
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(output_dir, f"{base}_testcases.xlsx")
    elif not os.path.isabs(output_path):
        output_path = os.path.join(output_dir, output_path)

    text = _read_input(input_path)
    if not text.strip():
        print("未读取到输入内容", file=sys.stderr)
        return 2

    try:
        specs = parse_casespecs_yaml(text)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    # Read LLM config & system prompt (for validation/visibility)
    llm_text = _read_input(args.llm_config)
    try:
        llm_config = load_yaml(llm_text)
    except ValueError as e:
        print(f"LLM 配置错误: {e}", file=sys.stderr)
        return 2

    if not bool(llm_config.get("enabled", True)):
        print("LLM 已禁用，请在 llm.yaml 中设置 enabled: true", file=sys.stderr)
        return 2

    prompt_text = _read_input(args.prompt)
    if not prompt_text.strip():
        print("系统级prompt为空", file=sys.stderr)
        return 2

    cases: List[TestCase] = []
    next_index = 1
    for spec in specs:
        try:
            llm_items = generate_llm_cases(spec, llm_config, prompt_text)
            llm_cases, next_index = llm_items_to_cases(llm_items, spec, next_index)
            cases.extend(llm_cases)
        except Exception as e:
            print(f"LLM 生成失败: {e}", file=sys.stderr)
            return 2
    if args.json_only:
        print(json.dumps(cases_to_json(cases), ensure_ascii=False, indent=2))
        return 0

    output_parent = os.path.dirname(output_path)
    if output_parent:
        os.makedirs(output_parent, exist_ok=True)

    rows = to_excel_rows(cases)
    output_ext = os.path.splitext(output_path)[1].lower()
    if output_ext == ".csv":
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        print(f"已生成: {output_path}")
        return 0

    if openpyxl is None:
        print("缺少依赖: openpyxl，请先安装依赖", file=sys.stderr)
        return 2
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "TestCases"
    for row in rows:
        ws.append(row)

    # Styling
    header_fill = PatternFill("solid", fgColor="E8EEF7")
    header_font = Font(bold=True)
    thin = Side(border_style="thin", color="CBD5E1")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    wrap = Alignment(wrap_text=True, vertical="top")

    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
        for cell in row:
            cell.alignment = wrap
            cell.border = border
            if cell.row == 1:
                cell.fill = header_fill
                cell.font = header_font
            elif cell.row % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="F8FAFC")

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    # Column widths
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_len + 2, 60)

    wb.save(output_path)
    print(f"已生成: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

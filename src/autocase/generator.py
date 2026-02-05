from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

from .parser import CaseSpec


@dataclass
class TestCase:
    case_id: str
    module: str
    case_type: str
    name: str
    priority: str
    preconditions: str
    steps: str
    expected: str
    keywords: str


 


def to_excel_rows(cases: List[TestCase]) -> List[List[str]]:
    headers = [
        "用例ID",
        "所属模块",
        "用例类型",
        "用例名称",
        "优先级",
        "前置条件",
        "用例步骤",
        "预期结果",
        "关键词",
    ]
    rows = [headers]
    for c in cases:
        rows.append(
            [
                c.case_id,
                c.module,
                c.case_type,
                c.name,
                c.priority,
                c.preconditions,
                c.steps,
                c.expected,
                c.keywords,
            ]
        )
    return rows


def cases_to_json(cases: List[TestCase]) -> List[Dict[str, Any]]:
    data = []
    for c in cases:
        data.append(
            {
                "case_id": c.case_id,
                "module": c.module,
                "case_type": c.case_type,
                "name": c.name,
                "priority": c.priority,
                "preconditions": c.preconditions,
                "steps": c.steps,
                "expected": c.expected,
                "keywords": c.keywords,
            }
        )
    return data


def llm_items_to_cases(
    items: List[Dict[str, Any]],
    spec: CaseSpec,
    start_index: int,
) -> Tuple[List[TestCase], int]:
    cases: List[TestCase] = []
    next_index = start_index
    module_code = _derive_module_code(spec)
    module_label = _module_label(spec.module)
    for item in items:
        type_value = item.get("type", [])
        if isinstance(type_value, list):
            type_value = ", ".join(type_value)
        steps = item.get("steps", [])
        if isinstance(steps, list):
            steps_text = "\n".join([f"{i + 1}. {s}" for i, s in enumerate(steps)])
        else:
            steps_text = _normalize_numbered_text(str(steps))
        expected = item.get("expected", "")
        if isinstance(expected, list):
            expected_text = "\n".join([f"{i + 1}. {s}" for i, s in enumerate(expected)])
        else:
            expected_text = _normalize_numbered_text(str(expected))
        name = str(item.get("name", ""))
        if module_label and not name.startswith(f"[{module_label}]"):
            name = f"[{module_label}] {name}"
        cases.append(
            TestCase(
                case_id=f"{module_code}-{next_index:04d}",
                module=spec.module,
                case_type=str(type_value),
                name=name,
                priority=str(item.get("priority", "P2")),
                preconditions=str(item.get("pre", "")),
                steps=steps_text,
                expected=expected_text,
                keywords=", ".join(spec.keywords),
            )
        )
        next_index += 1
    return cases, next_index


def _normalize_numbered_text(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if len(lines) <= 1:
        return f"1. {cleaned}"
    return "\n".join([f"{i + 1}. {line}" for i, line in enumerate(lines)])


def _module_label(module: str) -> str:
    if not module:
        return ""
    parts = [p.strip() for p in module.split("/") if p.strip()]
    return parts[-1] if parts else module.strip()


def _derive_module_code(spec: CaseSpec) -> str:
    raw = (spec.module_code or "").strip()
    if raw:
        return raw.upper()
    # Fallback: keep ASCII letters/digits from module, use initials.
    cleaned = []
    for ch in spec.module:
        if ch.isascii() and (ch.isalnum() or ch in (" ", "-", "_", "/")):
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    words = [w for w in "".join(cleaned).replace("/", " ").split() if w]
    if not words:
        return "MOD"
    initials = "".join([w[0] for w in words]).upper()
    return initials or "MOD"

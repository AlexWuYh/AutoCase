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
    steps: List[str]
    expected: List[str]
    keywords: str
    stage: str


_ALLOWED_STAGES = [
    "单元测试阶段",
    "功能测试阶段",
    "集成测试阶段",
    "系统测试阶段",
    "冒烟测试阶段",
    "版本验证阶段",
]


def to_excel_rows(cases: List[TestCase]) -> List[List[str]]:
    headers = [
        "用例ID",
        "所属模块",
        "用例名称",
        "前置条件",
        "步骤",
        "预期",
        "关键词",
        "优先级",
        "用例类型",
        "适用阶段",
    ]
    rows = [headers]
    for c in cases:
        steps_text = "\n".join([f"{i + 1}. {s}" for i, s in enumerate(c.steps)])
        expected_text = "\n".join([f"{i + 1}. {s}" for i, s in enumerate(c.expected)])
        rows.append(
            [
                c.case_id,
                c.module,
                c.name,
                c.preconditions,
                steps_text,
                expected_text,
                c.keywords,
                c.priority,
                c.case_type,
                c.stage,
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
                "stage": c.stage,
            }
        )
    return data


def _normalize_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if "\n" in text:
            return [line.strip() for line in text.splitlines() if line.strip()]
        return [text]
    if value is None:
        return []
    return [str(value).strip()]


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
        raw_steps = item.get("steps", [])
        steps_list = _normalize_list(raw_steps)
        if len(steps_list) > 4:
            steps_list = steps_list[:4]
        raw_expected = item.get("expected", [])
        expected_list = _normalize_list(raw_expected)
        if len(expected_list) < len(steps_list):
            expected_list += [""] * (len(steps_list) - len(expected_list))
        elif len(expected_list) > len(steps_list):
            expected_list = expected_list[: len(steps_list)]

        stage_value = item.get("stage", item.get("适用阶段", ""))
        stage_text = str(stage_value).strip()
        if stage_text not in _ALLOWED_STAGES:
            stage_text = "功能测试阶段"
        name = str(item.get("name", ""))
        if module_label and not name.startswith(f"[{module_label}]"):
            name = f"[{module_label}] {name}"
        cases.append(
            TestCase(
                case_id=f"{module_code}-{next_index:04d}",
                module=spec.module,
                case_type=str(type_value),
                name=name,
                priority=str(item.get("priority", "2")),
                preconditions=str(item.get("pre", "")),
                steps=steps_list,
                expected=expected_list,
                keywords=", ".join(spec.keywords),
                stage=stage_text,
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

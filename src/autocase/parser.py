from dataclasses import dataclass
from typing import List, Dict, Any

try:
    import yaml
except Exception:  # pragma: no cover - optional import guard
    yaml = None


@dataclass
class CaseSpec:
    module: str
    feature: str
    description: str
    keywords: List[str]


_REQUIRED_KEYS = ["module", "feature", "description", "keywords"]
_ALIASES = {
    "模块": "module",
    "功能": "feature",
    "描述": "description",
    "关键词": "keywords",
}


def parse_casespecs_yaml(text: str) -> List[CaseSpec]:
    """Parse CaseSpec list from YAML text.

    Supported formats:
    1) Top-level list
    2) Top-level dict with `cases: [...]`
    3) Multi-doc YAML separated by '---'
    """
    if yaml is None:
        raise RuntimeError("缺少依赖: pyyaml，请先安装依赖")

    docs = list(yaml.safe_load_all(text))
    if not docs:
        raise ValueError("输入格式错误：YAML 为空")

    specs: List[CaseSpec] = []
    for data in docs:
        if data is None:
            continue
        if isinstance(data, list):
            specs.extend(_parse_list(data))
        elif isinstance(data, dict) and "cases" in data and isinstance(data["cases"], list):
            specs.extend(_parse_list(data["cases"]))
        elif isinstance(data, dict):
            specs.append(_parse_one(data))
        else:
            raise ValueError("输入格式错误：不支持的 YAML 结构")
    if not specs:
        raise ValueError("未解析到任何用例输入")
    return specs


def _normalize_keywords(raw: Any) -> List[str]:
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.replace("，", ",").split(",")]
        return [p for p in parts if p]
    return []


def load_yaml(text: str) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("缺少依赖: pyyaml，请先安装依赖")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("策略配置格式错误：YAML 顶层必须是对象")
    return data


def _parse_list(items: List[Any]) -> List[CaseSpec]:
    specs = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("输入格式错误：cases 列表元素必须是对象")
        specs.append(_parse_one(item))
    return specs


def _parse_one(data: Dict[str, Any]) -> CaseSpec:
    # Normalize alias keys (Chinese -> English)
    normalized = {}
    for k, v in data.items():
        key = _ALIASES.get(k, k)
        normalized[key] = v

    missing = [k for k in _REQUIRED_KEYS if k not in normalized]
    if missing:
        raise ValueError(f"缺少必填字段: {', '.join(missing)}")

    module = str(normalized["module"]).strip()
    feature = str(normalized["feature"]).strip()
    description = str(normalized["description"]).strip()
    keywords = _normalize_keywords(normalized["keywords"])

    return CaseSpec(
        module=module,
        feature=feature,
        description=description,
        keywords=keywords,
    )

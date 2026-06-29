"""YAML import/export for requirement groups. Reuses autocase.parser to keep
the on-disk format identical to the CLI's input format.
"""
from __future__ import annotations

from io import StringIO
from typing import Iterable, List

import yaml
from autocase.parser import CaseSpec, parse_casespecs_yaml

from ..models.requirement import Requirement
from ..models.requirement_group import RequirementGroup


def parse_yaml_to_specs(text: str) -> List[CaseSpec]:
    """Parse a YAML string into a list of CaseSpec objects.

    Raises ValueError on invalid YAML. Uses autocase.parser for format compat.
    """
    if not text or not text.strip():
        raise ValueError("YAML 内容为空")
    try:
        return parse_casespecs_yaml(text)
    except (yaml.YAMLError, ValueError) as e:
        raise ValueError(f"YAML 解析失败: {e}") from e


def specs_from_requirements(requirements: Iterable[Requirement]) -> List[dict]:
    """Build a list of dicts from DB requirement rows (for YAML export)."""
    items: List[dict] = []
    for r in requirements:
        items.append(
            {
                "module": r.module,
                "feature": r.feature,
                "description": r.description,
                "keywords": list(r.keywords or []),
            }
        )
    return items


def render_group_to_yaml(group: RequirementGroup) -> str:
    """Render a requirement group as a YAML string (CLI-compatible format)."""
    payload = {"cases": specs_from_requirements(group.requirements)}
    stream = StringIO()
    yaml.safe_dump(
        payload,
        stream,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=120,
    )
    return stream.getvalue()

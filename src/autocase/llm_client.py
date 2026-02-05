import json
import os
from typing import Any, Dict, List

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional import guard
    OpenAI = None

from .parser import CaseSpec


def generate_llm_cases(
    spec: CaseSpec,
    llm_config: Dict[str, Any],
    system_prompt: str,
) -> List[Dict[str, Any]]:
    if OpenAI is None:
        raise RuntimeError("缺少依赖: openai，请先安装依赖")

    api_key_env = llm_config.get("api_key_env", "OPENAI_API_KEY")
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise RuntimeError(f"未找到API Key环境变量: {api_key_env}")

    base_url = llm_config.get("base_url") or None
    if base_url:
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=api_key)
    model = llm_config.get("model", "gpt-4o-mini")

    user_prompt = _build_user_prompt(spec)
    max_retries = int(llm_config.get("retry_count", 2))
    retry_suffix = llm_config.get(
        "retry_prompt_suffix",
        "再次提醒：只输出JSON数组，不要包含任何解释或其它文本。",
    )

    last_text = ""
    for attempt in range(max_retries + 1):
        prompt = user_prompt if attempt == 0 else f"{user_prompt}\n\n{retry_suffix}"
        text = _call_model(client, model, llm_config, system_prompt, prompt)
        last_text = text
        items = _parse_json_list(text)
        if items:
            return items
    raise RuntimeError("LLM 未返回有效 JSON 数组")


def _build_user_prompt(spec: CaseSpec) -> str:
    keywords = ", ".join(spec.keywords)
    return (
        "请基于以下功能点补充测试用例，要求返回 JSON 数组。\n"
        "仅输出 JSON，不要解释。\n\n"
        "输入：\n"
        f"模块: {spec.module}\n"
        f"功能: {spec.feature}\n"
        f"描述: {spec.description}\n"
        f"关键词: {keywords}\n\n"
        "输出 JSON 数组元素字段：\n"
        "- type: 用例类型（数组或字符串）\n"
        "- name: 用例名称\n"
        "- priority: P0/P1/P2/P3\n"
        "- pre: 前置条件\n"
        "- steps: 步骤数组\n"
        "- expected: 预期结果\n\n"
        "不要包含 用例ID、所属模块、关键词 字段。"
    )


def _call_model(
    client: OpenAI,
    model: str,
    llm_config: Dict[str, Any],
    system_prompt: str,
    user_prompt: str,
) -> str:
    api_mode = llm_config.get("api_mode", "responses")
    if api_mode == "chat_completions":
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=llm_config.get("temperature", 0.2),
            max_tokens=llm_config.get("max_tokens", 2000),
            top_p=llm_config.get("top_p", 1.0),
            frequency_penalty=llm_config.get("frequency_penalty", 0.0),
            presence_penalty=llm_config.get("presence_penalty", 0.0),
        )
        return _extract_chat_text(response)
    response = client.responses.create(
        model=model,
        instructions=system_prompt,
        input=user_prompt,
        temperature=llm_config.get("temperature", 0.2),
        max_output_tokens=llm_config.get("max_tokens", 2000),
        top_p=llm_config.get("top_p", 1.0),
        frequency_penalty=llm_config.get("frequency_penalty", 0.0),
        presence_penalty=llm_config.get("presence_penalty", 0.0),
    )
    return _extract_text(response)


def _extract_text(response: Any) -> str:
    # SDK provides output_text helper in some versions
    if hasattr(response, "output_text"):
        return response.output_text
    # Fallback to structured content
    try:
        return response.output[0].content[0].text
    except Exception:
        return ""


def _extract_chat_text(response: Any) -> str:
    try:
        return response.choices[0].message.content or ""
    except Exception:
        return ""


def _parse_json_list(text: str) -> List[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [d for d in data if isinstance(d, dict)]
    except Exception:
        return []
    return []

import json
import os
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional import guard
    OpenAI = None

from .parser import CaseSpec


def _env_flag(name: str) -> Optional[bool]:
    raw = os.getenv(name)
    if raw is None:
        return None
    return raw.strip().lower() in ("1", "true", "yes", "y", "on")


def generate_llm_cases(
    spec: CaseSpec,
    llm_config: Dict[str, Any],
    system_prompt: str,
) -> List[Dict[str, Any]]:
    if OpenAI is None:
        raise RuntimeError("缺少依赖: openai，请先安装依赖")

    api_key_env = os.getenv(
        "AUTOCASE_API_KEY_ENV",
        llm_config.get("api_key_env", "OPENAI_API_KEY"),
    )
    allow_empty_key = _env_flag("AUTOCASE_ALLOW_EMPTY_KEY")
    if allow_empty_key is None:
        allow_empty_key = bool(llm_config.get("allow_empty_key", False))
    api_key = None
    if api_key_env:
        api_key = os.getenv(api_key_env)
    if not api_key and not allow_empty_key:
        missing = api_key_env or "(empty)"
        raise RuntimeError(f"未找到API Key环境变量: {missing}")
    if not api_key and allow_empty_key:
        # OpenAI SDK still requires a non-empty api_key; local compatible servers can ignore it.
        api_key = "EMPTY"

    base_url = os.getenv("AUTOCASE_BASE_URL", llm_config.get("base_url") or "") or None
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)
    model = os.getenv("AUTOCASE_MODEL", llm_config.get("model", "gpt-4o-mini"))

    user_prompt = _build_user_prompt(spec)
    max_retries = int(llm_config.get("retry_count", 2))
    retry_suffix = llm_config.get(
        "retry_prompt_suffix",
        "再次提醒：只输出JSON数组，不要包含任何解释或其它文本。",
    )

    debug_log = _env_flag("AUTOCASE_DEBUG_LOG")
    if debug_log is None:
        debug_log = bool(llm_config.get("debug_log", False))
    for attempt in range(max_retries + 1):
        prompt = user_prompt if attempt == 0 else f"{user_prompt}\n\n{retry_suffix}"
        text = _call_model(client, model, llm_config, system_prompt, prompt)
        items = _parse_json_list(text)
        if items:
            return items
        if debug_log:
            _log_invalid_response(text, attempt)
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
        "- steps: 步骤数组（最多4步）\n"
        "- expected: 预期结果数组（与步骤严格一一对应）\n"
        "- stage: 适用阶段（单选：单元测试阶段/功能测试阶段/集成测试阶段/系统测试阶段/冒烟测试阶段/版本验证阶段）\n\n"
        "不要包含 用例ID、所属模块、关键词 字段。"
    )


def _call_model(
    client: OpenAI,
    model: str,
    llm_config: Dict[str, Any],
    system_prompt: str,
    user_prompt: str,
) -> str:
    api_mode = os.getenv("AUTOCASE_API_MODE", llm_config.get("api_mode", "responses"))
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
    text = _strip_think(text).strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [d for d in data if isinstance(d, dict)]
    except Exception:
        # Try to salvage a JSON array embedded in other text (e.g., with <think>).
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            snippet = text[start : end + 1]
            try:
                data = json.loads(snippet)
                if isinstance(data, list):
                    return [d for d in data if isinstance(d, dict)]
            except Exception:
                return []
        return []
    return []


def generate_module_code(
    module_name: str,
    llm_config: Dict[str, Any],
) -> str:
    if OpenAI is None:
        raise RuntimeError("缺少依赖: openai，请先安装依赖")

    api_key_env = os.getenv(
        "AUTOCASE_API_KEY_ENV",
        llm_config.get("api_key_env", "OPENAI_API_KEY"),
    )
    allow_empty_key = _env_flag("AUTOCASE_ALLOW_EMPTY_KEY")
    if allow_empty_key is None:
        allow_empty_key = bool(llm_config.get("allow_empty_key", False))
    api_key = None
    if api_key_env:
        api_key = os.getenv(api_key_env)
    if not api_key and not allow_empty_key:
        missing = api_key_env or "(empty)"
        raise RuntimeError(f"未找到API Key环境变量: {missing}")
    if not api_key and allow_empty_key:
        api_key = "EMPTY"

    base_url = os.getenv("AUTOCASE_BASE_URL", llm_config.get("base_url") or "") or None
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)
    model = os.getenv("AUTOCASE_MODEL", llm_config.get("model", "gpt-4o-mini"))

    prompt = (
        "请为以下中文模块名称生成一个英文缩写前缀，要求：\n"
        "1) 只输出 2-6 位大写英文字母\n"
        "2) 不要输出解释或其它文本\n"
        f"模块名称: {module_name}\n"
        "输出示例: ORG"
    )
    text = _call_model(client, model, llm_config, "你是缩写生成器。", prompt)
    cleaned = _strip_think(text).strip().upper()
    # Extract leading letters
    letters = "".join([ch for ch in cleaned if ch.isalpha()])
    if len(letters) < 2:
        return "MOD"
    return letters[:6]


def _log_invalid_response(text: str, attempt: int) -> None:
    think_text = _extract_think(text)
    output_text = _strip_think(text).strip().replace("\r\n", "\n")
    if len(think_text) > 2000:
        think_text = think_text[:2000] + "\n...[truncated]..."
    if len(output_text) > 2000:
        output_text = output_text[:2000] + "\n...[truncated]..."
    if think_text:
        print(
            f"[debug] LLM think (attempt {attempt + 1}):\n{think_text}",
            file=os.sys.stderr,
        )
    print(
        f"[debug] LLM output (attempt {attempt + 1}) not valid JSON array:\n{output_text}",
        file=os.sys.stderr,
    )


def _strip_think(text: str) -> str:
    # Remove common chain-of-thought wrapper tags.
    if not text:
        return ""
    cleaned = text
    for open_tag, close_tag in (("<think>", "</think>"), ("<analysis>", "</analysis>")):
        while True:
            start = cleaned.find(open_tag)
            if start == -1:
                break
            end = cleaned.find(close_tag, start + len(open_tag))
            if end == -1:
                # If unclosed, remove the tag and continue (best-effort preserve content).
                cleaned = cleaned[:start] + cleaned[start + len(open_tag) :]
                break
            cleaned = cleaned[:start] + cleaned[end + len(close_tag) :]
    return cleaned


def _extract_think(text: str) -> str:
    if not text:
        return ""
    blocks = []
    for open_tag, close_tag in (("<think>", "</think>"), ("<analysis>", "</analysis>")):
        start = 0
        while True:
            s = text.find(open_tag, start)
            if s == -1:
                break
            e = text.find(close_tag, s + len(open_tag))
            if e == -1:
                blocks.append(text[s + len(open_tag) :].strip())
                break
            blocks.append(text[s + len(open_tag) : e].strip())
            start = e + len(close_tag)
    return "\n---\n".join([b for b in blocks if b])

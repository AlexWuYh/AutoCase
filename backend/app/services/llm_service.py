"""Simple LLM connectivity test wrapper — reuses the existing autocase LLM client
module but with a minimal prompt for smoketesting configuration.
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]


def test_llm_connection(config: Dict[str, Any], test_message: str = "Say OK") -> str:
    """Send a minimal request through the configured LLM provider.

    Returns the model's text response. Raises RuntimeError on failure.
    """
    if OpenAI is None:
        raise RuntimeError("缺少依赖: openai")

    api_key_env = config.get("api_key_env", "OPENAI_API_KEY")
    api_key = None
    if api_key_env:
        api_key = os.getenv(api_key_env)
    allow_empty = bool(config.get("allow_empty_key", False))
    if not api_key and not allow_empty:
        raise RuntimeError(f"未找到 API Key 环境变量: {api_key_env}")
    if not api_key and allow_empty:
        api_key = "EMPTY"

    base_url = config.get("base_url") or None
    client_kwargs: Dict[str, Any] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url

    client = OpenAI(**client_kwargs)
    model = config.get("model", "gpt-4o-mini")
    api_mode = config.get("api_mode", "chat_completions")
    extra_body = config.get("extra_body") or None

    start = time.perf_counter()
    if api_mode == "chat_completions":
        kwargs = dict(
            model=model,
            messages=[{"role": "user", "content": test_message}],
            temperature=0.0,
            max_tokens=50,
        )
        if extra_body:
            kwargs["extra_body"] = extra_body
        response = client.chat.completions.create(**kwargs)
        reply = response.choices[0].message.content or ""
    else:
        kwargs = dict(
            model=model,
            input=test_message,
            temperature=0.0,
            max_output_tokens=50,
        )
        if extra_body:
            kwargs["extra_body"] = extra_body
        response = client.responses.create(**kwargs)
        if hasattr(response, "output_text"):
            reply = response.output_text or ""
        else:
            reply = response.output[0].content[0].text or ""  # type: ignore[union-attr,index]

    elapsed = time.perf_counter() - start
    return f"[{elapsed * 1000:.0f}ms] {reply.strip()}"

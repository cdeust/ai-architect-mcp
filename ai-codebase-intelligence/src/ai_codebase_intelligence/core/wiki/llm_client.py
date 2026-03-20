"""LLM client — 1:1 port of gitnexus core/wiki/llm-client.js.

OpenAI-compatible API client. Supports OpenAI, Azure, LiteLLM, Ollama.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

from ...storage.repo_manager import load_cli_config


def resolve_llm_config(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    saved = load_cli_config()
    ov = overrides or {}
    return {
        "apiKey": (
            ov.get("apiKey")
            or os.environ.get("GITNEXUS_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or saved.get("apiKey", "")
        ),
        "baseUrl": (
            ov.get("baseUrl")
            or os.environ.get("GITNEXUS_LLM_BASE_URL")
            or saved.get("baseUrl", "https://openrouter.ai/api/v1")
        ),
        "model": (
            ov.get("model")
            or os.environ.get("GITNEXUS_MODEL")
            or saved.get("model", "minimax/minimax-m2.5")
        ),
        "maxTokens": ov.get("maxTokens", 16384),
        "temperature": ov.get("temperature", 0),
    }


def estimate_tokens(text: str) -> int:
    return len(text) // 4 + 1


def call_llm(
    prompt: str,
    config: dict[str, Any],
    system_prompt: str = "",
) -> dict[str, Any]:
    import urllib.request
    import urllib.error

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    url = config["baseUrl"].rstrip("/") + "/chat/completions"
    body = {
        "model": config["model"],
        "messages": messages,
        "max_tokens": config["maxTokens"],
        "temperature": config["temperature"],
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['apiKey']}",
    }

    max_retries = 3
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url, data=json.dumps(body).encode("utf-8"),
                headers=headers, method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            choice = (data.get("choices") or [{}])[0]
            content = (choice.get("message") or {}).get("content", "")
            if not content:
                raise RuntimeError("LLM returned empty response")

            return {
                "content": content,
                "promptTokens": (data.get("usage") or {}).get("prompt_tokens"),
                "completionTokens": (data.get("usage") or {}).get("completion_tokens"),
            }
        except urllib.error.HTTPError as e:
            last_error = e
            if e.code == 429 and attempt < max_retries - 1:
                time.sleep(3)
                continue
            if e.code >= 500 and attempt < max_retries - 1:
                time.sleep((attempt + 1) * 2)
                continue
            raise RuntimeError(f"LLM API error ({e.code}): {e.read().decode()[:500]}") from e
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 3)
                continue
            raise

    raise last_error or RuntimeError("LLM call failed after retries")

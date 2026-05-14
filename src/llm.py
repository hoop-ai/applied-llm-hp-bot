"""OpenRouter HTTP client + message assembly.

Single entry point: `call(user_message, context, history)`. Wraps the prompt
template, makes the chat-completions call, returns the model's text. Falls
through a small list of free models if the configured one is unavailable.
"""

from __future__ import annotations

import json
import os
from typing import Iterable

import requests
from dotenv import load_dotenv

from .prompts import build_prompt

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# Default: less-popular free models that aren't rate-limited as aggressively.
# The headline 70B models on OpenRouter free tier are typically saturated.
DEFAULT_MODEL = "z-ai/glm-4.5-air:free"

FALLBACK_MODELS = [
    "z-ai/glm-4.5-air:free",
    "openai/gpt-oss-20b:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "openai/gpt-oss-120b:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    # Paid tail. Reliable and cheap; only reached when every free model above
    # has refused or rate-limited the request, so day-to-day cost is ~zero.
    "anthropic/claude-haiku-4.5",
]


class LLMError(RuntimeError):
    pass


def _api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        raise LLMError("OPENROUTER_API_KEY is not set. Edit .env or set the env var.")
    return key


def _post(model: str, system_text: str, user_text: str) -> str:
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "HP-Bot Course Project",
    }
    payload = {
        "model": model,
        "temperature": 0.0,
        "max_tokens": 400,
        "messages": [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
    }
    resp = requests.post(OPENROUTER_URL, headers=headers, data=json.dumps(payload), timeout=60)
    if resp.status_code != 200:
        raise LLMError(f"OpenRouter {resp.status_code}: {resp.text[:300]}")
    body = resp.json()
    choices = body.get("choices") or []
    if not choices:
        raise LLMError(f"OpenRouter returned no choices: {body}")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if content is None:
        # Some models (or moderation passes) return null content; treat as failure
        # so we can try the next fallback model.
        raise LLMError(f"OpenRouter returned null content from {model}: {body}")
    return content.strip()


def _candidate_models() -> Iterable[str]:
    configured = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL).strip()
    yield configured
    for m in FALLBACK_MODELS:
        if m != configured:
            yield m


def call(user_message: str, context: str, history: str) -> str:
    """Single call point. Builds the full prompt and tries fallback models.

    On total failure (every model in the chain raised), re-raises the last
    LLMError instead of disguising the outage as a behavioral REFUSAL. The
    pipeline catches this and renders a visible "service unavailable" string.
    """
    full_prompt = build_prompt(context=context, history=history, user_message=user_message)
    last_error: LLMError | None = None
    for model in _candidate_models():
        try:
            return _post(model=model, system_text=full_prompt, user_text=user_message)
        except LLMError as e:
            last_error = e
            continue
    assert last_error is not None  # loop ran at least once
    raise last_error

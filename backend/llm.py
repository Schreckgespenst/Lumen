"""Ollama integration. Wraps chat + JSON parsing with graceful fallback."""
import json
import os
import re
from typing import Any, Dict, List, Optional

from ollama import Client

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME = os.environ.get("LUMEN_MODEL", "gemma4")

_client = Client(host=OLLAMA_HOST)


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort JSON extraction. Handles fenced blocks and stray prose."""
    if not text:
        return None
    text = text.strip()
    # Strip ```json fences if present
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        candidate = fence.group(1)
    else:
        # Find the first { ... last } span
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = text[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def chat_json(
    system_prompt: str,
    user_message: str,
    image_b64: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Call the LLM and parse a JSON reply.

    Falls back to a `general` intent with raw text in `reply_markdown` if the
    model returns invalid JSON.
    """
    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    user_msg: Dict[str, Any] = {"role": "user", "content": user_message}
    if image_b64:
        # Ollama python client accepts `images` as list of base64 strings.
        user_msg["images"] = [image_b64]
    messages.append(user_msg)

    try:
        response = _client.chat(
            model=MODEL_NAME,
            messages=messages,
            format="json",
            options={"temperature": 0.3},
        )
    except Exception as e:  # noqa: BLE001
        return {
            "intent": "general",
            "reply_markdown": f"_LLM error: {e}_",
            "food_entries": [],
            "follow_up_options": [],
            "_error": str(e),
        }

    raw = response.get("message", {}).get("content", "") if isinstance(response, dict) else getattr(response.message, "content", "")
    parsed = _extract_json(raw)
    if parsed is None:
        return {
            "intent": "general",
            "reply_markdown": raw or "_(empty response)_",
            "food_entries": [],
            "follow_up_options": [],
            "_raw": raw,
        }

    parsed.setdefault("intent", "general")
    parsed.setdefault("reply_markdown", "")
    parsed.setdefault("food_entries", [])
    parsed.setdefault("follow_up_options", [])
    return parsed


def chat_plain(system_prompt: str, user_message: str) -> str:
    """Plain text chat call used for the profile-learning side request."""
    try:
        response = _client.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            options={"temperature": 0.1},
        )
    except Exception as e:  # noqa: BLE001
        return f'{{"_error": "{e}"}}'
    return response.get("message", {}).get("content", "") if isinstance(response, dict) else getattr(response.message, "content", "")

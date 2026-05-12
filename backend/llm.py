"""LLM backend. Switchable between local Ollama and cloud Groq.

Set `LUMEN_BACKEND` to "ollama" (default) or "groq".
- Ollama:  uses LUMEN_MODEL (default "gemma4") and OLLAMA_HOST.
- Groq:    uses LUMEN_MODEL (default "llama-3.1-8b-instant") and GROQ_API_KEY.

Both implementations expose the same two entry points used by the chat route:
`chat_json` (JSON-mode reply) and `chat_plain` (free-form text, used for the
profile-learning side call).
"""
import json
import os
import re
from typing import Any, Dict, List, Optional


def _backend() -> str:
    return os.environ.get("LUMEN_BACKEND", "ollama").lower()


def _model() -> str:
    if "LUMEN_MODEL" in os.environ:
        return os.environ["LUMEN_MODEL"]
    return "llama-3.1-8b-instant" if _backend() == "groq" else "gemma4"


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort JSON extraction. Handles fenced blocks and stray prose."""
    if not text:
        return None
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        candidate = fence.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = text[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


# ---------- Ollama ----------

def _ollama_client():
    from ollama import Client
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    return Client(host=host)


def _ollama_chat_raw(
    system_prompt: str,
    user_message: str,
    image_b64: Optional[str],
    history: Optional[List[Dict[str, str]]],
    json_mode: bool,
    temperature: float,
) -> str:
    client = _ollama_client()
    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    user_msg: Dict[str, Any] = {"role": "user", "content": user_message}
    if image_b64:
        user_msg["images"] = [image_b64]
    messages.append(user_msg)

    kwargs: Dict[str, Any] = {
        "model": _model(),
        "messages": messages,
        "options": {"temperature": temperature},
    }
    if json_mode:
        kwargs["format"] = "json"

    response = client.chat(**kwargs)
    if isinstance(response, dict):
        return response.get("message", {}).get("content", "")
    return getattr(response.message, "content", "")


# ---------- Groq ----------

def _groq_client():
    from groq import Groq
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Get a free key at https://console.groq.com/keys"
        )
    return Groq(api_key=api_key)


def _groq_chat_raw(
    system_prompt: str,
    user_message: str,
    image_b64: Optional[str],
    history: Optional[List[Dict[str, str]]],
    json_mode: bool,
    temperature: float,
) -> str:
    client = _groq_client()
    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    if image_b64:
        # Llama 3.1 8B is text-only; surface the limitation rather than 500.
        user_message = (
            user_message
            + "\n\n[Note: an image was attached but the current LLM backend "
            "(text-only) cannot read it. Describe the photo in words to log it.]"
        )
    messages.append({"role": "user", "content": user_message})

    kwargs: Dict[str, Any] = {
        "model": _model(),
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    completion = client.chat.completions.create(**kwargs)
    return completion.choices[0].message.content or ""


# ---------- Dispatch ----------

def _chat_raw(
    system_prompt: str,
    user_message: str,
    image_b64: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
    json_mode: bool = True,
    temperature: float = 0.3,
) -> str:
    if _backend() == "groq":
        return _groq_chat_raw(system_prompt, user_message, image_b64, history, json_mode, temperature)
    return _ollama_chat_raw(system_prompt, user_message, image_b64, history, json_mode, temperature)


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
    try:
        raw = _chat_raw(system_prompt, user_message, image_b64, history, json_mode=True)
    except Exception as e:  # noqa: BLE001
        return {
            "intent": "general",
            "reply_markdown": f"_LLM error: {e}_",
            "food_entries": [],
            "follow_up_options": [],
            "_error": str(e),
        }

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
    """Plain-text chat call used for the profile-learning side request."""
    try:
        return _chat_raw(system_prompt, user_message, json_mode=False, temperature=0.1)
    except Exception as e:  # noqa: BLE001
        return f'{{"_error": "{e}"}}'

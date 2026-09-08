"""
AI-Powered Text Parsing Module

Provides LLM-powered text parsing using various AI providers.
Supports OpenAI, Anthropic, Grok, Gemini, Mistral, Groq, Cohere, Together, DeepSeek, Perplexity.
No external dependencies - uses urllib only.
"""

import json
import os
from contextvars import ContextVar
import urllib.request
import urllib.error
from urllib.parse import quote
from typing import Any, Dict, Optional


_STRICT = ContextVar("respondo_ai_strict", default=False)


class AIError(Exception):
    """Sanitized AI failure; contains a category and optional HTTP status only."""

    def __init__(self, code: str, status_code: Optional[int] = None):
        self.code = code
        self.status_code = status_code
        super().__init__("Respondo AI: " + code.replace("_", " ") +
                         (f" (HTTP {status_code})" if status_code is not None else ""))


def _failure(code, status=None):
    if _STRICT.get():
        raise AIError(code, status) from None
    return ""


def _get_api_key(provider: str) -> str:
    """Get API key from environment variable."""
    env_vars = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "grok": "GROK_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "groq": "GROQ_API_KEY",
        "cohere": "COHERE_API_KEY",
        "together": "TOGETHER_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "perplexity": "PERPLEXITY_API_KEY",
    }
    var_name = env_vars.get(provider, "")
    return os.environ.get(var_name, "")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _open_request(request, timeout):
    # A fresh opener avoids global urllib state and refuses credential forwarding.
    return urllib.request.build_opener(_NoRedirect()).open(request, timeout=timeout)


def _http_post(url: str, headers: dict, payload: dict, response_path: list) -> str:
    """Extract text; report fixed error categories, never raw exceptions/bodies."""
    code, status = "invalid_response", None
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with _open_request(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            for key in response_path:
                if isinstance(key, int):
                    if isinstance(result, list) and 0 <= key < len(result):
                        result = result[key]
                    else:
                        raise ValueError("invalid response shape")
                else:
                    if isinstance(result, dict) and key in result:
                        result = result[key]
                    else:
                        raise ValueError("invalid response shape")
            if not isinstance(result, str) or not result:
                raise ValueError("missing response text")
            return result
    except urllib.error.HTTPError as exc:
        status = exc.code if isinstance(exc.code, int) and 100 <= exc.code <= 599 else None
        code = "authentication" if status in (401, 403) else "rate_limit" if status == 429 else "http_error"
        try:
            exc.close()
        except Exception:
            # Cleanup must not replace the sanitized request failure.
            pass
    except TimeoutError:
        code = "timeout"
    except urllib.error.URLError as exc:
        code = "timeout" if isinstance(exc.reason, TimeoutError) else "connection"
    except OSError:
        code = "connection"
    except (ValueError, TypeError, KeyError, UnicodeError):
        code = "invalid_response"
    except Exception:
        code = "request_error"
    # Raise outside the except suite so no raw exception survives as __context__.
    return _failure(code, status)


def _schema_content(prompt, text, schema):
    content = f"{prompt}\n\n{text}"
    if schema is not None:
        content += "\n\nRespond with JSON matching this schema:\n" + json.dumps(schema, allow_nan=False)
    return content


def _call_openai(prompt: str, text: str, api_key: str, model: str, schema: Optional[dict]) -> str:
    """Call OpenAI API."""
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": f"{prompt}\n\n{text}"}],
    }
    if schema is not None:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "response", "strict": True, "schema": schema}
        }
    return _http_post(url, headers, payload, ["choices", 0, "message", "content"])


def _call_anthropic(prompt: str, text: str, api_key: str, model: str, schema: Optional[dict]) -> str:
    """Call Anthropic API."""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    content = f"{prompt}\n\n{text}"
    if schema is not None:
        content += f"\n\nRespond with JSON matching this schema:\n{json.dumps(schema)}"
    payload = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": content}],
    }
    return _http_post(url, headers, payload, ["content", 0, "text"])


def _call_grok(prompt: str, text: str, api_key: str, model: str, schema: Optional[dict]) -> str:
    """Call Grok (xAI) API - OpenAI compatible."""
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": _schema_content(prompt, text, schema)}],
    }
    if schema is not None:
        payload["response_format"] = {"type": "json_object"}
    return _http_post(url, headers, payload, ["choices", 0, "message", "content"])


def _call_gemini(prompt: str, text: str, api_key: str, model: str, schema: Optional[dict]) -> str:
    """Call Google Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{quote(model, safe='')}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    content = f"{prompt}\n\n{text}"
    if schema is not None:
        content += f"\n\nRespond with JSON matching this schema:\n{json.dumps(schema)}"
    payload: dict = {
        "contents": [{"parts": [{"text": content}]}],
    }
    if schema is not None:
        payload["generationConfig"] = {"responseMimeType": "application/json"}
    return _http_post(url, headers, payload, ["candidates", 0, "content", "parts", 0, "text"])


def _call_mistral(prompt: str, text: str, api_key: str, model: str, schema: Optional[dict]) -> str:
    """Call Mistral API."""
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": _schema_content(prompt, text, schema)}],
    }
    if schema is not None:
        payload["response_format"] = {"type": "json_object"}
    return _http_post(url, headers, payload, ["choices", 0, "message", "content"])


def _call_groq(prompt: str, text: str, api_key: str, model: str, schema: Optional[dict]) -> str:
    """Call Groq API - OpenAI compatible."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": _schema_content(prompt, text, schema)}],
    }
    if schema is not None:
        payload["response_format"] = {"type": "json_object"}
    return _http_post(url, headers, payload, ["choices", 0, "message", "content"])


def _call_cohere(prompt: str, text: str, api_key: str, model: str, schema: Optional[dict]) -> str:
    """Call Cohere API."""
    url = "https://api.cohere.com/v2/chat"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    content = f"{prompt}\n\n{text}"
    if schema is not None:
        content += f"\n\nRespond with JSON matching this schema:\n{json.dumps(schema)}"
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
    }
    if schema is not None:
        payload["response_format"] = {"type": "json_object"}
    return _http_post(url, headers, payload, ["message", "content", 0, "text"])


def _call_together(prompt: str, text: str, api_key: str, model: str, schema: Optional[dict]) -> str:
    """Call Together AI API - OpenAI compatible."""
    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": f"{prompt}\n\n{text}"}],
    }
    if schema is not None:
        payload["response_format"] = {"type": "json_object", "schema": schema}
    return _http_post(url, headers, payload, ["choices", 0, "message", "content"])


def _call_deepseek(prompt: str, text: str, api_key: str, model: str, schema: Optional[dict]) -> str:
    """Call DeepSeek API - OpenAI compatible."""
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": _schema_content(prompt, text, schema)}],
    }
    if schema is not None:
        payload["response_format"] = {"type": "json_object"}
    return _http_post(url, headers, payload, ["choices", 0, "message", "content"])


def _call_perplexity(prompt: str, text: str, api_key: str, model: str, schema: Optional[dict]) -> str:
    """Call Perplexity API - OpenAI compatible."""
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    content = f"{prompt}\n\n{text}"
    if schema is not None:
        content += f"\n\nRespond with JSON matching this schema:\n{json.dumps(schema)}"
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
    }
    return _http_post(url, headers, payload, ["choices", 0, "message", "content"])


# Provider configurations
PROVIDERS = {
    name: {"handler": handler, "model_env": name.upper() + "_MODEL"}
    for name, handler in (
        ("openai", _call_openai), ("anthropic", _call_anthropic), ("grok", _call_grok),
        ("gemini", _call_gemini), ("mistral", _call_mistral), ("groq", _call_groq),
        ("cohere", _call_cohere), ("together", _call_together),
        ("deepseek", _call_deepseek), ("perplexity", _call_perplexity))
}


def _invoke(prompt, text, provider, model, api_key, schema, strict):
    if not isinstance(strict, bool):
        raise TypeError("strict must be a boolean")
    token = _STRICT.set(strict)
    try:
        if not isinstance(prompt, str) or not isinstance(text, str) or not prompt or not text:
            return _failure("invalid_input")
        config = PROVIDERS.get(provider) if isinstance(provider, str) else None
        if config is None:
            return _failure("unknown_provider")
        selected = model if model is not None else os.environ.get(config["model_env"], "")
        if not isinstance(selected, str):
            return _failure("invalid_model")
        selected = selected.strip()
        if not selected:
            return _failure("missing_model")
        if any(ord(char) < 32 or ord(char) == 127 for char in selected):
            return _failure("invalid_model")
        invalid_model = False
        try:
            selected.encode("utf-8")
        except UnicodeError:
            invalid_model = True
        if invalid_model:
            return _failure("invalid_model")
        key = api_key or _get_api_key(provider)
        if not isinstance(key, str) or not key.strip():
            return _failure("missing_api_key")
        if schema is not None:
            invalid = not isinstance(schema, dict)
            try:
                json.dumps(schema, allow_nan=False)
            except (TypeError, ValueError, RecursionError):
                invalid = True
            if invalid:
                return _failure("invalid_schema")
        return config["handler"](prompt, text, key, selected, schema)
    finally:
        _STRICT.reset(token)


def parse(
    prompt: str,
    text: str,
    provider: str = "openai",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    *, strict: bool = False,
) -> str:
    """
    Parse text using an LLM API.

    Args:
        prompt: Instructions for the LLM (e.g., "Extract all email addresses")
        text: The text to parse
        provider: "openai", "anthropic", "grok", "gemini", "mistral", "groq",
                  "cohere", "together", "deepseek", "perplexity"
        model: Explicit model, or provider MODEL environment variable; no built-in model.
        api_key: API key (defaults to environment variable)
        strict: Raise sanitized AIError instead of returning an empty string.

    Returns:
        LLM response as string, or empty string on error.
    """
    return _invoke(prompt, text, provider, model, api_key, None, strict)


def parse_json(
    prompt: str,
    text: str,
    provider: str = "openai",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    schema: Optional[dict] = None,
    *, strict: bool = False,
) -> Any:
    """
    Parse text using an LLM and return JSON.

    Args:
        prompt: Instructions for the LLM
        text: The text to parse
        provider: API provider name
        model: Explicit model or provider MODEL environment variable.
        api_key: API key (optional)
        schema: JSON Schema for structured output (optional)
        strict: Raise sanitized AIError on configuration, request or JSON failure.

    Returns:
        Any JSON value, or None on error. JSON null is also a successful None.
    """
    # Add JSON instruction to prompt if no schema
    if prompt and isinstance(prompt, str) and schema is None:
        prompt = f"{prompt}\n\nRespond with valid JSON only, no other text."

    result = _invoke(prompt, text, provider, model, api_key, schema, strict)
    if not result:
        return None

    # Clean markdown code blocks
    result = result.strip()
    if result.startswith("```"):
        lines = result.split("\n")
        if len(lines) >= 2:
            result = "\n".join(lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:])
            result = result.strip()

    try:
        from jsonparse.records import _strict_loads
        return _strict_loads(result)
    except (ValueError, TypeError, RecursionError):
        pass
    if strict:
        raise AIError("invalid_json") from None
    return None


def list_providers() -> Dict[str, str]:
    """
    List available providers and their model environment-variable names.

    Returns:
        Independent dict mapping provider name to MODEL variable name, not values.
    """
    return {name: config["model_env"] for name, config in PROVIDERS.items()}


# Aliases for backward compatibility
parse_ai = parse
parse_ai_json = parse_json


__all__ = [
    "AIError",
    "parse",
    "parse_json",
    "list_providers",
    # Aliases
    "parse_ai",
    "parse_ai_json",
    # Config
    "PROVIDERS",
]

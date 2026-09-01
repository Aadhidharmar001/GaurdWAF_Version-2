from __future__ import annotations

from typing import Any, Dict

SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "api_key",
    "authorization",
    "cookie",
    "access_token",
    "refresh_token",
}

MAX_STRING_LENGTH = 256


def sanitize_parameters(parameters: Dict[str, Any]) -> Dict[str, Any]:
    return {key: _sanitize_value(key, value) for key, value in parameters.items()}


def _sanitize_value(key: str, value: Any) -> Any:
    normalized_key = key.lower()
    if normalized_key in SENSITIVE_KEYS:
        return "[REDACTED]"

    if isinstance(value, dict):
        return {
            nested_key: _sanitize_value(nested_key, nested_value)
            for nested_key, nested_value in value.items()
        }

    if isinstance(value, list):
        return [_sanitize_value(key, item) for item in value]

    if isinstance(value, str):
        compact_value = " ".join(value.split())
        if len(compact_value) > MAX_STRING_LENGTH:
            return f"{compact_value[:MAX_STRING_LENGTH]}...[truncated]"
        return compact_value

    return value

from __future__ import annotations

from typing import Dict, Optional


def parse_openai_usage(payload: object) -> Optional[Dict[str, int]]:
    if not isinstance(payload, dict):
        return None

    usage = payload.get("usage")
    if not isinstance(usage, dict):
        return None

    return {
        "prompt_tokens": _to_int(usage.get("prompt_tokens")),
        "completion_tokens": _to_int(usage.get("completion_tokens")),
        "total_tokens": _to_int(usage.get("total_tokens")),
    }


def _to_int(value: object) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


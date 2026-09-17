from __future__ import annotations

import re
from typing import Any, Mapping

_SECRET_KEYS = re.compile(
    r"(api[_-]?key|secret|token|password|authorization|credential)",
    re.IGNORECASE,
)
_SECRET_VALUES = re.compile(
    r"(?i)((?:api[_-]?key|secret|token|password|bearer)\s*[:=]\s*|[?&]key=)([^\s,;&]+)"
)
_BEARER = re.compile(r"(?i)(bearer\s+)([A-Za-z0-9._\-]+)")


def redact_text(value: str) -> str:
    redacted = _SECRET_VALUES.sub(lambda m: f"{m.group(1)}***", value)
    redacted = _BEARER.sub(r"\1***", redacted)
    return redacted


def redact_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in data.items():
        if _SECRET_KEYS.search(str(key)):
            out[key] = "***"
        elif isinstance(value, str):
            out[key] = redact_text(value)
        elif isinstance(value, Mapping):
            out[key] = redact_mapping(value)
        else:
            out[key] = value
    return out

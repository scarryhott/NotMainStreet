from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any


_STYLE_KEYS_TO_IGNORE = {
    "font_family",
    "font_size",
    "color",
}


def _normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in value.split("\n"):
        collapsed = re.sub(r"[\t ]+", " ", line.strip())
        lines.append(collapsed)
    return "\n".join(lines)


def _canonicalize(obj: Any) -> Any:
    if isinstance(obj, str):
        return _normalize_text(obj)

    if isinstance(obj, list):
        return [_canonicalize(x) for x in obj]

    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key in sorted(obj.keys()):
            if key in _STYLE_KEYS_TO_IGNORE:
                continue
            value = obj[key]
            if value is None:
                continue
            if key == "heading_level":
                # Normalize aliases to integer depth when possible.
                if isinstance(value, str) and value.lower().startswith("h") and value[1:].isdigit():
                    out[key] = int(value[1:])
                    continue
            out[key] = _canonicalize(value)
        return out

    return obj


def canonicalize_cdm(cdm: dict[str, Any]) -> str:
    canonical = _canonicalize(cdm)
    return json.dumps(canonical, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def cdm_hash(cdm: dict[str, Any]) -> str:
    canonical = canonicalize_cdm(cdm)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

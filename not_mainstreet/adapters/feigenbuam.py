from __future__ import annotations

import json
from pathlib import Path

from ..cdm import CDMRecord


def publish_git(record: CDMRecord, root: str = "index/documents") -> str:
    Path(root).mkdir(parents=True, exist_ok=True)
    path = Path(root) / f"{record.document_id}-{record.version}.json"
    path.write_text(json.dumps({
        "document_id": record.document_id,
        "version": record.version,
        "cdm_hash": record.cdm_hash,
        "search": {
            "title": record.payload.get("metadata", {}).get("title", ""),
            "tags": record.payload.get("metadata", {}).get("tags", []),
        },
    }, indent=2, ensure_ascii=False))
    return str(path)

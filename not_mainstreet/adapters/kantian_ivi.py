from __future__ import annotations

import json
from pathlib import Path

from ..cdm import CDMRecord


def publish_git(record: CDMRecord, root: str = "content/docs") -> str:
    Path(root).mkdir(parents=True, exist_ok=True)
    path = Path(root) / f"{record.document_id}.json"
    path.write_text(json.dumps({
        "document_id": record.document_id,
        "version": record.version,
        "cdm_hash": record.cdm_hash,
        "payload": record.payload,
    }, indent=2, ensure_ascii=False))
    return str(path)

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonicalization import cdm_hash


@dataclass
class CDMRecord:
    document_id: str
    version: int
    payload: dict[str, Any]
    cdm_hash: str


class CDMRegistry:
    """In-memory version registry used for deterministic/idempotency behavior."""

    def __init__(self) -> None:
        self._by_document: dict[str, list[CDMRecord]] = {}

    def latest(self, document_id: str) -> CDMRecord | None:
        rows = self._by_document.get(document_id, [])
        return rows[-1] if rows else None

    def register(self, document_id: str, payload: dict[str, Any]) -> CDMRecord:
        digest = cdm_hash(payload)
        latest = self.latest(document_id)
        if latest and latest.cdm_hash == digest:
            return latest

        next_version = 1 if latest is None else latest.version + 1
        record = CDMRecord(document_id=document_id, version=next_version, payload=payload, cdm_hash=digest)
        self._by_document.setdefault(document_id, []).append(record)
        return record

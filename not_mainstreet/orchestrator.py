from __future__ import annotations

from dataclasses import dataclass

from .adapters import feigenbuam, kantian_ivi
from .cdm import CDMRecord, CDMRegistry
from .errors import UnsupportedIntegrationMode


@dataclass
class PublishResult:
    record: CDMRecord
    kantian_ivi_path: str
    feigenbuam_path: str


class Orchestrator:
    def __init__(self, mode: str = "git") -> None:
        self.mode = mode
        self.registry = CDMRegistry()

    def process(self, document_id: str, cdm_payload: dict) -> PublishResult:
        record = self.registry.register(document_id=document_id, payload=cdm_payload)

        if self.mode != "git":
            raise UnsupportedIntegrationMode(
                f"mode '{self.mode}' not implemented; default 'git' is the supported mode"
            )

        k_path = kantian_ivi.publish_git(record)
        f_path = feigenbuam.publish_git(record)
        return PublishResult(record=record, kantian_ivi_path=k_path, feigenbuam_path=f_path)

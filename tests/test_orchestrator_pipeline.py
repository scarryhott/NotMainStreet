import json
import shutil
import unittest
from pathlib import Path

from not_mainstreet import Orchestrator
from not_mainstreet.assets import AssetStore
from not_mainstreet.docx_ingest import ingest_docx


class OrchestratorPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        for path in [Path("content"), Path("index"), Path("assets")]:
            if path.exists():
                shutil.rmtree(path)

    def test_idempotent_reprocess_does_not_churn_version(self) -> None:
        orch = Orchestrator(mode="git")
        payload = {"metadata": {"title": "Doc A", "tags": ["alpha"]}, "content": {"blocks": []}}

        r1 = orch.process("doc-1", payload)
        r2 = orch.process("doc-1", payload)

        self.assertEqual(r1.record.version, 1)
        self.assertEqual(r2.record.version, 1)
        self.assertEqual(r1.record.cdm_hash, r2.record.cdm_hash)

    def test_changed_payload_increments_version(self) -> None:
        orch = Orchestrator(mode="git")
        p1 = {"metadata": {"title": "Doc A"}, "content": {"blocks": []}}
        p2 = {"metadata": {"title": "Doc A changed"}, "content": {"blocks": []}}

        r1 = orch.process("doc-2", p1)
        r2 = orch.process("doc-2", p2)

        self.assertEqual(r1.record.version, 1)
        self.assertEqual(r2.record.version, 2)

    def test_git_mode_writes_expected_artifacts(self) -> None:
        orch = Orchestrator(mode="git")
        payload = {"metadata": {"title": "Doc B", "tags": ["beta"]}, "content": {"blocks": []}}

        result = orch.process("doc-3", payload)

        self.assertTrue(Path(result.kantian_ivi_path).exists())
        self.assertTrue(Path(result.feigenbuam_path).exists())

        content_doc = json.loads(Path(result.kantian_ivi_path).read_text())
        index_doc = json.loads(Path(result.feigenbuam_path).read_text())
        self.assertEqual(content_doc["document_id"], "doc-3")
        self.assertEqual(index_doc["document_id"], "doc-3")


class IngestAndAssetTests(unittest.TestCase):
    def test_docx_ingest_and_asset_store(self) -> None:
        sample = b"fake docx bytes"
        ingested = ingest_docx("MainStreet_Updated.docx", sample)
        self.assertEqual(len(ingested.checksum_sha256), 64)
        self.assertTrue(ingested.uploaded_at.endswith("Z"))

        store = AssetStore(root="assets")
        a1 = store.put(sample)
        a2 = store.put(sample)
        self.assertEqual(a1, a2)
        self.assertTrue(Path("assets", a1).exists())


if __name__ == "__main__":
    unittest.main()

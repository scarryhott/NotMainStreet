import json
import shutil
import unittest
from pathlib import Path

from not_mainstreet.database import EngineDatabases, initialize_databases, run_query
from not_mainstreet.portal import (
    Submission,
    list_edge_intake,
    list_unprocessed,
    render_portal_html,
    submit_edge_intake,
    submit_to_portal,
    sync_submission_to_engine,
)


class PortalDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = Path("data")
        if self.data_root.exists():
            shutil.rmtree(self.data_root)
        self.cfg = EngineDatabases(
            inside_path="data/test_inside_ivi.db",
            outside_path="data/test_outside_portal.db",
        )
        initialize_databases(self.cfg)

    def test_submit_and_list(self) -> None:
        sid = submit_to_portal(Submission("u1", "Need food routing", "Help connect suppliers"), self.cfg)
        self.assertGreater(sid, 0)
        pending = list_unprocessed(self.cfg)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["title"], "Need food routing")

    def test_sync_moves_submission_to_inside_engine(self) -> None:
        sid = submit_to_portal(Submission("u2", "Disaster prep", "Need local team"), self.cfg)
        proposal_id = sync_submission_to_engine(sid, self.cfg)
        self.assertEqual(proposal_id, f"proposal-{sid}")

        outside = run_query(self.cfg.outside_path, "SELECT processed FROM portal_submissions WHERE id = ?", (sid,))
        self.assertEqual(outside[0]["processed"], 1)

        inside = run_query(self.cfg.inside_path, "SELECT event_type, payload_json FROM engine_events ORDER BY id ASC")
        self.assertEqual(inside[0]["event_type"], "PortalSubmissionSynced")
        payload = json.loads(inside[0]["payload_json"])
        self.assertEqual(payload["proposal_id"], proposal_id)

    def _intake_payload(self) -> dict:
        return {
            "proposal_id": "prop-1",
            "tenant_id": "tenant-a",
            "community_id": "community-a",
            "session_id": "session-1",
            "who": {"user_id": "u-1", "roles": ["member"], "reputation_ref": "rep:1"},
            "why": {"goal": "support neighbors", "constraints": [], "values": ["care"], "urgency": "normal"},
            "what": {"category": "service", "description": "deliver food", "budget": 10.0, "requirements": []},
            "where": {"scope_level": "block", "geo": "g1", "service_area": "s1", "constraints": []},
            "when": {"window": "week-1", "trigger_conditions": [], "deadline": "2026-03-01"},
            "thread_ref": "thread-1",
        }

    def test_submit_edge_intake(self) -> None:
        out = submit_edge_intake(**self._intake_payload(), cfg=self.cfg)
        self.assertIn("proposal", out)
        self.assertIn("evaluation", out)
        self.assertFalse(out["idempotent_replay"])
        rows = list_edge_intake(self.cfg, tenant_id="tenant-a", gate_outcome="pass")
        self.assertTrue(any(r["proposal_id"] == "prop-1" for r in rows))

    def test_idempotent_submit_edge_intake(self) -> None:
        payload = self._intake_payload()
        payload["idempotency_key"] = "idem-1"
        out1 = submit_edge_intake(**payload, cfg=self.cfg)
        out2 = submit_edge_intake(**payload, cfg=self.cfg)
        self.assertFalse(out1["idempotent_replay"])
        self.assertTrue(out2["idempotent_replay"])
        rows = run_query(self.cfg.outside_path, "SELECT COUNT(*) AS c FROM edge_proposals")
        self.assertEqual(rows[0]["c"], 1)

    def test_render_portal_html(self) -> None:
        submit_to_portal(Submission("u3", "Bridge request", "Need coordination"), self.cfg)
        page = render_portal_html(self.cfg)
        self.assertIn("NotMainStreet Portal Interface", page)
        self.assertIn("Bridge request", page)


if __name__ == "__main__":
    unittest.main()

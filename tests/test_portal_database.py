import json
import shutil
import unittest
from pathlib import Path

from not_mainstreet.database import EngineDatabases, initialize_databases, run_query
from not_mainstreet.portal import (
    Submission,
    list_unprocessed,
    render_portal_html,
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

    def test_render_portal_html(self) -> None:
        submit_to_portal(Submission("u3", "Bridge request", "Need coordination"), self.cfg)
        page = render_portal_html(self.cfg)
        self.assertIn("NotMainStreet Portal Interface", page)
        self.assertIn("Bridge request", page)


if __name__ == "__main__":
    unittest.main()

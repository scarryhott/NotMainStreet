import json
import shutil
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

from not_mainstreet.database import EngineDatabases
from not_mainstreet.portal_server import PortalServerConfig, run_portal_server


class PortalServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if Path("data").exists():
            shutil.rmtree("data")
        cfg = PortalServerConfig(
            host="127.0.0.1",
            port=8766,
            databases=EngineDatabases(
                inside_path="data/test_inside_http.db",
                outside_path="data/test_outside_http.db",
            ),
        )
        cls.server = run_portal_server(cfg)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def _request(self, method: str, path: str, payload: dict | None = None):
        conn = HTTPConnection("127.0.0.1", 8766, timeout=5)
        body = None
        headers = {}
        if payload is not None:
            body = json.dumps(payload)
            headers["Content-Type"] = "application/json"
        conn.request(method, path, body=body, headers=headers)
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        return resp.status, raw

    def test_submit_list_and_sync_via_http(self) -> None:
        status, raw = self._request(
            "POST",
            "/api/submit",
            {"user_id": "u-http", "title": "Portal title", "body": "Portal body"},
        )
        self.assertEqual(status, 201)
        sid = json.loads(raw.decode("utf-8"))["submission_id"]

        status, raw = self._request("GET", "/api/submissions")
        self.assertEqual(status, 200)
        pending = json.loads(raw.decode("utf-8"))["pending"]
        self.assertTrue(any(p["id"] == sid for p in pending))

        status, raw = self._request("POST", f"/api/sync?submission_id={sid}")
        self.assertEqual(status, 200)
        body = json.loads(raw.decode("utf-8"))
        self.assertEqual(body["proposal_id"], f"proposal-{sid}")

    def test_assistant_empathy_endpoint(self) -> None:
        status, raw = self._request(
            "POST",
            "/api/assistant/empathy",
            {"intent": "increase trust", "mode": "complexify"},
        )
        self.assertEqual(status, 200)
        payload = json.loads(raw.decode("utf-8"))
        self.assertEqual(payload["mode"], "complexify")
        self.assertIn("guardrails", payload)

    def test_assistant_refine_endpoint(self) -> None:
        status, raw = self._request(
            "POST",
            "/api/assistant/refine",
            {
                "user_id": "u-http",
                "intent": "optimize supplies",
                "region_hint": "district-9",
                "density_band": "moderate",
            },
        )
        self.assertEqual(status, 200)
        payload = json.loads(raw.decode("utf-8"))
        self.assertIn("facts", payload)
        self.assertIn("proposal", payload)

    def _intake_payload(self) -> dict:
        return {
            "proposal_id": "prop-http-1",
            "tenant_id": "tenant-http",
            "community_id": "community-a",
            "session_id": "session-http-1",
            "who": {"user_id": "u-http", "roles": ["member"], "reputation_ref": "rep:1"},
            "why": {"goal": "support local food", "constraints": [], "values": ["care"], "urgency": "normal"},
            "what": {"category": "service", "description": "deliver groceries", "budget": 12.0, "requirements": []},
            "where": {"scope_level": "block", "geo": "g1", "service_area": "s1", "constraints": []},
            "when": {"window": "week-1", "trigger_conditions": [], "deadline": "2026-03-01"},
            "thread_ref": "thread-http-1",
            "idempotency_key": "idem-http-1",
        }

    def test_intake_endpoint(self) -> None:
        payload = self._intake_payload()
        status, raw = self._request("POST", "/api/intake", payload)
        self.assertEqual(status, 201)
        body = json.loads(raw.decode("utf-8"))
        self.assertIn("proposal", body)
        self.assertIn("evaluation", body)
        self.assertFalse(body["idempotent_replay"])

        status, raw = self._request("POST", "/api/intake", payload)
        self.assertEqual(status, 201)
        replay = json.loads(raw.decode("utf-8"))
        self.assertTrue(replay["idempotent_replay"])

        status, raw = self._request("GET", "/api/intake?tenant_id=tenant-http&gate_outcome=pass&limit=10&offset=0")
        self.assertEqual(status, 200)
        listed = json.loads(raw.decode("utf-8"))
        self.assertEqual(listed["limit"], 10)
        self.assertEqual(listed["offset"], 0)
        self.assertTrue(any(p["proposal_id"] == "prop-http-1" for p in listed["proposals"]))

    def test_root_html(self) -> None:
        status, raw = self._request("GET", "/")
        self.assertEqual(status, 200)
        html = raw.decode("utf-8")
        self.assertIn("NotMainStreet Portal Interface", html)


if __name__ == "__main__":
    unittest.main()

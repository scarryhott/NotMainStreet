from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .database import EngineDatabases
from .portal import Submission, list_unprocessed, render_portal_html, submit_to_portal, sync_submission_to_engine


@dataclass(frozen=True)
class PortalServerConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    databases: EngineDatabases = EngineDatabases()


class PortalRequestHandler(BaseHTTPRequestHandler):
    cfg = PortalServerConfig()

    def _send_json(self, payload: dict, code: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(length) if length else b"{}"
        return json.loads(data.decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            html = render_portal_html(self.cfg.databases).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        if parsed.path == "/api/submissions":
            self._send_json({"pending": list_unprocessed(self.cfg.databases)})
            return

        self._send_json({"error": "not_found"}, code=404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path == "/api/submit":
            body = self._read_json()
            required = {"user_id", "title", "body"}
            if not required.issubset(body):
                self._send_json({"error": "invalid_payload", "required": sorted(required)}, code=400)
                return
            sid = submit_to_portal(
                Submission(user_id=body["user_id"], title=body["title"], body=body["body"]),
                self.cfg.databases,
            )
            self._send_json({"submission_id": sid}, code=201)
            return

        if parsed.path == "/api/sync":
            qs = parse_qs(parsed.query)
            if "submission_id" not in qs:
                self._send_json({"error": "submission_id query parameter required"}, code=400)
                return
            try:
                sid = int(qs["submission_id"][0])
                proposal_id = sync_submission_to_engine(sid, self.cfg.databases)
            except Exception as exc:  # narrow enough for API boundary
                self._send_json({"error": str(exc)}, code=400)
                return
            self._send_json({"proposal_id": proposal_id})
            return

        self._send_json({"error": "not_found"}, code=404)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def run_portal_server(cfg: PortalServerConfig = PortalServerConfig()) -> ThreadingHTTPServer:
    handler = type("ConfiguredPortalRequestHandler", (PortalRequestHandler,), {"cfg": cfg})
    server = ThreadingHTTPServer((cfg.host, cfg.port), handler)
    return server

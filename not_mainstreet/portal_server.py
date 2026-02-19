from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .database import EngineDatabases
from .empathy_engine import MANIFESTO_TITLE, empathy_reflection
from .openclaw_bridge import OpenClawBridge, UserContext
from .portal import (
    Submission,
    list_edge_intake,
    list_unprocessed,
    render_portal_html,
    submit_edge_intake,
    submit_to_portal,
    sync_submission_to_engine,
)


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

        if parsed.path == "/api/intake":
            qs = parse_qs(parsed.query)
            limit = int(qs.get("limit", ["50"])[0])
            offset = int(qs.get("offset", ["0"])[0])
            proposals = list_edge_intake(
                self.cfg.databases,
                tenant_id=qs.get("tenant_id", [None])[0],
                gate_outcome=qs.get("gate_outcome", [None])[0],
                routing_class=qs.get("routing_class", [None])[0],
                limit=limit,
                offset=offset,
            )
            self._send_json({"proposals": proposals, "limit": limit, "offset": offset})
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




        if parsed.path == "/api/intake":
            body = self._read_json()
            required = {
                "proposal_id",
                "tenant_id",
                "community_id",
                "session_id",
                "who",
                "why",
                "what",
                "where",
                "when",
                "thread_ref",
            }
            if not required.issubset(body):
                self._send_json({"error": "invalid_payload", "required": sorted(required)}, code=400)
                return
            try:
                result = submit_edge_intake(
                    proposal_id=body["proposal_id"],
                    tenant_id=body["tenant_id"],
                    community_id=body["community_id"],
                    session_id=body["session_id"],
                    who=body["who"],
                    why=body["why"],
                    what=body["what"],
                    where=body["where"],
                    when=body["when"],
                    thread_ref=body["thread_ref"],
                    idempotency_key=body.get("idempotency_key"),
                    cfg=self.cfg.databases,
                )
            except Exception as exc:
                self._send_json({"error": "validation_error", "detail": str(exc)}, code=400)
                return
            self._send_json(result, code=201)
            return

        if parsed.path == "/api/assistant/empathy":
            body = self._read_json()
            intent = body.get("intent", "unspecified")
            mode = body.get("mode", "complexify")
            reflection = empathy_reflection(intent, mode=mode)
            self._send_json({
                "title": MANIFESTO_TITLE,
                "mode": reflection.mode,
                "amplification_notice": reflection.amplification_notice,
                "credo": reflection.credo,
                "guardrails": reflection.guardrails,
                "generated_at": reflection.generated_at,
            })
            return

        if parsed.path == "/api/assistant/refine":
            body = self._read_json()
            required = {"user_id", "intent", "region_hint", "density_band"}
            if not required.issubset(body):
                self._send_json({"error": "invalid_payload", "required": sorted(required)}, code=400)
                return
            bridge = OpenClawBridge()
            facts, profile, proposal = bridge.run_refinement_cycle(
                UserContext(
                    user_id=body["user_id"],
                    intent=body["intent"],
                    region_hint=body["region_hint"],
                    density_band=body["density_band"],
                )
            )
            self._send_json({
                "facts": facts,
                "profile": profile,
                "proposal": {
                    "title": proposal.title,
                    "rationale": proposal.rationale,
                    "patch_outline": proposal.patch_outline,
                    "generated_at": proposal.generated_at,
                },
            })
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

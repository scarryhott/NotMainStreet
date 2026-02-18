"""Executable integration primitives for Not MainStreet."""

from .canonicalization import canonicalize_cdm, cdm_hash
from .cdm import CDMRecord, CDMRegistry
from .coordination import ContinuityConstraint, validate_continuity
from .database import EngineDatabases, initialize_databases, run_query
from .docx_ingest import IngestedDocx, extract_docx_text, ingest_docx
from .event_spine import EventSpine
from .governance import SovereigntyContext, sovereignty_weight
from .graphs import LaplacianDiagnostics, l_diag
from .nodes import NodeRecord, NodeState, TRANSITIONS
from .orchestrator import Orchestrator, PublishResult
from .portal import Submission, list_unprocessed, render_portal_html, submit_to_portal, sync_submission_to_engine
from .portal_server import PortalServerConfig, run_portal_server
from .philosophy_runtime import CycleOutcome, Proposal, run_cycle

__all__ = [
    "canonicalize_cdm",
    "cdm_hash",
    "CDMRecord",
    "CDMRegistry",
    "ContinuityConstraint",
    "validate_continuity",
    "EngineDatabases",
    "initialize_databases",
    "run_query",
    "IngestedDocx",
    "extract_docx_text",
    "ingest_docx",
    "EventSpine",
    "SovereigntyContext",
    "sovereignty_weight",
    "LaplacianDiagnostics",
    "l_diag",
    "NodeRecord",
    "NodeState",
    "TRANSITIONS",
    "Orchestrator",
    "PublishResult",
    "Submission",
    "list_unprocessed",
    "render_portal_html",
    "submit_to_portal",
    "sync_submission_to_engine",
    "PortalServerConfig",
    "run_portal_server",
    "CycleOutcome",
    "Proposal",
    "run_cycle",
]

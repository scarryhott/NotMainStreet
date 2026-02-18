from __future__ import annotations

import hashlib
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO


@dataclass
class IngestedDocx:
    filename: str
    checksum_sha256: str
    uploaded_at: str


def ingest_docx(filename: str, blob: bytes) -> IngestedDocx:
    """Minimal ingest primitive for DOCX payload metadata registration."""
    return IngestedDocx(
        filename=filename,
        checksum_sha256=hashlib.sha256(blob).hexdigest(),
        uploaded_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


def extract_docx_text(blob: bytes) -> str:
    """Extract plain text from DOCX word/document.xml without external dependencies."""
    with zipfile.ZipFile(BytesIO(blob)) as zf:
        xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
    text_nodes = re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml)
    return "\n".join(t for t in text_nodes if t)

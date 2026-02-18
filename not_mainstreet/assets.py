from __future__ import annotations

import hashlib
from pathlib import Path


class AssetStore:
    """Filesystem-backed content-addressable asset store for local development."""

    def __init__(self, root: str = "assets") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, content: bytes) -> str:
        digest = hashlib.sha256(content).hexdigest()
        path = self.root / digest
        if not path.exists():
            path.write_bytes(content)
        return digest

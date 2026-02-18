#!/usr/bin/env python3
"""Unblock checklist validator for external repo integrations.

Runs matrix schema validation first, then readiness checks.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

MATRIX_PATH = Path("contracts/target_integration_matrix.yaml")
TARGETS = ("kantian_ivi", "feigenbuam")


def _run(cmd: list[str], cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def load_matrix() -> dict:
    return json.loads(MATRIX_PATH.read_text())


def _pinned_commit_exists(url: str, commit: str) -> tuple[bool, str]:
    p = _run(["git", "ls-remote", url, commit])
    if p.returncode == 0 and p.stdout.strip():
        return True, "found via ls-remote"

    temp = Path(".tmp/integration-verify")
    if temp.exists():
        _run(["rm", "-rf", str(temp)])
    temp.mkdir(parents=True, exist_ok=True)

    if _run(["git", "init", "-q"], cwd=str(temp)).returncode != 0:
        return False, "failed to init temp git repo"
    if _run(["git", "remote", "add", "origin", url], cwd=str(temp)).returncode != 0:
        return False, "failed to add remote"
    p = _run(["git", "fetch", "--depth=1", "origin", commit], cwd=str(temp))
    if p.returncode == 0:
        return True, "found via fetch fallback"

    return False, (p.stderr.strip() or p.stdout.strip() or "commit not found")


def _is_unresolved(value: str) -> bool:
    return not value or value == "TBD"


def validate_target(name: str, cfg: dict) -> list[str]:
    errors: list[str] = []
    for key in ["repository_url", "default_branch", "maintenance_status", "license", "pinned_commit"]:
        if _is_unresolved(str(cfg.get(key, ""))):
            errors.append(f"{name}: unresolved {key}")

    schema = cfg.get("schema", {})
    for key in ["format", "version", "location", "source_ref"]:
        if _is_unresolved(str(schema.get(key, ""))):
            errors.append(f"{name}: unresolved schema.{key}")

    url = str(cfg.get("repository_url", ""))
    commit = str(cfg.get("pinned_commit", ""))
    if not _is_unresolved(url) and not _is_unresolved(commit):
        ok, msg = _pinned_commit_exists(url, commit)
        if not ok:
            errors.append(f"{name}: pinned_commit not reachable in remote ({msg})")

    return errors


def main() -> int:
    schema_check = _run(["python", "scripts/validate_target_integration_matrix.py"])
    if schema_check.returncode != 0:
        print(schema_check.stdout, end="")
        print(schema_check.stderr, end="")
        return 1

    matrix = load_matrix()
    errors: list[str] = []

    sources = matrix.get("sources", {})
    for name in TARGETS:
        if name not in sources:
            errors.append(f"missing target block: {name}")
            continue
        errors.extend(validate_target(name, sources[name]))

    comp = matrix.get("compatibility", {})
    if "strict_mode" not in comp:
        errors.append("missing compatibility.strict_mode")
    if _is_unresolved(str(comp.get("breaking_change_policy", ""))):
        errors.append("missing compatibility.breaking_change_policy")

    if errors:
        print("Integration readiness FAILED:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Integration readiness PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

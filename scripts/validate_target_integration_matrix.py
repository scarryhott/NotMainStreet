#!/usr/bin/env python3
"""Validate contracts/target_integration_matrix.yaml against formal schema.

The matrix file is stored as JSON-compatible YAML, so we parse with stdlib json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path("contracts/target_integration_matrix.schema.json")
MATRIX_PATH = Path("contracts/target_integration_matrix.yaml")


def _check_type(expected: str, value: Any) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
    }.get(expected, True)


def _validate(schema: dict[str, Any], value: Any, path: str, defs: dict[str, Any], errors: list[str]) -> None:
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref.startswith("#/$defs/"):
            key = ref.split("/", 2)[2]
            _validate(defs[key], value, path, defs, errors)
        return

    expected_type = schema.get("type")
    if expected_type and not _check_type(expected_type, value):
        errors.append(f"{path}: expected {expected_type}")
        return

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: value {value!r} not in enum {schema['enum']}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: string shorter than minLength {schema['minLength']}")

    if isinstance(value, int):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: integer below minimum {schema['minimum']}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: array shorter than minItems {schema['minItems']}")
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(value):
                _validate(item_schema, item, f"{path}[{i}]", defs, errors)

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required key '{key}'")

        props = schema.get("properties", {})
        for key, val in value.items():
            if key in props:
                _validate(props[key], val, f"{path}.{key}", defs, errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: additional property '{key}' not allowed")


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text())
    matrix = json.loads(MATRIX_PATH.read_text())
    errors: list[str] = []
    _validate(schema, matrix, "matrix", schema.get("$defs", {}), errors)

    if errors:
        print("Matrix schema validation FAILED:")
        for e in errors:
            print(f"- {e}")
        return 1

    print("Matrix schema validation PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""A small JSON Schema checker for the contract tests: the subset specs/schemas uses.
Standard library only, so the suite runs anywhere Python does."""

from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMAS = Path(__file__).resolve().parents[2] / "specs" / "schemas"
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def load(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text())


def errors(value, schema: dict, path: str = "$") -> list[str]:
    if "$ref" in schema:
        return errors(value, load(schema["$ref"].split("#")[0]), path)
    out: list[str] = []
    if "oneOf" in schema:
        if sum(not errors(value, s, path) for s in schema["oneOf"]) != 1:
            out.append(f"{path}: matches none or several of oneOf")
        return out
    t = schema.get("type")
    if t:
        allowed = t if isinstance(t, list) else [t]
        ok = any(
            (a == "integer" and isinstance(value, int) and not isinstance(value, bool))
            or (a == "number" and isinstance(value, (int, float)) and not isinstance(value, bool))
            or (a in TYPES and isinstance(value, TYPES[a]))
            for a in allowed)
        if not ok:
            return [f"{path}: expected {t}, got {type(value).__name__}"]
    if "const" in schema and value != schema["const"]:
        out.append(f"{path}: expected {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        out.append(f"{path}: {value!r} not in enum")
    if isinstance(value, str) and "pattern" in schema and not re.search(schema["pattern"], value):
        out.append(f"{path}: {value!r} does not match {schema['pattern']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            out.append(f"{path}: below minimum")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            out.append(f"{path}: not above {schema['exclusiveMinimum']}")
    if isinstance(value, dict):
        for k in schema.get("required", []):
            if k not in value:
                out.append(f"{path}: missing {k}")
        props = schema.get("properties", {})
        for k, v in value.items():
            if k in props:
                out += errors(v, props[k], f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                out.append(f"{path}: unexpected {k}")
    if isinstance(value, list):
        prefix = schema.get("prefixItems")
        if prefix:
            for i, (v, s) in enumerate(zip(value, prefix)):
                out += errors(v, s, f"{path}[{i}]")
            if schema.get("items") is False and len(value) > len(prefix):
                out.append(f"{path}: too many items")
        elif isinstance(schema.get("items"), dict):
            for i, v in enumerate(value):
                out += errors(v, schema["items"], f"{path}[{i}]")
    return out

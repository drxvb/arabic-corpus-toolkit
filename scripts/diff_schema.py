#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diff_schema.py — diff two JSON Schema files and classify the change.

Per Kimi-style asset-promotion lens of the v0.2 multi-agent review:

  > scripts/diff_schema.py between any two refs prints `[ADD] field foo`,
  > `[REMOVE] field bar`, `[RENAME] x → y` — refuses to allow a MAJOR-class
  > change without an explicit `--allow-break` flag plus a CHANGELOG.md entry.

This is the schema-versioning enforcement tool that goes with the per-asset
SemVer policy declared in `CHANGELOG.md`.

Usage:
    python scripts/diff_schema.py OLD.schema.json NEW.schema.json
    python scripts/diff_schema.py OLD NEW --allow-break    # required for MAJOR

Exit codes:
    0  — PATCH or MINOR change (additive / non-breaking)
    1  — MAJOR change requires --allow-break OR errors during diff
    2  — usage error

Python 3 stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


@dataclass
class SchemaDiff:
    """Result of diffing two schema files."""
    added_fields: List[str] = field(default_factory=list)
    removed_fields: List[str] = field(default_factory=list)
    type_changes: List[Tuple[str, str, str]] = field(default_factory=list)  # (field, old_type, new_type)
    enum_changes: List[Tuple[str, List, List]] = field(default_factory=list)  # (field, added, removed)
    required_added: List[str] = field(default_factory=list)
    required_removed: List[str] = field(default_factory=list)

    def classify(self) -> str:
        """Return 'PATCH', 'MINOR', or 'MAJOR' per the toolkit's SemVer rules."""
        # MAJOR if any breaking change
        if self.removed_fields:
            return "MAJOR"
        if self.type_changes:
            return "MAJOR"
        if self.required_added:
            return "MAJOR"  # consumers that don't supply this field now fail
        # Enum value removals are breaking (consumers using removed value fail)
        for _, _, removed in self.enum_changes:
            if removed:
                return "MAJOR"
        # MINOR if anything additive
        if self.added_fields or self.required_removed:
            return "MINOR"
        for _, added, _ in self.enum_changes:
            if added:
                return "MINOR"
        return "PATCH"

    def summary(self) -> str:
        out: List[str] = []
        if self.added_fields:
            out.append(f"## Added fields ({len(self.added_fields)})")
            for f in self.added_fields[:30]:
                out.append(f"  [ADD]     {f}")
        if self.removed_fields:
            out.append(f"\n## Removed fields ({len(self.removed_fields)})")
            for f in self.removed_fields[:30]:
                out.append(f"  [REMOVE]  {f}")
        if self.type_changes:
            out.append(f"\n## Type changes ({len(self.type_changes)})")
            for fld, old_t, new_t in self.type_changes[:30]:
                out.append(f"  [TYPE]    {fld}: {old_t} -> {new_t}")
        if self.enum_changes:
            out.append(f"\n## Enum changes ({len(self.enum_changes)})")
            for fld, added, removed in self.enum_changes[:30]:
                if added:
                    out.append(f"  [ENUM+]   {fld}: added {added}")
                if removed:
                    out.append(f"  [ENUM-]   {fld}: removed {removed}")
        if self.required_added:
            out.append(f"\n## Newly-required fields ({len(self.required_added)})")
            for f in self.required_added[:30]:
                out.append(f"  [REQ+]    {f}")
        if self.required_removed:
            out.append(f"\n## No-longer-required fields ({len(self.required_removed)})")
            for f in self.required_removed[:30]:
                out.append(f"  [REQ-]    {f}")
        if not out:
            out.append("(no changes detected)")
        return "\n".join(out)


def _collect_properties(schema: Dict[str, Any], prefix: str = "") -> Dict[str, Dict[str, Any]]:
    """Walk a JSON Schema and return a flat map of field_path -> field_schema.
    Handles top-level + nested objects + items (for arrays) + definitions.
    """
    fields: Dict[str, Dict[str, Any]] = {}

    def _walk(node: Any, path: str) -> None:
        if not isinstance(node, dict):
            return
        # Properties
        for name, sub in (node.get("properties") or {}).items():
            full = f"{path}.{name}" if path else name
            fields[full] = sub if isinstance(sub, dict) else {}
            _walk(sub, full)
        # Array items
        items = node.get("items")
        if isinstance(items, dict):
            _walk(items, f"{path}[]" if path else "[]")
        # oneOf / anyOf / allOf
        for combinator in ("oneOf", "anyOf", "allOf"):
            for sub in (node.get(combinator) or []):
                _walk(sub, path)

    _walk(schema, prefix)

    # Definitions get their own namespace
    for def_name, def_schema in (schema.get("definitions") or {}).items():
        _walk(def_schema, f"#/definitions/{def_name}")

    return fields


def _required_set(schema: Dict[str, Any]) -> Set[str]:
    """Collect all `required` field names from the schema, with definition prefixes."""
    required: Set[str] = set()

    def _walk(node: Any, prefix: str) -> None:
        if not isinstance(node, dict):
            return
        for r in (node.get("required") or []):
            required.add(f"{prefix}.{r}" if prefix else r)
        for name, sub in (node.get("properties") or {}).items():
            _walk(sub, f"{prefix}.{name}" if prefix else name)
        items = node.get("items")
        if isinstance(items, dict):
            _walk(items, f"{prefix}[]" if prefix else "[]")

    _walk(schema, "")
    for def_name, def_schema in (schema.get("definitions") or {}).items():
        _walk(def_schema, f"#/definitions/{def_name}")
    return required


def diff_schemas(old_path: Path | str, new_path: Path | str) -> SchemaDiff:
    """Compute the diff between two JSON Schema files."""
    old = json.loads(Path(old_path).read_text(encoding="utf-8"))
    new = json.loads(Path(new_path).read_text(encoding="utf-8"))

    old_fields = _collect_properties(old)
    new_fields = _collect_properties(new)

    diff = SchemaDiff()
    diff.added_fields = sorted(set(new_fields) - set(old_fields))
    diff.removed_fields = sorted(set(old_fields) - set(new_fields))

    # Type changes — compare common fields
    for fld in set(old_fields) & set(new_fields):
        old_t = old_fields[fld].get("type") if isinstance(old_fields[fld], dict) else None
        new_t = new_fields[fld].get("type") if isinstance(new_fields[fld], dict) else None
        # Normalize list types
        if isinstance(old_t, list):
            old_t = tuple(sorted(old_t))
        if isinstance(new_t, list):
            new_t = tuple(sorted(new_t))
        if old_t != new_t and old_t is not None and new_t is not None:
            diff.type_changes.append((fld, str(old_t), str(new_t)))

        # Enum changes
        old_enum = old_fields[fld].get("enum") if isinstance(old_fields[fld], dict) else None
        new_enum = new_fields[fld].get("enum") if isinstance(new_fields[fld], dict) else None
        if old_enum or new_enum:
            old_set = set(old_enum or [])
            new_set = set(new_enum or [])
            added = sorted(new_set - old_set, key=lambda x: str(x))
            removed = sorted(old_set - new_set, key=lambda x: str(x))
            if added or removed:
                diff.enum_changes.append((fld, added, removed))

    # Required-fields diff
    old_req = _required_set(old)
    new_req = _required_set(new)
    diff.required_added = sorted(new_req - old_req)
    diff.required_removed = sorted(old_req - new_req)

    return diff


def cli_main() -> int:
    p = argparse.ArgumentParser(description="Diff two JSON Schema files; refuse MAJOR breaks without --allow-break")
    p.add_argument("old", help="Old schema file (or commit ref + path — TODO v0.6)")
    p.add_argument("new", help="New schema file")
    p.add_argument("--allow-break", action="store_true",
                   help="Permit MAJOR breaking changes (requires CHANGELOG.md entry per policy)")
    p.add_argument("--json", action="store_true", help="Emit JSON-formatted diff")
    args = p.parse_args()

    try:
        d = diff_schemas(args.old, args.new)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    classification = d.classify()

    if args.json:
        import dataclasses
        payload = dataclasses.asdict(d)
        payload["classification"] = classification
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"# Schema diff: {args.old} -> {args.new}\n")
        print(f"**Classification: {classification}**\n")
        print(d.summary())

    if classification == "MAJOR" and not args.allow_break:
        print(
            "\n❌ MAJOR (breaking) change detected. "
            "Pass --allow-break AND add a CHANGELOG.md entry explaining the migration.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(cli_main())

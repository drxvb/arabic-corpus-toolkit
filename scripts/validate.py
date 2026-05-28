#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate.py — schema validator for arabic-corpus-toolkit JSON assets.

Per the Codex-style API-design lens of the v0.2 multi-agent review,
this is the **net-new contribution that justifies the shared module's
existence**: a typed, dataclass-backed schema report that catches what
the humanizer's review process caught manually in v2.6.0 (the 14
surgical fixes) — but now automatically.

Distinguishes:
- ERRORS (blocking): missing required fields, JSON-parse failures,
  malformed `entries` structure
- WARNINGS (non-blocking): unknown confidence values, unknown
  political_sensitivity values, recommended-but-missing fields
- UNKNOWN FIELDS (forward-compat): tracked, not rejected — surfaces
  typos (`politcal_sensitivity`) without blocking new v2.7+ fields
- COVERAGE: per-v2.6+ optional field, how many entries carry it —
  the regression detector for triage coverage

Python 3 stdlib only.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Set

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


REQUIRED_ENTRY_FIELDS: Set[str] = {
    "en", "ai_default_calque", "natural_arabic", "domain", "confidence",
}
RECOMMENDED_ENTRY_FIELDS: Set[str] = {
    "alternatives", "llm_votes", "n_llms", "consensus_strength",
    "corpus_hits", "partial_hits",
}
OPTIONAL_V260_FIELDS: Set[str] = {
    # v2.6.0 triage additions
    "regional_sensitivity",
    "political_sensitivity",
    "disambiguation_pair_id",
    "disambiguation_warning",
    "applies_only_in_domain",
    "v2_6_triage_note",
    # v2.6.3 topic-guard additions
    "context_keywords_arabic",
    "context_keywords_english",
    "context_keywords_required_count",
    "exclude_if_pattern",
}
CONFIDENCE_VALUES = {"medium", "medium_consensus", "high", "high_user_attested", "topic-guarded", "low"}
REGIONAL_SENS_VALUES = {None, "gulf", "levant", "maghreb", "pan-arab"}
POL_SENS_VALUES = {None, "none", "low", "medium", "high", "critical"}


@dataclass
class SchemaReport:
    """Result of validate_schema(). Dataclass for clean dict serialization."""
    ok: bool = True
    path: str = ""
    schema_version: str = ""
    n_entries: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    unknown_fields: Dict[str, int] = field(default_factory=dict)
    missing_required_by_index: List[int] = field(default_factory=list)
    coverage: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def validate_schema(path: Path | str) -> SchemaReport:
    """Validate a calque-dictionary.json against the v0.3 schema rules."""
    rep = SchemaReport(path=str(path))

    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        rep.ok = False
        rep.errors.append(f"file not found: {path}")
        return rep
    except OSError as e:
        rep.ok = False
        rep.errors.append(f"could not read {path}: {e}")
        return rep

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        rep.ok = False
        rep.errors.append(f"invalid JSON: {e}")
        return rep

    # Wrapper / envelope support
    if isinstance(data, list):
        entries = data
        rep.schema_version = ""
    elif isinstance(data, dict):
        rep.schema_version = str(
            data.get("$schema_version")
            or data.get("metadata", {}).get("version", "")
        )
        entries = data.get("entries")
    else:
        rep.ok = False
        rep.errors.append("root must be list or object with 'entries'")
        return rep

    if not isinstance(entries, list):
        rep.ok = False
        rep.errors.append("'entries' missing or not a list")
        return rep

    rep.n_entries = len(entries)
    for k in OPTIONAL_V260_FIELDS:
        rep.coverage[k] = 0

    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            rep.errors.append(f"entry[{i}] not an object")
            rep.ok = False
            continue
        missing = REQUIRED_ENTRY_FIELDS - set(e)
        if missing:
            rep.errors.append(f"entry[{i}] missing required: {sorted(missing)}")
            rep.missing_required_by_index.append(i)
            rep.ok = False
        conf = e.get("confidence")
        if conf is not None and conf not in CONFIDENCE_VALUES:
            rep.warnings.append(f"entry[{i}] unknown confidence: {conf!r}")
        reg_sens = e.get("regional_sensitivity")
        if "regional_sensitivity" in e and reg_sens not in REGIONAL_SENS_VALUES:
            rep.warnings.append(f"entry[{i}] unknown regional_sensitivity: {reg_sens!r}")
        pol_sens = e.get("political_sensitivity")
        if "political_sensitivity" in e and pol_sens not in POL_SENS_VALUES:
            rep.warnings.append(f"entry[{i}] unknown political_sensitivity: {pol_sens!r}")
        # If exclude_if_pattern is present, recommend context_keywords_required_count
        if e.get("exclude_if_pattern") and "context_keywords_required_count" not in e:
            rep.warnings.append(
                f"entry[{i}] has exclude_if_pattern without context_keywords_required_count"
            )
        for k in e:
            if k in OPTIONAL_V260_FIELDS:
                rep.coverage[k] += 1
            elif k not in REQUIRED_ENTRY_FIELDS and k not in RECOMMENDED_ENTRY_FIELDS:
                rep.unknown_fields[k] = rep.unknown_fields.get(k, 0) + 1

    return rep


def cli_main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="Validate arabic-corpus-toolkit JSON assets")
    p.add_argument("path", help="Path to JSON file (e.g., corpus/calque-dictionary.json)")
    p.add_argument("--json", action="store_true", help="Emit JSON report")
    p.add_argument("--strict", action="store_true", help="Exit non-zero on warnings too")
    args = p.parse_args()

    rep = validate_schema(args.path)

    if args.json:
        print(rep.to_json())
    else:
        print(f"# Schema validation: {args.path}\n")
        print(f"Status: {'✅ OK' if rep.ok else '❌ FAIL'}")
        print(f"Schema version: {rep.schema_version or '(unversioned)'}")
        print(f"Entries: {rep.n_entries}")
        if rep.errors:
            print(f"\n## Errors ({len(rep.errors)})")
            for err in rep.errors[:30]:
                print(f"  - {err}")
            if len(rep.errors) > 30:
                print(f"  - ... and {len(rep.errors) - 30} more")
        if rep.warnings:
            print(f"\n## Warnings ({len(rep.warnings)})")
            for w in rep.warnings[:15]:
                print(f"  - {w}")
            if len(rep.warnings) > 15:
                print(f"  - ... and {len(rep.warnings) - 15} more")
        if rep.unknown_fields:
            print(f"\n## Unknown fields (forward-compat tracking)")
            for fld, n in sorted(rep.unknown_fields.items(), key=lambda x: -x[1]):
                print(f"  - {fld}: {n} entries")
        if rep.coverage:
            print(f"\n## Optional v2.6+ field coverage (out of {rep.n_entries})")
            for fld in sorted(rep.coverage):
                print(f"  - {fld}: {rep.coverage[fld]}")

    failed = (not rep.ok) or (args.strict and rep.warnings)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(cli_main())

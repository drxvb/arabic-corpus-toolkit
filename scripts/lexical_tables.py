#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lexical_tables.py — Loader for Asset C (lexical-tables) in arabic-corpus-toolkit.

Typed API surface (Codex's lens from the v0.2 multi-agent review). Mirrors the
loader pattern established by scripts/dictionary.py (Asset A) and the register
policies in scripts/register.py (Asset B).

Public surface:
    load_tables() -> dict                # parsed JSON, mtime-cached
    schema_version() -> str              # "$schema_version" from the asset
    get_table(name) -> dict              # by-name table accessor
    table_names() -> tuple[str, ...]     # ordered list of table names
    ai_phrase_alternatives(phrase) -> list[str] | None
    connector_replacement(connector) -> str | None
    is_repetitive_starter(starter) -> bool
    starter_replacements() -> list[str]
    filler_entries() -> list[str]
    quote_verb_pool(verb) -> list[str] | None
    soft_validate() -> list[str]         # returns refusal-list-style errors
    stats() -> dict

Python 3 stdlib only.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

_HERE = Path(__file__).resolve().parent
_CORPUS_DIR = _HERE.parent / "corpus"
_ASSET_PATH = _CORPUS_DIR / "lexical-tables.json"

# (mtime, data) tuple cache. Reload when mtime advances.
_cache: Optional[Tuple[float, Dict[str, Any]]] = None


def asset_path() -> Path:
    return _ASSET_PATH


def load_tables() -> Dict[str, Any]:
    """Return the parsed lexical-tables asset. mtime-keyed cache."""
    global _cache
    try:
        mtime = _ASSET_PATH.stat().st_mtime
    except FileNotFoundError:
        raise FileNotFoundError(
            f"lexical-tables asset not found at {_ASSET_PATH}. "
            f"This is shipped in arabic-corpus-toolkit >= v0.7."
        )
    if _cache is None or _cache[0] != mtime:
        _cache = (mtime, json.loads(_ASSET_PATH.read_text(encoding="utf-8")))
    return _cache[1]


def schema_version() -> str:
    return load_tables()["$schema_version"]


def table_names() -> Tuple[str, ...]:
    return tuple(load_tables()["tables"].keys())


def get_table(name: str) -> Dict[str, Any]:
    tables = load_tables()["tables"]
    if name not in tables:
        raise KeyError(f"no such lexical table: {name!r}. Known: {sorted(tables)}")
    return tables[name]


def ai_phrase_alternatives(phrase: str) -> Optional[List[str]]:
    """Return alternatives for an AI phrase, or None if the phrase is not in the table."""
    for entry in get_table("ai_phrases")["entries"]:
        if entry["input"] == phrase:
            return list(entry["alternatives"])
    return None


def connector_replacement(connector: str) -> Optional[str]:
    """Return the natural replacement for an AI connector, or None if not in the table."""
    for entry in get_table("connectors")["entries"]:
        if entry["input"] == connector:
            return entry["replacement"]
    return None


def is_repetitive_starter(starter: str) -> bool:
    return starter in get_table("repetitive_starters")["detectors"]


def starter_replacements() -> List[str]:
    return list(get_table("repetitive_starters")["replacements"])


def filler_entries() -> List[str]:
    return list(get_table("fillers")["entries"])


def numbered_transition_replacement(input_word: str) -> Optional[str]:
    for entry in get_table("numbered_transitions")["entries"]:
        if entry["input"] == input_word:
            return entry["replacement"]
    return None


def quote_verb_pool(verb: str) -> Optional[List[str]]:
    """Return the rotation pool for a quote-introducing verb, or None."""
    for entry in get_table("quote_verbs")["entries"]:
        if entry["input"] == verb:
            return list(entry["rotation_pool"])
    return None


def structural_opener_patterns() -> List[Dict[str, Any]]:
    """Return Gap-C regex patterns + replacements (v1.1.0+). Each entry has
    'pattern' (Python regex) and 'replacements' (list of templates with {0}-style
    positional substitution for captured groups)."""
    return list(get_table("structural_openers")["entries"])


def intensifier_destack_patterns() -> List[Dict[str, str]]:
    """Return Gap-G regex de-stacking patterns (v1.1.0+). Each entry has
    'pattern' (Python regex) and 'replacement' (plain string)."""
    return list(get_table("intensifier_destack")["entries"])


def soft_validate() -> List[str]:
    """Cheap structural validation. Returns list of error strings; empty list = OK.

    Does NOT implement full JSON Schema. Catches the failures most likely to
    bite consumers: missing required keys, empty tables, mis-typed policy fields.
    """
    errs: List[str] = []
    try:
        data = load_tables()
    except Exception as e:
        return [f"could not load asset: {e}"]

    for key in ("$schema_version", "asset_name", "tables"):
        if key not in data:
            errs.append(f"missing top-level key {key!r}")

    if data.get("asset_name") != "lexical-tables":
        errs.append(f"asset_name should be 'lexical-tables', got {data.get('asset_name')!r}")

    EXPECTED_POLICIES = {
        "ai_phrases":           "deterministic_all_matches",
        "connectors":           "probabilistic_per_match",
        "repetitive_starters":  "consecutive_repeat_trigger",
        "fillers":              "intensity_gated",
        "numbered_transitions": "probabilistic_per_match",
        "quote_verbs":          "rotation_pool",
        "structural_openers":   "regex_capture_substitute",
        "intensifier_destack":  "regex_substitute",
    }
    tables = data.get("tables", {})
    for name, expected_policy in EXPECTED_POLICIES.items():
        if name not in tables:
            errs.append(f"missing required table {name!r}")
            continue
        actual_policy = tables[name].get("policy")
        if actual_policy != expected_policy:
            errs.append(f"table {name!r}: policy is {actual_policy!r}, expected {expected_policy!r}")

    # Probabilities must be in [0, 1]
    for name in ("connectors", "repetitive_starters", "numbered_transitions"):
        if name in tables:
            prob = tables[name].get("probability")
            if prob is not None and not (0.0 <= prob <= 1.0):
                errs.append(f"table {name!r}: probability {prob} out of [0,1]")

    return errs


def stats() -> Dict[str, Any]:
    """Counts per table, for human inspection."""
    data = load_tables()
    out: Dict[str, Any] = {
        "schema_version": data.get("$schema_version"),
        "asset_name": data.get("asset_name"),
        "tables": {},
    }
    for name, table in data.get("tables", {}).items():
        if name == "repetitive_starters":
            out["tables"][name] = {
                "policy": table.get("policy"),
                "detector_count": len(table.get("detectors", [])),
                "replacement_count": len(table.get("replacements", [])),
            }
        elif name == "fillers":
            out["tables"][name] = {
                "policy": table.get("policy"),
                "entry_count": len(table.get("entries", [])),
            }
        else:
            entries = table.get("entries", [])
            out["tables"][name] = {
                "policy": table.get("policy"),
                "entry_count": len(entries),
                "source_tag_counts": _count_source_tags(entries),
            }
    return out


def _count_source_tags(entries: List[Any]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for e in entries:
        if isinstance(e, dict):
            tag = e.get("source_tag", "v1_substrate")
            out[tag] = out.get(tag, 0) + 1
    return out


if __name__ == "__main__":
    # Quick CLI: print stats and run soft validation
    import sys
    print("=== Asset C: lexical-tables ===")
    print(f"path: {_ASSET_PATH}")
    print()
    print(json.dumps(stats(), ensure_ascii=False, indent=2))
    print()
    errs = soft_validate()
    if errs:
        print(f"SOFT VALIDATION: {len(errs)} error(s)")
        for e in errs:
            print(f"  - {e}")
        sys.exit(1)
    print("SOFT VALIDATION: OK")
    sys.exit(0)

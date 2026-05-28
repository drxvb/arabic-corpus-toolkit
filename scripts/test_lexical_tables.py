#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_lexical_tables.py — Release gate for v0.7 Asset C migration.

Tests the typed API surface against the shipped lexical-tables.json. If any
assertion fails, the migration is incomplete.
"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lexical_tables import (
    load_tables,
    schema_version,
    table_names,
    get_table,
    ai_phrase_alternatives,
    connector_replacement,
    is_repetitive_starter,
    starter_replacements,
    filler_entries,
    numbered_transition_replacement,
    quote_verb_pool,
    templated_starter_strategies,
    soft_validate,
    stats,
)


def _assert(cond: bool, msg: str) -> bool:
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {msg}")
    return cond


def main() -> int:
    print("=== Asset C: lexical-tables release gate ===\n")
    failures = 0

    # T1: schema_version
    sv = schema_version()
    if not _assert(sv == "1.0.0", f"schema_version() == '1.0.0' (got {sv!r})"):
        failures += 1

    # T2: all seven tables present
    names = table_names()
    expected = ("ai_phrases", "connectors", "repetitive_starters", "fillers",
                "numbered_transitions", "quote_verbs", "templated_starters")
    if not _assert(set(names) == set(expected),
                   f"all seven tables present (got {sorted(names)})"):
        failures += 1

    # T3: ai_phrase alternatives — v1 substrate entry
    alts = ai_phrase_alternatives("من المهم ملاحظة")
    if not _assert(alts == ["للعلم", "من الجدير بالذكر", "تذكر"],
                   "ai_phrase_alternatives('من المهم ملاحظة') returns v1 alternatives"):
        failures += 1

    # T4: ai_phrase alternatives — Gap A extension entry
    alts_gap = ai_phrase_alternatives("تجدر الإشارة إلى أن")
    if not _assert(alts_gap == ["يذكر أن", "والحقيقة أن"],
                   "ai_phrase_alternatives('تجدر الإشارة إلى أن') returns Gap A alternatives"):
        failures += 1

    # T5: missing phrase returns None
    if not _assert(ai_phrase_alternatives("هذه عبارة غير موجودة") is None,
                   "ai_phrase_alternatives(missing) returns None"):
        failures += 1

    # T6: connector_replacement — v1 substrate
    if not _assert(connector_replacement("وعلاوة على ذلك،") == "كما أن،",
                   "connector_replacement v1 substrate"):
        failures += 1

    # T7: connector_replacement — Gap B extension
    if not _assert(connector_replacement("فضلا عن ذلك،") == "كذلك،",
                   "connector_replacement Gap B extension"):
        failures += 1

    # T8: repetitive starters detection
    if not _assert(is_repetitive_starter("تعتبر") is True,
                   "is_repetitive_starter('تعتبر') = True"):
        failures += 1
    if not _assert(is_repetitive_starter("ركض") is False,
                   "is_repetitive_starter('ركض') = False"):
        failures += 1

    # T9: starter replacements (the pronoun-prefixed pool)
    replacements = starter_replacements()
    if not _assert("فهي" in replacements and "وهي" in replacements,
                   "starter_replacements() contains pronoun-prefixed forms"):
        failures += 1

    # T10: fillers
    fillers = filler_entries()
    if not _assert("طبعا،" in fillers and len(fillers) == 4,
                   "filler_entries() returns the 4 v1 fillers"):
        failures += 1

    # T11: numbered transitions
    if not _assert(numbered_transition_replacement("أولا،") == "في البداية،",
                   "numbered_transition_replacement('أولا،')"):
        failures += 1

    # T12: quote-verb rotation pool (Gap D)
    pool = quote_verb_pool("قال")
    if not _assert(pool is not None and "أكد" in pool and "أوضح" in pool,
                   "quote_verb_pool('قال') contains أكد and أوضح"):
        failures += 1

    # T13: templated starters return as advisory strategies
    strategies = templated_starter_strategies()
    if not _assert(len(strategies) == 10 and all("strategy" in s and "pattern" in s for s in strategies),
                   "templated_starter_strategies() returns 10 advisory entries"):
        failures += 1

    # T14: soft_validate passes on the shipped asset
    errs = soft_validate()
    if not _assert(errs == [], f"soft_validate() returns no errors (got: {errs})"):
        failures += 1

    # T15: stats produces a summary
    s = stats()
    if not _assert(s["schema_version"] == "1.0.0" and "tables" in s,
                   "stats() returns versioned summary"):
        failures += 1

    # T16: per-table entry counts match the source-of-truth
    # ai_phrases: 30 v1 + 10 Gap A = 40
    ai_count = len(get_table("ai_phrases")["entries"])
    if not _assert(ai_count == 40, f"ai_phrases has 40 entries (got {ai_count})"):
        failures += 1
    # connectors: 8 v1 + 13 Gap B = 21
    conn_count = len(get_table("connectors")["entries"])
    if not _assert(conn_count == 21, f"connectors has 21 entries (got {conn_count})"):
        failures += 1
    # numbered_transitions: 5
    nt_count = len(get_table("numbered_transitions")["entries"])
    if not _assert(nt_count == 5, f"numbered_transitions has 5 entries (got {nt_count})"):
        failures += 1

    print()
    if failures:
        print(f"FAILED: {failures} test(s)")
        return 1
    print("OK: all release-gate tests pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

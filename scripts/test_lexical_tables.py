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
    structural_opener_patterns,
    intensifier_destack_patterns,
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

    # T1: schema_version (bumped to 1.1.0 with parity fix)
    sv = schema_version()
    if not _assert(sv == "1.1.0", f"schema_version() == '1.1.0' (got {sv!r})"):
        failures += 1

    # T2: all eight tables present (v1.1.0 replaced templated_starters with structural_openers + added intensifier_destack)
    names = table_names()
    expected = ("ai_phrases", "connectors", "repetitive_starters", "fillers",
                "numbered_transitions", "quote_verbs",
                "structural_openers", "intensifier_destack")
    if not _assert(set(names) == set(expected),
                   f"all eight tables present (got {sorted(names)})"):
        failures += 1

    # T3: ai_phrase alternatives — v1 substrate entry (humanizer-parity content)
    alts = ai_phrase_alternatives("من المهم ملاحظة")
    if not _assert(alts == ["نشير إلى", "يلزم التنبيه إلى"],
                   "ai_phrase_alternatives('من المهم ملاحظة') returns humanizer-parity v1 alternatives"):
        failures += 1

    # T4: ai_phrase alternatives — Gap A extension entry (with humanizer-parity empty-string alt)
    alts_gap = ai_phrase_alternatives("تجدر الإشارة إلى أن")
    if not _assert(alts_gap == ["يُذكر أن", "والحقيقة أن", ""],
                   "ai_phrase_alternatives('تجدر الإشارة إلى أن') returns Gap A alternatives with pro-drop"):
        failures += 1

    # T5: missing phrase returns None
    if not _assert(ai_phrase_alternatives("هذه عبارة غير موجودة") is None,
                   "ai_phrase_alternatives(missing) returns None"):
        failures += 1

    # T6: connector_replacement — v1 substrate
    if not _assert(connector_replacement("وعلاوة على ذلك،") == "كما أن،",
                   "connector_replacement v1 substrate"):
        failures += 1

    # T7: connector_replacement — Gap B extension (humanizer uses فضلاً with tashkeel)
    if not _assert(connector_replacement("فضلاً عن ذلك،") == "كذلك،",
                   "connector_replacement Gap B (with tashkeel)"):
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

    # T12: quote-verb rotation pool (Gap D) — humanizer uses أكّد with tashkeel
    pool = quote_verb_pool("قال")
    if not _assert(pool is not None and "أكّد" in pool and "أوضح" in pool,
                   "quote_verb_pool('قال') contains أكّد and أوضح"):
        failures += 1

    # T13: structural openers (Gap C) — NEW in v1.1.0, mechanically applicable
    structural = structural_opener_patterns()
    if not _assert(len(structural) == 10 and all("pattern" in s and "replacements" in s for s in structural),
                   "structural_opener_patterns() returns 10 regex entries (was advisory in v1.0.0)"):
        failures += 1
    # T13b: confirm capture-group pattern is regex-compilable
    import re as _re
    try:
        _re.compile(structural[0]["pattern"])
        compile_ok = True
    except Exception:
        compile_ok = False
    if not _assert(compile_ok, "structural_openers[0].pattern compiles as a Python regex"):
        failures += 1

    # T14: intensifier de-stack patterns (Gap G) — NEW in v1.1.0, first-class table
    destack = intensifier_destack_patterns()
    if not _assert(len(destack) == 8 and all("pattern" in s and "replacement" in s for s in destack),
                   "intensifier_destack_patterns() returns 8 regex entries"):
        failures += 1

    # T15: soft_validate passes on the shipped asset
    errs = soft_validate()
    if not _assert(errs == [], f"soft_validate() returns no errors (got: {errs})"):
        failures += 1

    # T16: stats produces a summary
    s = stats()
    if not _assert(s["schema_version"] == "1.1.0" and "tables" in s,
                   "stats() returns versioned summary"):
        failures += 1

    # T17: per-table entry counts at v1.1.0 humanizer-parity
    # ai_phrases: 67 = 6 pro-drop + 1 tautology + 7 clause-preserving + 21 v1 + 4 calque + 16 newsroom + 12 Gap A
    ai_count = len(get_table("ai_phrases")["entries"])
    if not _assert(ai_count == 67, f"ai_phrases has 67 entries at v1.1.0 (got {ai_count})"):
        failures += 1
    # connectors: 8 v1 + 14 Gap B (with tashkeel variant of في حين أن) = 22
    conn_count = len(get_table("connectors")["entries"])
    if not _assert(conn_count == 22, f"connectors has 22 entries at v1.1.0 (got {conn_count})"):
        failures += 1
    # numbered_transitions: 5
    nt_count = len(get_table("numbered_transitions")["entries"])
    if not _assert(nt_count == 5, f"numbered_transitions has 5 entries (got {nt_count})"):
        failures += 1
    # repetitive starters: 11 (humanizer-parity, includes tashkeel variants)
    rs_count = len(get_table("repetitive_starters")["detectors"])
    if not _assert(rs_count == 11, f"repetitive_starters has 11 detectors at v1.1.0 (got {rs_count})"):
        failures += 1
    # quote_verbs: 4 (humanizer has separate tashkeel + bare for ذكر أن/أنّ)
    qv_count = len(get_table("quote_verbs")["entries"])
    if not _assert(qv_count == 4, f"quote_verbs has 4 entries at v1.1.0 (got {qv_count})"):
        failures += 1

    # T18: pro-drop empty-string alternative is preserved (schema relaxation)
    pro_drop = ai_phrase_alternatives("في الواقع")
    if not _assert(pro_drop is not None and "" in pro_drop,
                   "ai_phrase_alternatives('في الواقع') includes '' (pro-drop) per humanizer-parity"):
        failures += 1

    print()
    if failures:
        print(f"FAILED: {failures} test(s)")
        return 1
    print("OK: all release-gate tests pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

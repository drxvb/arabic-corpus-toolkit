#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
influence_telemetry.py — v1.7.0 per-output asset-influence telemetry (Gap G3).

The third (and final) foundational debt the 3-evaluator audit flagged:

  > Codex: "I cannot tell which asset, rule, vendor, or stage caused a
            specific output decision."
  > Gemini: "Lack of observability and debuggability — absence of per-output
             asset-influence telemetry."
  > Sonnet: "A translation comes back with stages.A_terminology.matched_count: 11
             but no per-output trace of WHICH 11 Asset G entries fired."

This module provides:
  - `InfluenceTrace`         : append-only causal record
  - `record(asset_id, ...)`  : log one influence
  - `as_json()` / `from_json()`: serialize/deserialize

# Data model

Each record is an immutable dict:
  {
    "asset_id":      "G.technology",          # which asset
    "asset_version": "1.4.0",                  # at what version
    "trigger":       "term_hint_injected",     # what fired
    "evidence":      {"en": "cloud computing", "ar": "الحوسبة السحابية"},
    "stage":         "A_terminology",          # which pipeline phase
    "seq":           7,                        # ordinal within trace
  }

Consumers create an instance, pass it through their stages, and serialize
it in the final output's `influence_trace` field.

# Usage

    from influence_telemetry import InfluenceTrace
    trace = InfluenceTrace()
    trace.record(
        asset_id="G.technology",
        asset_version="1.4.0",
        trigger="term_hint_injected",
        evidence={"en": "cloud computing", "ar": "الحوسبة السحابية"},
        stage="A_terminology",
    )
    result["influence_trace"] = trace.as_json()

Python 3 stdlib only.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional


_VALID_TRIGGERS = frozenset({
    "term_hint_injected",       # Stage A: Asset G EN→AR pair appended to LLM prompt
    "calque_correction_applied", # Stage D: Asset A calque dict substitution fired
    "lex_substitution_fired",    # Asset C ai_phrases substitution
    "intensifier_destacked",     # Asset C intensifier_destack regex matched
    "typography_normalized",     # Asset D typography rule applied
    "anti_pattern_detected",     # Asset E reader-respect-patterns hit
    "terminology_confirmed",     # Asset F candidate corpus-confirmed a term
    "cross_vendor_correction",   # Stage E vendor proposed an EN→AR fix
    "humanizer_gate_decision",   # Stage F humanness gate scored/rejected
    "language_check_failed",     # Asset normalize: output not Arabic-dominant
    "compatibility_refused",     # Asset registry refused a schema version
    "other",                     # caller-named fallback
})


class InfluenceTrace:
    """Append-only causal record of which assets influenced an output.

    Construct one per top-level operation (one translation, one section draft,
    one humanizer pass). Pass it through pipeline stages. Serialize as JSON at
    the end.
    """

    def __init__(self):
        self._records: List[Dict[str, Any]] = []

    def record(self,
               asset_id: str,
               asset_version: str,
               trigger: str,
               evidence: Optional[Dict[str, Any]] = None,
               stage: Optional[str] = None) -> None:
        """Append one influence record. Once appended, the record is immutable
        (we don't expose mutation). Unknown triggers are accepted but mapped
        to 'other' with the user-supplied string preserved in `trigger_raw`."""
        if trigger in _VALID_TRIGGERS:
            normalized_trigger = trigger
            trigger_raw = None
        else:
            normalized_trigger = "other"
            trigger_raw = trigger
        rec: Dict[str, Any] = {
            "seq": len(self._records),
            "asset_id": asset_id,
            "asset_version": asset_version,
            "trigger": normalized_trigger,
            "stage": stage or "unspecified",
            "evidence": dict(evidence) if evidence else {},
        }
        if trigger_raw is not None:
            rec["trigger_raw"] = trigger_raw
        self._records.append(rec)

    def __len__(self) -> int:
        return len(self._records)

    def __bool__(self) -> bool:
        return bool(self._records)

    def __iter__(self):
        return iter(self._records)

    def filter_by(self, **kw) -> List[Dict[str, Any]]:
        """Return records matching all kw==value constraints."""
        return [r for r in self._records if all(r.get(k) == v for k, v in kw.items())]

    def by_asset(self, asset_id: str) -> List[Dict[str, Any]]:
        return self.filter_by(asset_id=asset_id)

    def by_stage(self, stage: str) -> List[Dict[str, Any]]:
        return self.filter_by(stage=stage)

    def by_trigger(self, trigger: str) -> List[Dict[str, Any]]:
        return self.filter_by(trigger=trigger)

    def summary(self) -> Dict[str, Any]:
        """Aggregate counts per asset / stage / trigger."""
        from collections import Counter
        return {
            "total_influences": len(self._records),
            "by_asset_id":      dict(Counter(r["asset_id"] for r in self._records)),
            "by_stage":         dict(Counter(r["stage"]    for r in self._records)),
            "by_trigger":       dict(Counter(r["trigger"]  for r in self._records)),
        }

    def as_json(self) -> List[Dict[str, Any]]:
        """Return a JSON-serializable list of records (immutable copy)."""
        return [dict(r) for r in self._records]

    @classmethod
    def from_json(cls, records: List[Dict[str, Any]]) -> "InfluenceTrace":
        """Reconstruct from a previously-serialized trace."""
        t = cls()
        for r in records:
            t._records.append(dict(r))
        # Renumber `seq` defensively in case the source had gaps
        for i, r in enumerate(t._records):
            r["seq"] = i
        return t


def known_triggers() -> List[str]:
    """List the standardized trigger names. Callers can use other values
    (they get normalized to 'other' with the raw value preserved)."""
    return sorted(_VALID_TRIGGERS)


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # Self-test
    print("═" * 64)
    print("  influence_telemetry.py — self-test")
    print("═" * 64)

    t = InfluenceTrace()
    t.record(
        asset_id="G.technology", asset_version="1.4.0",
        trigger="term_hint_injected",
        evidence={"en": "cloud computing", "ar": "الحوسبة السحابية"},
        stage="A_terminology",
    )
    t.record(
        asset_id="A", asset_version="1.2.0",
        trigger="calque_correction_applied",
        evidence={"calque": "الشخصية", "natural": "الشخصنة"},
        stage="D_validator",
    )
    t.record(
        asset_id="C", asset_version="1.1.0",
        trigger="lex_substitution_fired",
        evidence={"phrase": "من المهم ملاحظة", "replaced_with": "نشير إلى"},
        stage="D_validator",
    )
    t.record(
        asset_id="custom-asset", asset_version="0.1.0",
        trigger="unknown_trigger_name",      # → normalized to 'other'
        evidence={"detail": "test"},
        stage="custom",
    )

    print(f"\nTotal records: {len(t)}")
    print(f"\nFull trace:")
    for r in t:
        print(f"  [{r['seq']}] {r['stage']:<15} {r['asset_id']:<15} {r['trigger']}")

    print(f"\nFilter by stage='D_validator': {len(t.by_stage('D_validator'))} records")
    print(f"Filter by asset='C':            {len(t.by_asset('C'))} records")
    print(f"\nSummary:")
    print(json.dumps(t.summary(), ensure_ascii=False, indent=2))

    # Round-trip JSON
    s = t.as_json()
    t2 = InfluenceTrace.from_json(s)
    assert len(t2) == len(t), "round-trip length mismatch"
    assert t2.as_json() == t.as_json(), "round-trip data mismatch"
    print(f"\n✓ JSON round-trip: identical")

    # Unknown trigger preservation
    custom_rec = t.by_asset("custom-asset")[0]
    assert custom_rec["trigger"] == "other"
    assert custom_rec["trigger_raw"] == "unknown_trigger_name"
    print(f"✓ Unknown trigger preserved as trigger_raw")

    print(f"\nKnown standard triggers: {known_triggers()}")
    print(f"\n✓ All self-test assertions passed.")

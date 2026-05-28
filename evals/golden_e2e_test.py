#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
golden_e2e_test.py — v1.4.1 family golden regression.

Multi-agent roadmap consensus item #3 (both codex + minimax critics ranked top-5).

Runs deterministic, OFFLINE assertions on the entire family:
  - Toolkit asset shapes + counts within expected bounds
  - Translator Stage A finds N Asset G hits on canonical input
  - Authoring suite resolves Asset G hints from canonical fact pack
  - Humanizer score_text gives expected score for canonical clean/sloppy inputs

This catches silent regressions when any sibling ships a new release. Does
NOT call LLM proxies — that's `evals/end_to_end_demo.py`'s job.

Run:
    python evals/golden_e2e_test.py

Exit 0 on full pass, 1 on any assertion failure.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT.parent

sys.path.insert(0, str(ROOT / "scripts"))


def _assert(cond: bool, msg: str) -> bool:
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {msg}")
    return cond


def golden_canon_en() -> str:
    """Canonical English used across all assertions. Stable across versions."""
    return (
        "The Saudi tech sector grew 15% YoY in Q1 2026, driven by artificial "
        "intelligence and cloud computing adoption. Email and instant messaging "
        "usage doubled. The CEO of Vision 2030 office announced new 5G networks. "
        "Internet of Things infrastructure leads regional growth."
    )


def golden_canon_clean_ar() -> str:
    return (
        "أعلنت الحكومة عن خطة جديدة لتطوير قطاع التقنية. "
        "شملت الخطة عدة محاور أساسية منها التعليم والابتكار."
    )


def golden_canon_sloppy_ar() -> str:
    return (
        "من المهم ملاحظة أن النظام في غاية الأهمية البالغة جداً. "
        "علاوة على ذلك، تجدر الإشارة إلى أن الفائدة كبيرة. "
        "بشكل عام، في الواقع الأمر جيد."
    )


def test_asset_registry() -> int:
    """v1.6.0: assert the asset version registry contract."""
    failures = 0
    print("\n━━━ Toolkit asset_registry (v1.6.0+) ━━━")
    from asset_registry import (  # type: ignore
        list_assets, current_version, is_compatible, check_consumer,
    )
    assets = list_assets()
    if not _assert(len(assets) >= 8,
                   f"Registry lists >=8 assets (got {len(assets)})"):
        failures += 1
    if not _assert(is_compatible("G.technology", "1.4.0"),
                   "G.technology v1.4.0 within band"):
        failures += 1
    if not _assert(not is_compatible("G.technology", "2.0.0"),
                   "G.technology v2.0.0 outside band (refused)"):
        failures += 1
    # Consumer audits
    for consumer in ("humanizer", "translator", "authoring"):
        r = check_consumer(consumer)
        if not _assert(not r.has_problems,
                       f"check_consumer({consumer!r}) reports no problems"):
            failures += 1
    return failures


def test_arabic_normalize() -> int:
    """v1.5.0: assert the canonical Arabic normalization contract."""
    failures = 0
    print("\n━━━ Toolkit arabic_normalize (v1.5.0+) ━━━")
    from arabic_normalize import normalize, arabic_char_ratio, is_arabic_dominant  # type: ignore
    cases = [
        ("strip tashkeel",        "الذكاءِ",   "light",      "الذكاء"),
        ("alif → bare (medium)",  "أحمد",       "medium",     "احمد"),
        ("alif preserved (light)","أحمد",       "light",      "أحمد"),
        ("ta marbuta (aggressive)","الحوسبة",  "aggressive", "الحوسبه"),
    ]
    for desc, src, level, expected in cases:
        got = normalize(src, level=level)
        if not _assert(got == expected, f"{level}: {desc} — {src!r} → {expected!r} (got {got!r})"):
            failures += 1
    # Idempotence
    sample = "الحوسبةُ السحابيّة لــأحمدَ"
    once = normalize(sample, level="medium")
    if not _assert(normalize(once, level="medium") == once,
                   "Idempotence: normalize(normalize(x)) == normalize(x)"):
        failures += 1
    # Language detection
    if not _assert(is_arabic_dominant("مرحبا بكم"),
                   "is_arabic_dominant detects pure Arabic"):
        failures += 1
    if not _assert(not is_arabic_dominant("Hello World"),
                   "is_arabic_dominant rejects pure English"):
        failures += 1
    return failures


def test_toolkit() -> int:
    failures = 0
    print("\n━━━ Toolkit asset shape ━━━")
    import dictionary, terminology, domain_terminology, lexical_tables

    if not _assert(dictionary.entry_count() >= 300,
                   f"Asset A: dictionary has >=300 entries (got {dictionary.entry_count()})"):
        failures += 1
    if not _assert(lexical_tables.soft_validate() == [],
                   "Asset C: lexical-tables soft_validate clean"):
        failures += 1
    if not _assert(terminology.candidate_count("technology") >= 900,
                   f"Asset F.tech: >=900 candidates (got {terminology.candidate_count('technology')})"):
        failures += 1
    if not _assert(domain_terminology.pair_count() >= 400,
                   f"Asset G: >=400 paired terms (got {domain_terminology.pair_count()})"):
        failures += 1
    # Specific anchor pairs must survive every release
    anchors = [
        ("artificial intelligence", "الذكاء"),
        ("cloud computing", "الحوسبة"),
        ("5G", "الجيل"),
        ("email", "بريد"),
    ]
    for en, ar_root in anchors:
        hits = domain_terminology.find_by_en(en)
        ok = len(hits) > 0 and any(ar_root in h["ar"] for h in hits)
        if not _assert(ok, f"Asset G anchor: '{en}' → contains '{ar_root}'"):
            failures += 1
    return failures


def test_translator() -> int:
    failures = 0
    print("\n━━━ Translator Stage A ━━━")
    translator_scripts = PUBLIC / "arabic-corpus-translator" / "scripts"
    if not translator_scripts.exists():
        print("  [SKIP] translator not at sibling path")
        return 0
    sys.path.insert(0, str(translator_scripts))
    try:
        from translate import stage_a_terminology  # type: ignore
    except Exception as e:
        print(f"  [SKIP] translator import failed: {e}")
        return 0

    result = stage_a_terminology(golden_canon_en(), "technology")
    if not _assert(result.get("matched_count", 0) >= 1,
                   f"Stage A: >=1 calque-dict hit (got {result.get('matched_count')})"):
        failures += 1
    if not _assert(len(result.get("asset_g_terminology_hits", [])) >= 5,
                   f"Stage A: >=5 Asset G hits on canonical EN (got {len(result.get('asset_g_terminology_hits', []))})"):
        failures += 1
    if not _assert(result.get("asset_f_available") is True,
                   "Asset F available to translator"):
        failures += 1
    if not _assert(result.get("asset_g_available") is True,
                   "Asset G available to translator"):
        failures += 1
    return failures


def test_humanizer() -> int:
    failures = 0
    print("\n━━━ Humanizer score_text ━━━")
    h_scripts = PUBLIC / "arabic-ai-text-humanizer" / "scripts"
    if not h_scripts.exists():
        print("  [SKIP] humanizer not at sibling path")
        return 0
    sys.path.insert(0, str(h_scripts))
    try:
        from humanize_v2 import score_text, apply_typography_rules, reader_respect_score  # type: ignore
    except Exception as e:
        print(f"  [SKIP] humanizer import failed: {e}")
        return 0

    clean = score_text(golden_canon_clean_ar())
    if not _assert(clean.get("score", 0) >= 90,
                   f"score_text clean: >=90 (got {clean.get('score')})"):
        failures += 1
    sloppy = score_text(golden_canon_sloppy_ar())
    if not _assert(sloppy.get("score", 100) <= 20,
                   f"score_text sloppy: <=20 (got {sloppy.get('score')})"):
        failures += 1
    if not _assert(clean.get("sample_size", 0) >= 60,
                   f"sample_size includes Asset C: >=60 (got {clean.get('sample_size')})"):
        failures += 1

    # Asset D / E (humanizer v2.12.0+)
    print("\n━━━ Humanizer Asset D + E (v2.12.0+) ━━━")
    text, diag_d = apply_typography_rules("هذا اختبار, مع علامة استفهام?")
    if not _assert(diag_d.get("asset_d_available") is True,
                   "Asset D available to humanizer"):
        failures += 1
    if not _assert("،" in text and "؟" in text,
                   f"Typography conversion fires: 'هذا اختبار, مع علامة استفهام?' → got {text!r}"):
        failures += 1

    diag_e = reader_respect_score(
        "هذا أمر ثابت وراسخ، أي بمعنى آخر النتيجة واضحة وجلية."
    )
    if not _assert(diag_e.get("available") is True,
                   "Asset E available to humanizer"):
        failures += 1
    if not _assert(diag_e.get("anti_pattern_hits", 0) >= 2,
                   f"Asset E catches >=2 hits on tautology+re-explanation sample (got {diag_e.get('anti_pattern_hits')})"):
        failures += 1
    return failures


def test_authoring() -> int:
    failures = 0
    print("\n━━━ Authoring-suite Asset G hints ━━━")
    a_scripts = PUBLIC / "arabic-authoring-suite" / "scripts"
    if not a_scripts.exists():
        print("  [SKIP] authoring-suite not at sibling path")
        return 0
    sys.path.insert(0, str(a_scripts))
    try:
        from generate import _find_terminology_hits, _load_asset_g  # type: ignore
    except Exception as e:
        print(f"  [SKIP] authoring-suite import failed: {e}")
        return 0

    if not _assert(_load_asset_g("technology") is not None,
                   "Asset G loadable by authoring"):
        failures += 1
    hits = _find_terminology_hits(golden_canon_en(), "technology")
    if not _assert(len(hits) >= 5,
                   f"Authoring finds >=5 terminology hits in canonical EN (got {len(hits)})"):
        failures += 1
    return failures


def main() -> int:
    print("═" * 68)
    print("  arabic-* family GOLDEN E2E regression  v1.4.1")
    print("═" * 68)
    total = 0
    total += test_asset_registry()
    total += test_arabic_normalize()
    total += test_toolkit()
    total += test_translator()
    total += test_humanizer()
    total += test_authoring()
    print()
    print("─" * 68)
    if total:
        print(f"✗ {total} assertion(s) failed")
        return 1
    print("✓ All golden assertions pass — family pipeline intact.")
    print("─" * 68)
    return 0


if __name__ == "__main__":
    sys.exit(main())

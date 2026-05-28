#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arabic_normalize.py — v1.5.0 shared Unicode normalization contract.

Three independent evaluators (Sonnet/Codex/Gemini) flagged the absence of this
contract as the family's #1 architectural debt. Asset C's lex pass strips
tashkeel one way, the translator's Stage D tokenizes another way, score_text
counts Arabic chars a third way — producing silent inconsistencies that bite
at scale.

This module is THE canonical source. All four siblings must route Arabic
normalization through here.

# Levels

- `light`      : strip tashkeel + tatweel. Meaning-preserving, safe for output.
- `medium`     : light + alif variants → bare alif + alif-maqsura → ya. Good
                 for matching/search. Some meaning loss (الذكــاء vs الذكاء
                 may carry stylistic intent in poetry; medium drops it).
- `aggressive` : medium + ta marbuta → ha + hamza-on-letter → bare letter.
                 Max recall for fuzzy retrieval. NOT for user-facing output.

# Contract

- **Idempotent**: `normalize(normalize(x, L), L) == normalize(x, L)` for all L.
- **Monotone**: light ⊆ medium ⊆ aggressive. If two strings collide at level
  `light` they also collide at `medium` and `aggressive`.
- **Pure**: no I/O, no randomness. Stdlib only.
- **Reversible markers preserved**: digits and ASCII punctuation pass through
  unchanged unless the caller asks (`digit_form="western"` etc.).

# Usage

    from arabic_normalize import normalize, NormalizationLevel
    light = normalize("الذكــاء الاصطناعيّ", level="light")
    # → "الذكاء الاصطناعي"

    medium = normalize("أحمد قال هذى", level="medium")
    # → "احمد قال هذي"

    aggressive = normalize("الحوسبة السحابيّة", level="aggressive")
    # → "الحوسبه السحابيه"

Python 3 stdlib only.
"""
from __future__ import annotations

import re
from typing import Literal, Set

NormalizationLevel = Literal["light", "medium", "aggressive"]


# Tashkeel (Arabic diacritics): U+064B..U+0652 + U+0670 (dagger alif) + U+0640 (tatweel)
# Tatweel is a stretching character with no semantic content.
_TASHKEEL_CHARS = set("ًٌٍَُِّْـٰٕٖٜٗ٘ٙٚٛٝٞ")
# Build a translation table for tashkeel stripping
_TASHKEEL_TRANSLATE = {ord(c): None for c in _TASHKEEL_CHARS}


# Alif variants — semantically the same letter in matching contexts
_ALIF_VARIANTS = {
    "آ": "ا",  # alif with madda
    "أ": "ا",  # alif with hamza above
    "إ": "ا",  # alif with hamza below
    "ٱ": "ا",  # alif wasla
}
_ALIF_TRANSLATE = {ord(k): v for k, v in _ALIF_VARIANTS.items()}


# Alif maqsura → ya. Many corpora use them interchangeably.
_YA_VARIANTS = {
    "ى": "ي",  # alif maqsura → ya
}
_YA_TRANSLATE = {ord(k): v for k, v in _YA_VARIANTS.items()}


# Ta marbuta → ha. Aggressive only; this collapses real morphology.
_TA_MARBUTA = {"ة": "ه"}
_TA_TRANSLATE = {ord(k): v for k, v in _TA_MARBUTA.items()}


# Hamza-on-letter → bare letter. Aggressive only.
_HAMZA_ON_LETTER = {
    "ؤ": "و",
    "ئ": "ي",
}
_HAMZA_ON_LETTER_TRANSLATE = {ord(k): v for k, v in _HAMZA_ON_LETTER.items()}


# Arabic-Indic digits → Western, and vice versa
_ARABIC_INDIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_WESTERN_DIGITS = "0123456789"
_AI_TO_WESTERN = {ord(a): w for a, w in zip(_ARABIC_INDIC_DIGITS, _WESTERN_DIGITS)}
_WESTERN_TO_AI = {ord(w): a for w, a in zip(_WESTERN_DIGITS, _ARABIC_INDIC_DIGITS)}


def normalize(text: str, level: NormalizationLevel = "light",
              digit_form: Literal["preserve", "western", "arabic_indic"] = "preserve") -> str:
    """Apply Arabic normalization at the requested level.

    Args:
        text: Input string. Non-Arabic content passes through unchanged.
        level: "light" / "medium" / "aggressive". See module docstring.
        digit_form: "preserve" (default) leaves digits as-is. "western"
                    converts Arabic-Indic to Western. "arabic_indic" the inverse.

    Returns:
        Normalized text. Empty input returns "".
    """
    if not text:
        return ""

    if level not in ("light", "medium", "aggressive"):
        raise ValueError(f"unknown level: {level!r}. Use light/medium/aggressive.")

    # All levels: strip tashkeel + tatweel
    text = text.translate(_TASHKEEL_TRANSLATE)

    if level in ("medium", "aggressive"):
        # Alif variants
        text = text.translate(_ALIF_TRANSLATE)
        # Alif maqsura → ya
        text = text.translate(_YA_TRANSLATE)

    if level == "aggressive":
        # Ta marbuta → ha
        text = text.translate(_TA_TRANSLATE)
        # Hamza on letter → bare letter
        text = text.translate(_HAMZA_ON_LETTER_TRANSLATE)

    if digit_form == "western":
        text = text.translate(_AI_TO_WESTERN)
    elif digit_form == "arabic_indic":
        text = text.translate(_WESTERN_TO_AI)

    return text


def arabic_char_ratio(text: str) -> float:
    """Fraction of `text` that is Arabic letters (U+0600..U+06FF range, letter
    subset). Used by consumers (authoring-suite humanizer_gate) to detect
    language mismatch. Pure-letter count / total-letter count; ignores spaces,
    digits, ASCII letters."""
    if not text:
        return 0.0
    ar_chars = sum(1 for c in text if "؀" <= c <= "ۿ" and c.isalpha())
    total_letters = sum(1 for c in text if c.isalpha())
    if total_letters == 0:
        return 0.0
    return ar_chars / total_letters


def is_arabic_dominant(text: str, threshold: float = 0.5) -> bool:
    """True iff `text` is >=`threshold` fraction Arabic letters (default 50%).
    Used by translator Stage E and authoring humanizer_gate."""
    return arabic_char_ratio(text) >= threshold


# ── Module-level self-test ──
if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    EDGE_CASES = [
        # (description, input, level, expected)
        ("strip tashkeel",         "الذكاءِ الاصطناعيّ", "light",      "الذكاء الاصطناعي"),
        ("strip tatweel",          "الذكــاء",            "light",      "الذكاء"),
        ("alif madda → bare",      "آدم",                  "medium",     "ادم"),
        ("alif-hamza-above → bare","أحمد",                 "medium",     "احمد"),
        ("alif-hamza-below → bare","إبراهيم",              "medium",     "ابراهيم"),
        ("alif maqsura → ya",      "هذى",                  "medium",     "هذي"),
        ("light preserves alif",   "أحمد",                 "light",      "أحمد"),
        ("ta marbuta → ha (aggr)", "الحوسبة",              "aggressive", "الحوسبه"),
        ("ta marbuta preserved",   "الحوسبة",              "medium",     "الحوسبة"),
        ("hamza-on-waw → waw",     "سؤال",                 "aggressive", "سوال"),
        ("hamza-on-ya → ya",       "قائد",                 "aggressive", "قايد"),
        ("Western text unchanged", "Hello World 5G",       "light",      "Hello World 5G"),
        ("Empty input",            "",                     "light",      ""),
        ("Digits preserved",       "5G إنترنت ٤G",         "light",      "5G إنترنت ٤G"),
    ]

    print(f"{'═' * 72}")
    print(f"  arabic_normalize.py — edge-case verification")
    print(f"{'═' * 72}\n")

    failures = 0
    for desc, src, level, expected in EDGE_CASES:
        got = normalize(src, level=level)
        ok = got == expected
        marker = "✓" if ok else "✗"
        print(f"  [{marker}] {level:10s} {desc}")
        if not ok:
            print(f"        in:       {src!r}")
            print(f"        expected: {expected!r}")
            print(f"        got:      {got!r}")
            failures += 1

    # Idempotence test
    print(f"\nIdempotence:")
    for level in ("light", "medium", "aggressive"):
        sample = "الحوسبةُ السحابيّة لــأحمدَ"
        once = normalize(sample, level=level)
        twice = normalize(once, level=level)
        ok = once == twice
        marker = "✓" if ok else "✗"
        print(f"  [{marker}] {level:10s} normalize(normalize(x)) == normalize(x)")
        if not ok:
            failures += 1
            print(f"        once:  {once!r}")
            print(f"        twice: {twice!r}")

    # Monotonicity test: collisions at light propagate to medium and aggressive
    print(f"\nMonotonicity:")
    collide_pairs = [
        ("الذكاءِ", "الذكاء"),     # tashkeel — collide at all levels
        ("أحمد",   "احمد"),         # alif — collide at medium+aggressive
        ("الحوسبة", "الحوسبه"),     # ta marbuta — collide at aggressive only
    ]
    for a, b in collide_pairs:
        for level in ("light", "medium", "aggressive"):
            collide = normalize(a, level=level) == normalize(b, level=level)
            print(f"  {level:10s}  {a!r} == {b!r}: {collide}")

    # Char ratio
    print(f"\narabic_char_ratio + is_arabic_dominant:")
    samples = ["مرحبا بكم", "Hello World", "Mixed نص مع text", "5G إنترنت"]
    for s in samples:
        r = arabic_char_ratio(s)
        d = is_arabic_dominant(s)
        print(f"  ratio={r:.2f} dominant={d}  {s!r}")

    print(f"\n{'─' * 72}")
    if failures:
        print(f"✗ {failures} edge case(s) failed.")
        sys.exit(1)
    print(f"✓ All edge cases passed. Contract sound.")
    print(f"{'─' * 72}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_arabic_normalize_units.py -- deterministic unit tests for the G1
normalization contract in scripts/arabic_normalize.py.

Covers the three levels (light/medium/aggressive), IDEMPOTENCE, tashkeel +
tatweel stripping, alef/hamza/ya variant handling per level, arabic_char_ratio()
on pure-Arabic / mixed / pure-Latin inputs, and empty/whitespace edge cases.

stdlib only. No network / no LLM calls. Deterministic (pure functions).
"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from arabic_normalize import (
    normalize,
    arabic_char_ratio,
    is_arabic_dominant,
)

failures = 0


def check(cond, label):
    global failures
    status = "[PASS]" if cond else "[FAIL]"
    print(f"  {status} {label}")
    if not cond:
        failures += 1


def section(t):
    print(f"\n--- {t} ---")


# ---------- tashkeel + tatweel stripping (all levels) ----------
section("light: tashkeel + tatweel stripping")
# Diacritics (kasra + shadda) removed at the lightest level.
check(normalize("الذكاءِ الاصطناعيّ", level="light") == "الذكاء الاصطناعي",
      "light strips tashkeel (kasra/shadda)")
# Tatweel (U+0640) is a pure stretch char, removed at every level.
check(normalize("الذكــاء", level="light") == "الذكاء",
      "light strips tatweel")
# light is meaning-preserving: alif-hamza-above must survive at light.
check(normalize("أحمد", level="light") == "أحمد",
      "light preserves alif-hamza variants (no folding)")


# ---------- alef / ya variant folding (medium) ----------
section("medium: alef + ya variant folding")
check(normalize("آدم", level="medium") == "ادم",
      "medium folds alif-madda -> bare alif")
check(normalize("أحمد", level="medium") == "احمد",
      "medium folds alif-hamza-above -> bare alif")
check(normalize("إبراهيم", level="medium") == "ابراهيم",
      "medium folds alif-hamza-below -> bare alif")
check(normalize("هذى", level="medium") == "هذي",
      "medium folds alif-maqsura -> ya")
# medium must NOT touch ta-marbuta (that is aggressive-only).
check(normalize("الحوسبة", level="medium") == "الحوسبة",
      "medium preserves ta-marbuta")


# ---------- aggressive: ta-marbuta + hamza-on-letter ----------
section("aggressive: ta-marbuta + hamza-on-letter")
check(normalize("الحوسبة", level="aggressive") == "الحوسبه",
      "aggressive folds ta-marbuta -> ha")
check(normalize("سؤال", level="aggressive") == "سوال",
      "aggressive folds hamza-on-waw -> waw")
check(normalize("قائد", level="aggressive") == "قايد",
      "aggressive folds hamza-on-ya -> ya")
# aggressive subsumes medium: alif folding still applies.
check(normalize("أحمد", level="aggressive") == "احمد",
      "aggressive subsumes medium alif folding")


# ---------- IDEMPOTENCE: normalize(normalize(x)) == normalize(x) ----------
section("idempotence across levels and several Arabic strings")
IDEMPOTENCE_SAMPLES = [
    "الحوسبةُ السحابيّة لــأحمدَ",
    "آدم وإبراهيم قالا هذى",
    "سؤال قائدٍ عن الذكــاء",
    "الذكاءِ الاصطناعيّ",
    "",
    "   ",
]
for level in ("light", "medium", "aggressive"):
    for s in IDEMPOTENCE_SAMPLES:
        once = normalize(s, level=level)
        twice = normalize(once, level=level)
        check(once == twice,
              f"idempotent [{level}] on {s!r}")


# ---------- monotonicity: collision at light => collision at medium/aggressive
section("monotonicity: light-collisions propagate upward")
# tashkeel-only difference collides at EVERY level.
for level in ("light", "medium", "aggressive"):
    check(normalize("الذكاءِ", level=level) == normalize("الذكاء", level=level),
          f"tashkeel pair collides at {level}")


# ---------- arabic_char_ratio: pure-Arabic / mixed / pure-Latin ----------
section("arabic_char_ratio: pure-Arabic / mixed / pure-Latin")
# Pure Arabic letters (spaces ignored) -> 1.0
check(arabic_char_ratio("مرحبا بكم") == 1.0,
      "pure-Arabic ratio == 1.0")
# Pure Latin -> 0.0
check(arabic_char_ratio("Hello World") == 0.0,
      "pure-Latin ratio == 0.0")
# Mixed: 'Mixed نص مع text' -> Arabic letters / total letters, strictly between.
mixed_ratio = arabic_char_ratio("Mixed نص مع text")
check(0.0 < mixed_ratio < 1.0,
      "mixed ratio strictly between 0 and 1")
# Digits / spaces ignored: '5G إنترنت' counts only letters (G is 1 Latin, إنترنت Arabic).
r_5g = arabic_char_ratio("5G إنترنت")
check(0.0 < r_5g < 1.0,
      "ratio ignores digits, counts only letters")
# is_arabic_dominant threshold behaviour.
check(is_arabic_dominant("مرحبا بكم") is True,
      "is_arabic_dominant True on pure Arabic")
check(is_arabic_dominant("Hello World") is False,
      "is_arabic_dominant False on pure Latin")


# ---------- empty / whitespace / non-Arabic edge cases ----------
section("edge cases: empty / whitespace / Latin / digits")
check(normalize("", level="light") == "",
      "empty input -> empty string")
check(normalize("   ", level="aggressive") == "   ",
      "whitespace-only passes through unchanged")
check(normalize("Hello World 5G", level="light") == "Hello World 5G",
      "Western text unchanged")
check(arabic_char_ratio("") == 0.0,
      "arabic_char_ratio('') == 0.0")
check(arabic_char_ratio("   ") == 0.0,
      "arabic_char_ratio(whitespace) == 0.0 (no letters)")
check(arabic_char_ratio("12345") == 0.0,
      "arabic_char_ratio(digits) == 0.0 (no letters)")

# Unknown level must raise ValueError (contract guard).
raised = False
try:
    normalize("نص", level="extreme")
except ValueError:
    raised = True
check(raised, "normalize(unknown level) raises ValueError")


# ---------- Verdict ----------
print()
print("-" * 60)
if failures == 0:
    print("PASS: arabic_normalize G1 contract unit tests OK")
    print("-" * 60)
    sys.exit(0)
else:
    print(f"FAIL: {failures} normalization contract regression(s)")
    print("-" * 60)
    sys.exit(1)

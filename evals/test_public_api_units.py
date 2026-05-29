#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_public_api_units.py -- deterministic unit tests for the public read APIs.

Covers dictionary.py, asset_registry.py, register.py, lexical_tables.py against
the REAL committed corpus/*.json assets. Asserts returned structures and edge
cases: missing key, empty/unknown input, npm-range MAJOR-bump incompatibility.

stdlib only. No network / no LLM calls. Deterministic.
"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import dictionary as dic
import asset_registry as ar
import register as reg
import lexical_tables as lt

failures = 0


def check(cond, label):
    global failures
    status = "[PASS]" if cond else "[FAIL]"
    print(f"  {status} {label}")
    if not cond:
        failures += 1


def section(t):
    print(f"\n--- {t} ---")


# ---------- dictionary.py ----------
section("dictionary: load + lookup + edge cases")
keys, lookup = dic.load_dictionary()
assert isinstance(keys, list) and isinstance(lookup, dict)  # structural sanity
check(isinstance(keys, list) and isinstance(lookup, dict),
      "load_dictionary() returns (list, dict)")
check(dic.entry_count() > 0, "entry_count() > 0 against real corpus")

# Known entry from real corpus ('Series A' confirmed present).
hits = dic.find_by_en("Series A")
check(len(hits) == 1, "find_by_en('Series A') returns exactly one entry")
check(hits and hits[0].get("en") == "Series A",
      "returned entry has matching 'en' field")

# Edge: missing key -> empty list, canonical -> None.
check(dic.find_by_en("___no_such_english_term___") == [],
      "find_by_en(missing) returns empty list")
check(dic.find_canonical("___no_such_english_term___") is None,
      "find_canonical(missing) returns None")

st = dic.stats()
check(set(st).issuperset({"total", "high_confidence", "topic_guarded"}),
      "stats() exposes total/high_confidence/topic_guarded keys")
check(st["total"] == dic.entry_count(),
      "stats()['total'] agrees with entry_count()")


# ---------- asset_registry.py: npm-style ranges ----------
section("asset_registry: is_compatible + ranges + edge cases")
check(ar.current_version("A") == "1.2.0",
      "current_version('A') == '1.2.0' (real registry)")
check(ar.compatibility_band("A") == "^1.0.0",
      "compatibility_band('A') == '^1.0.0'")

# ^1.0.0 means [1.0.0, 2.0.0): minor/patch inside band are compatible.
check(ar.is_compatible("A", "1.0.0") is True,
      "is_compatible: lower-bound 1.0.0 within ^1.0.0")
check(ar.is_compatible("A", "1.5.0") is True,
      "is_compatible: minor bump 1.5.0 within ^1.0.0")

# MAJOR bump 2.0.0 is OUTSIDE ^1.0.0 -> incompatible.
check(ar.is_compatible("A", "2.0.0") is False,
      "is_compatible: MAJOR bump 2.0.0 incompatible with ^1.0.0")

# Edge: unknown asset / malformed version are swallowed to False, never raise.
check(ar.is_compatible("___no_asset___", "1.0.0") is False,
      "is_compatible(unknown asset) returns False (no raise)")
check(ar.is_compatible("A", "not-a-semver") is False,
      "is_compatible(malformed version) returns False (no raise)")

# Edge: current_version on unknown asset raises KeyError.
raised = False
try:
    ar.current_version("___no_asset___")
except KeyError:
    raised = True
check(raised, "current_version(unknown) raises KeyError")

# required_for returns the consumer's declared map.
reqs = ar.required_for("humanizer")
check(isinstance(reqs, dict) and reqs.get("A") == "^1.0.0",
      "required_for('humanizer') maps asset A -> '^1.0.0'")

# check_consumer audit: real registry should be internally consistent.
report = ar.check_consumer("humanizer")
check(report.has_problems is False,
      "check_consumer('humanizer') reports no problems on shipped registry")


# ---------- register.py: policy retrieval ----------
section("register: policy_for + edge cases")
pol = reg.policy_for("news")
check(pol.get("applies_calque_dictionary") is True,
      "policy_for('news').applies_calque_dictionary is True")
check(reg.policy_for("technical").get("applies_calque_dictionary") is False,
      "policy_for('technical').applies_calque_dictionary is False")
check("news" in reg.known_registers() and "classical" in reg.known_registers(),
      "known_registers() includes news + classical")

# Defensive copy: mutating the returned dict must not corrupt the source.
pol["applies_calque_dictionary"] = "MUTATED"
check(reg.policy_for("news").get("applies_calque_dictionary") is True,
      "policy_for returns a defensive copy (mutation does not leak)")

# Edge: unknown register raises.
raised = False
try:
    reg.policy_for("___no_register___")
except reg.UnknownRegisterError:
    raised = True
check(raised, "policy_for(unknown) raises UnknownRegisterError")


# ---------- lexical_tables.py: load + lookups + edge cases ----------
section("lexical_tables: load + table lookups + edge cases")
check(lt.schema_version() == "1.1.0",
      "schema_version() == '1.1.0' (real asset)")
names = lt.table_names()
check("ai_phrases" in names and "connectors" in names,
      "table_names() includes ai_phrases + connectors")
check(lt.soft_validate() == [],
      "soft_validate() returns no errors on shipped asset")

# Real ai_phrase: pull a known input from the table itself, assert list result.
first_phrase = lt.get_table("ai_phrases")["entries"][0]["input"]
alts = lt.ai_phrase_alternatives(first_phrase)
check(isinstance(alts, list) and len(alts) > 0,
      "ai_phrase_alternatives(known) returns non-empty list")
# Edge: unknown phrase -> None.
check(lt.ai_phrase_alternatives("___no_such_phrase___") is None,
      "ai_phrase_alternatives(missing) returns None")

# Real connector lookup -> str; unknown -> None.
first_conn = lt.get_table("connectors")["entries"][0]["input"]
check(isinstance(lt.connector_replacement(first_conn), str),
      "connector_replacement(known) returns a string")
check(lt.connector_replacement("___no_such_connector___") is None,
      "connector_replacement(missing) returns None")

# Edge: get_table(unknown) raises KeyError.
raised = False
try:
    lt.get_table("___no_such_table___")
except KeyError:
    raised = True
check(raised, "get_table(unknown) raises KeyError")


# ---------- Verdict ----------
print()
print("-" * 60)
if failures == 0:
    print("PASS: public read-API unit tests OK (28 assertions)")
    print("-" * 60)
    sys.exit(0)
else:
    print(f"FAIL: {failures} public read-API regression(s)")
    print("-" * 60)
    sys.exit(1)

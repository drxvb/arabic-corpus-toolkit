#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
contract_conformance.py — v1.10.1 inter-sibling G1-G4 conformance regression.

Convergent 3-of-4 A5 roadmap-critique vendors flagged this as missing P0:
"Cross-sibling regression detection. All four siblings share G1-G4 contracts.
A change to G1 will have blast radius across all four packages. There's no
shared regression test suite that proves every sibling still obeys the
contracts after any change."

Tests each sibling's adoption of the four foundational contracts:
  G1 — arabic_normalize (toolkit v1.5.0)
  G2 — asset_registry   (toolkit v1.6.0)
  G3 — influence_telemetry (toolkit v1.7.0)
  G4 — install_family   (toolkit v1.8.0)

Adoption matrix expected (12 cells, ✓ = consumer adopts):

| Contract | Toolkit | Humanizer | Translator | Authoring |
|---|---|---|---|---|
| G1 normalize | ✓ | ✓ | ✓ | ✓ |
| G2 registry  | ✓ | ✓ | ✓ | ✓ |
| G3 telemetry | ✓ | ✓ | ✓ | ✓ |
| G4 install   | ✓ | n/a | n/a | n/a |

Plus toolkit v1.10.0 schema-1.3.0 conformance:
  - G.business / G.legal / G.politics expose pairs_below_threshold field
  - n_independent_agree present on active pairs
  - Consumers expose min_consensus parameter

Exit 0 on full pass, 1 on any conformance violation.
"""
from __future__ import annotations
import inspect
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT.parent

sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(PUBLIC / "arabic-corpus-translator" / "scripts"))
sys.path.insert(0, str(PUBLIC / "arabic-authoring-suite" / "scripts"))
sys.path.insert(0, str(PUBLIC / "arabic-ai-text-humanizer" / "scripts"))

PASS = "[PASS]"
FAIL = "[FAIL]"
failures = 0
checks = 0

def check(cond: bool, msg: str) -> None:
    global failures, checks
    checks += 1
    mark = PASS if cond else FAIL
    print(f"  {mark} {msg}")
    if not cond: failures += 1


def section(title: str) -> None:
    print(f"\n━━━ {title} ━━━")


# ─────────────────────────────────────────────────────────────
# G1 — arabic_normalize contract adoption
# ─────────────────────────────────────────────────────────────
section("G1 — arabic_normalize (toolkit canonical)")
try:
    import arabic_normalize
    check(callable(arabic_normalize.normalize), "toolkit: normalize() callable")
    check(callable(arabic_normalize.arabic_char_ratio), "toolkit: arabic_char_ratio() callable")
    sample = "الذكاءُ الاصطناعيِّ"
    expected = arabic_normalize.normalize(sample, level="light")
    again   = arabic_normalize.normalize(expected, level="light")
    check(expected == again, "toolkit: normalize idempotent at light level")
except Exception as e:
    check(False, f"toolkit: arabic_normalize import — {e}")

# Translator: Stage D should route through arabic_normalize
try:
    import translate as t
    src = inspect.getsource(t)
    check("_stage_d_normalize" in src, "translator: _stage_d_normalize helper present")
    check("arabic_normalize" in src, "translator: imports/references arabic_normalize")
except Exception as e:
    check(False, f"translator: G1 conformance — {e}")

# Authoring: humanizer_gate should route through arabic_char_ratio
try:
    import generate as g
    src = inspect.getsource(g)
    check("arabic_normalize" in src or "arabic_char_ratio" in src,
          "authoring: arabic_normalize/arabic_char_ratio referenced")
except Exception as e:
    check(False, f"authoring: G1 conformance — {e}")

# Humanizer: score_text Arabic-char counting should route through arabic_normalize
try:
    import humanize_v2 as h
    src = inspect.getsource(h)
    check("arabic_normalize" in src,
          "humanizer: arabic_normalize referenced (G1 adoption)")
except Exception as e:
    check(False, f"humanizer: G1 conformance — {e}")

# ─────────────────────────────────────────────────────────────
# G2 — asset_registry contract adoption
# ─────────────────────────────────────────────────────────────
section("G2 — asset_registry (toolkit canonical)")
try:
    import asset_registry
    assets = asset_registry.list_assets()
    check(len(assets) >= 12, f"toolkit: registry knows >=12 assets (got {len(assets)})")
    biz_v = asset_registry.current_version("G.business")
    check(biz_v.startswith("1.") and int(biz_v.split(".")[1]) >= 3,
          f"toolkit: G.business at >=1.3 (got {biz_v})")
    pol_v = asset_registry.current_version("G.politics")
    check(pol_v.startswith("1.") and int(pol_v.split(".")[1]) >= 3,
          f"toolkit: G.politics at >=1.3 (got {pol_v})")
    # is_compatible smoke test (npm-range parsing)
    check(asset_registry.is_compatible("G.technology", "1.4.0"),
          "toolkit: is_compatible('G.technology', '1.4.0') → True")
    check(not asset_registry.is_compatible("G.technology", "2.0.0"),
          "toolkit: is_compatible('G.technology', '2.0.0') → False (MAJOR refused)")
    report_t = asset_registry.check_consumer("translator")
    check(getattr(report_t, "problems", None) == [] or report_t.is_clean(),
          f"translator: 0 compat problems")
    report_a = asset_registry.check_consumer("authoring")
    check(getattr(report_a, "problems", None) == [] or report_a.is_clean(),
          f"authoring: 0 compat problems")
    report_h = asset_registry.check_consumer("humanizer")
    check(getattr(report_h, "problems", None) == [] or report_h.is_clean(),
          f"humanizer: 0 compat problems")
except Exception as e:
    check(False, f"toolkit: asset_registry — {e}")

# Translator: should call _check_asset_compat routing through registry
try:
    src = inspect.getsource(t)
    check("_check_asset_compat" in src, "translator: _check_asset_compat helper present")
    check("registry" in src.lower() or "asset_registry" in src,
          "translator: references asset_registry")
except Exception as e:
    check(False, f"translator: G2 conformance — {e}")

# Authoring: should reference asset_registry
try:
    src = inspect.getsource(g)
    check("registry" in src.lower() or "is_compatible" in src,
          "authoring: registry-aware compat check present")
except Exception as e:
    check(False, f"authoring: G2 conformance — {e}")

# Humanizer: should reference asset_registry
try:
    src = inspect.getsource(h)
    check("_registry_is_compatible" in src or "asset_registry" in src,
          "humanizer: registry adoption present")
except Exception as e:
    check(False, f"humanizer: G2 conformance — {e}")

# ─────────────────────────────────────────────────────────────
# G3 — influence_telemetry contract adoption
# ─────────────────────────────────────────────────────────────
section("G3 — influence_telemetry (toolkit canonical)")
try:
    import influence_telemetry
    trace = influence_telemetry.InfluenceTrace()
    trace.record(asset_id="X", asset_version="1.0.0", trigger="term_hint_injected",
                 evidence={"k": "v"}, stage="A")
    check(len(trace.as_json()) == 1, "toolkit: trace.record() works")
except Exception as e:
    check(False, f"toolkit: influence_telemetry — {e}")

# Translator: stage_a_terminology emits trace + threads to D/E/F
try:
    src = inspect.getsource(t)
    check("_new_influence_trace" in src or "InfluenceTrace" in src,
          "translator: instantiates InfluenceTrace")
    check("term_hint_injected" in src, "translator: emits term_hint_injected trigger")
    check("lex_substitution_fired" in src, "translator: Stage D emits lex_substitution_fired")
    check("humanizer_gate_decision" in src, "translator: Stage F emits humanizer_gate_decision")
except Exception as e:
    check(False, f"translator: G3 conformance — {e}")

# Authoring: production path emits trace
try:
    src = inspect.getsource(g)
    check("_new_authoring_trace" in src or "InfluenceTrace" in src,
          "authoring: instantiates InfluenceTrace")
    check("term_hint_injected" in src, "authoring: emits term_hint_injected trigger")
    # The A4 killer fix: trace must be threaded through _find_terminology_hits production call
    assert "_find_terminology_hits(scan_text, domain, trace=trace" in src, \
        "authoring: production path threads trace= to _find_terminology_hits (A4 killer fix)"
    check(True, "authoring: A4 killer-finding fix in place (trace threaded in production)")
except Exception as e:
    check(False, f"authoring: G3 conformance — {e}")

# Humanizer: score_text emits trace via emit_trace=True path
try:
    src = inspect.getsource(h)
    check("emit_trace" in src, "humanizer: emit_trace parameter present in scoring")
    check("InfluenceTrace" in src or "_new_humanizer_trace" in src,
          "humanizer: InfluenceTrace instantiation")
except Exception as e:
    check(False, f"humanizer: G3 conformance — {e}")

# ─────────────────────────────────────────────────────────────
# G4 — install_family contract
# ─────────────────────────────────────────────────────────────
section("G4 — install_family")
ifp = ROOT / "install_family.py"
check(ifp.exists(), f"toolkit: install_family.py at {ifp.name}")
if ifp.exists():
    txt = ifp.read_text(encoding="utf-8", errors="replace")
    check("ACQUIRE" in txt or "git clone" in txt, "install_family: acquire phase present")
    check("VERIFY" in txt or "family_doctor" in txt, "install_family: verify phase present")
    check("encoding=\"utf-8\"" in txt or "encoding='utf-8'" in txt,
          "install_family: utf-8 subprocess encoding (Windows cp1252 fix)")

# ─────────────────────────────────────────────────────────────
# Toolkit v1.10.0 schema-1.3.0 (new domain consensus tiering)
# ─────────────────────────────────────────────────────────────
section("Toolkit v1.10.0 — schema 1.3.0 tiered domain assets")
for domain in ("business", "legal", "politics"):
    p = ROOT / "corpus" / f"domain-terminology-{domain}.json"
    if not p.exists():
        check(False, f"G.{domain}: file missing"); continue
    data = json.loads(p.read_text(encoding="utf-8"))
    schema = data.get("$schema_version", "")
    schema_major = schema.split(".")[0] if "." in schema else schema
    # v1.10.0 introduced schema 1.3.0; v1.11.0 bumps to 1.4.0; both honor the same contract surface.
    check(schema_major == "1" and int(schema.split(".")[1]) >= 3,
          f"G.{domain}: schema >=1.3.x (got {schema})")
    check("pairs_below_threshold" in data, f"G.{domain}: pairs_below_threshold present")
    check("validation_method" in data, f"G.{domain}: validation_method present")
    if data.get("pairs"):
        sample = data["pairs"][0]
        check("n_independent_agree" in sample, f"G.{domain}: pairs have n_independent_agree")
        check(0 <= sample.get("n_independent_agree", -1) <= 3,
              f"G.{domain}: n_independent_agree in [0,3]")

# ─────────────────────────────────────────────────────────────
# Consumer min_consensus API (translator v1.8.0, authoring v1.6.0)
# ─────────────────────────────────────────────────────────────
section("Consumer min_consensus API (translator v1.8.0 / authoring v1.6.0)")
try:
    sig_t = inspect.signature(t.translate)
    check("min_consensus" in sig_t.parameters,
          f"translator.translate: min_consensus param present (sig={list(sig_t.parameters)[:10]})")
    sig_h = inspect.signature(t._find_terminology_pairs_in_text)
    check("min_consensus" in sig_h.parameters,
          "translator._find_terminology_pairs_in_text: min_consensus param present")

    # Behavioral check
    biz_text = "central bank board of directors crude oil"
    hits_1 = t._find_terminology_pairs_in_text(biz_text, "business", min_consensus=1)
    hits_3 = t._find_terminology_pairs_in_text(biz_text, "business", min_consensus=3)
    check(len(hits_1) >= len(hits_3), f"translator: min_consensus=3 returns <= min_consensus=1 (got {len(hits_1)}/{len(hits_3)})")
    if hits_3:
        check(all(h.get("n_independent_agree") == 3 for h in hits_3),
              "translator: min_consensus=3 only returns 3/3 unanimous pairs")

    # backward compat — G.technology pairs lack the field
    tech_text = "artificial intelligence machine learning"
    h1 = t._find_terminology_pairs_in_text(tech_text, "technology", min_consensus=1)
    h3 = t._find_terminology_pairs_in_text(tech_text, "technology", min_consensus=3)
    check(len(h1) == len(h3), "translator: G.technology (no n_independent_agree) identical at all thresholds")
except Exception as e:
    check(False, f"translator min_consensus API — {e}")

try:
    sig_g = inspect.signature(g.generate)
    check("min_consensus" in sig_g.parameters,
          "authoring.generate: min_consensus param present")
    sig_f = inspect.signature(g._find_terminology_hits)
    check("min_consensus" in sig_f.parameters,
          "authoring._find_terminology_hits: min_consensus param present")
    # Behavioral
    h1 = g._find_terminology_hits("central bank board of directors", "business", min_consensus=1)
    h3 = g._find_terminology_hits("central bank board of directors", "business", min_consensus=3)
    check(len(h1) >= len(h3), f"authoring: min_consensus=3 returns <= min_consensus=1 (got {len(h1)}/{len(h3)})")
except Exception as e:
    check(False, f"authoring min_consensus API — {e}")

# ─────────────────────────────────────────────────────────────
# Adoption matrix summary
# ─────────────────────────────────────────────────────────────
section("Adoption matrix verdict")
print(f"  Total conformance checks: {checks}")
print(f"  Passed: {checks - failures}")
print(f"  Failed: {failures}")
print()
print("─" * 60)
if failures == 0:
    print(f"✓ Inter-sibling contract conformance INTACT ({checks}/{checks})")
    print("─" * 60)
    sys.exit(0)
else:
    print(f"✗ {failures}/{checks} conformance violations")
    print("─" * 60)
    sys.exit(1)

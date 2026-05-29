#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_safe_llm_call.py -- v1.13.0 regression suite for safe_llm_call contract.

Closes the cross-cutting A7 multi-vendor convergent gap. 12 assertions across 5 fixtures.
"""
from __future__ import annotations
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from safe_llm_call import (
    safe_llm_call, LLMCallResult, reset_circuit,
    CIRCUIT_THRESHOLD, CIRCUIT_RESET_S,
)

PASS, FAIL = "[PASS]", "[FAIL]"
failures = 0
def check(cond, label, detail=""):
    global failures
    print(f"  {PASS if cond else FAIL} {label}" + (f" — {detail}" if detail else ""))
    if not cond: failures += 1
def section(t): print(f"\n--- {t} ---")


# ---------- A: unreachable endpoint never raises ----------
section("A: unreachable endpoint MUST return structured failure (never raise)")
reset_circuit()
r = safe_llm_call("http://127.0.0.1:1", "fake-key",
                  {"model": "x", "messages": [{"role":"user","content":"x"}]},
                  timeout=1.0, max_retries=0)
check(isinstance(r, LLMCallResult), "returns LLMCallResult, never raises")
check(r.ok is False, "ok=False for unreachable")
check(r.error_class in ("network", "timeout"),
      f"error_class is network or timeout (got {r.error_class!r})")
check(r.payload is None, "payload=None on failure")
check(r.attempts == 1, f"attempts=1 (max_retries=0; got {r.attempts})")


# ---------- B: circuit breaker triggers after threshold ----------
section("B: circuit breaker opens after CIRCUIT_THRESHOLD consecutive failures")
reset_circuit()
results = []
for _ in range(CIRCUIT_THRESHOLD + 1):
    results.append(safe_llm_call("http://127.0.0.1:1", "fake-key",
                                  {"model":"x","messages":[{"role":"user","content":"x"}]},
                                  timeout=1.0, max_retries=0))
check(results[-1].circuit_open is True,
      f"circuit open after {CIRCUIT_THRESHOLD}+ failures")
check(results[-1].error_class == "circuit_open",
      f"last attempt short-circuits with error_class='circuit_open' (got {results[-1].error_class!r})")
check(results[-1].attempts == 0,
      f"short-circuit attempt counted as 0 attempts (got {results[-1].attempts})")
check(results[-1].latency_ms < 100,
      f"short-circuit is fast (<100ms; got {results[-1].latency_ms}ms)")


# ---------- C: reset_circuit() unblocks ----------
section("C: reset_circuit() lets calls through again")
reset_circuit()
r = safe_llm_call("http://127.0.0.1:1", "fake-key",
                  {"model":"x","messages":[{"role":"user","content":"x"}]},
                  timeout=1.0, max_retries=0)
check(r.circuit_open is False, "after reset, circuit is closed")


# ---------- D: retries are exponential-backoff bounded ----------
section("D: max_retries respects bound and times out reasonably")
reset_circuit()
import time
t0 = time.time()
r = safe_llm_call("http://127.0.0.1:1", "fake-key",
                  {"model":"x","messages":[{"role":"user","content":"x"}]},
                  timeout=1.0, max_retries=2, retry_backoff_s=0.1)
elapsed = time.time() - t0
check(r.attempts == 3, f"3 attempts with max_retries=2 (got {r.attempts})")
check(elapsed < 5.0, f"total bounded under 5s (got {elapsed:.1f}s)")


# ---------- E: malformed payload doesn't raise ----------
section("E: unencodable payload returns structured failure")
reset_circuit()
class _NotJSON: pass
r = safe_llm_call("http://127.0.0.1:1", "fake-key",
                  {"model":"x","msg": _NotJSON()},  # not json-encodable
                  timeout=1.0)
check(r.ok is False, "unencodable payload -> ok=False")
check(r.error_class == "payload_encode",
      f"error_class=payload_encode (got {r.error_class!r})")


# Verdict
print()
print("─" * 60)
if failures == 0:
    print("✓ safe_llm_call contract INTACT (12 assertions)")
    print("─" * 60)
    sys.exit(0)
else:
    print(f"✗ {failures} safe_llm_call regressions")
    print("─" * 60)
    sys.exit(1)

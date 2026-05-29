#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
safe_llm_call.py — v1.13.0 shared LLM proxy failure-resilience contract.

Closes the cross-cutting A7 multi-vendor convergent gap:
  - translator: 4/4 vendors (codex + gemini + minimax + deepseek) flagged
    LLM provider failure handling as the #1 must-have
  - humanizer:  3/4 vendors (codex + minimax + deepseek) flagged LLM error
    handling + retry + circuit-breaker
  - authoring:  inherits via draft_section calls
  - toolkit:    3/4 vendors flagged API contract stability

The Contract — `safe_llm_call(vendor_url, api_key, payload, timeout=60,
max_retries=2, retry_backoff_s=2.0)` returns:

    LLMCallResult(
        ok:           bool,         # True if a real LLM response was obtained
        payload:      Optional[str], # the LLM's message content (None on failure)
        error_class:  Optional[str], # "timeout" | "http_5xx" | "http_4xx" |
                                    # "json_decode" | "auth" | "network" |
                                    # "empty_response" | "unknown"
        error_detail: Optional[str], # human-readable detail
        latency_ms:   int,          # total wall-clock including retries
        attempts:     int,          # how many tries (1 on first-pass success)
        circuit_open: bool,         # True if this vendor was circuit-broken
    )

The contract NEVER raises an exception. Consumers check `.ok`. This is the
explicit failure-state pattern the panel asked for.

# Why this lives in the toolkit, not each sibling

3 of 4 siblings make LLM calls. Duplicating retry / circuit-breaker / failure
envelope code in each sibling would drift. Centralizing here, the same
contract serves translator Stages C/E, humanizer score_text_deep, authoring
draft_section, and any future sibling.

Python 3 stdlib only.
"""
from __future__ import annotations
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# Module-level circuit-breaker state per vendor URL. Each vendor tracks
# consecutive failures; on >= CIRCUIT_THRESHOLD, subsequent calls short-circuit
# for CIRCUIT_RESET_S seconds. Stateless retry within a single call is
# separate (controlled by max_retries kwarg).
CIRCUIT_THRESHOLD = 3
CIRCUIT_RESET_S = 60.0
_CIRCUIT_STATE: Dict[str, Dict[str, Any]] = {}


@dataclass
class LLMCallResult:
    """Structured pass/fail envelope. NEVER raises; consumers check .ok."""
    ok: bool
    payload: Optional[str] = None
    error_class: Optional[str] = None
    error_detail: Optional[str] = None
    latency_ms: int = 0
    attempts: int = 0
    circuit_open: bool = False
    http_status: Optional[int] = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __bool__(self) -> bool:
        return self.ok


def _circuit_state(vendor_url: str) -> Dict[str, Any]:
    """Get or create per-vendor circuit-breaker state."""
    if vendor_url not in _CIRCUIT_STATE:
        _CIRCUIT_STATE[vendor_url] = {
            "consecutive_failures": 0,
            "circuit_opened_at": None,
        }
    return _CIRCUIT_STATE[vendor_url]


def _is_circuit_open(vendor_url: str, now: float) -> bool:
    """True if this vendor is currently circuit-broken."""
    st = _circuit_state(vendor_url)
    if st["circuit_opened_at"] is None:
        return False
    if now - st["circuit_opened_at"] >= CIRCUIT_RESET_S:
        # Reset
        st["circuit_opened_at"] = None
        st["consecutive_failures"] = 0
        return False
    return True


def _record_failure(vendor_url: str, now: float) -> None:
    st = _circuit_state(vendor_url)
    st["consecutive_failures"] += 1
    if st["consecutive_failures"] >= CIRCUIT_THRESHOLD and st["circuit_opened_at"] is None:
        st["circuit_opened_at"] = now


def _record_success(vendor_url: str) -> None:
    st = _circuit_state(vendor_url)
    st["consecutive_failures"] = 0
    st["circuit_opened_at"] = None


def reset_circuit(vendor_url: Optional[str] = None) -> None:
    """Reset circuit state for one vendor or all. Useful for tests."""
    if vendor_url is None:
        _CIRCUIT_STATE.clear()
    else:
        _CIRCUIT_STATE.pop(vendor_url, None)


def safe_llm_call(vendor_url: str,
                  api_key: str,
                  payload: Dict[str, Any],
                  timeout: float = 60.0,
                  max_retries: int = 2,
                  retry_backoff_s: float = 2.0,
                  path: str = "/v1/chat/completions") -> LLMCallResult:
    """Make an OpenAI-compatible chat-completions request with retries +
    circuit breaker + structured failure envelope.

    Args:
        vendor_url: base URL like "http://192.168.80.107:11438"
        api_key:    bearer token
        payload:    OpenAI Chat Completions request body (model + messages + ...)
        timeout:    per-attempt timeout in seconds
        max_retries: number of retries on transient failures (default 2)
        retry_backoff_s: exponential backoff base (sleeps backoff * (2**attempt))
        path:       endpoint path (defaults to chat completions)

    Returns:
        LLMCallResult — check .ok; payload contains the message content on success.

    Never raises. All exceptions become structured failure envelopes.
    """
    started = time.time()
    attempts = 0

    # Circuit-breaker check
    if _is_circuit_open(vendor_url, started):
        return LLMCallResult(
            ok=False, error_class="circuit_open",
            error_detail=f"vendor {vendor_url} is circuit-broken after "
                         f"{CIRCUIT_THRESHOLD}+ consecutive failures; "
                         f"will reset {CIRCUIT_RESET_S:.0f}s after the last failure",
            latency_ms=int((time.time() - started) * 1000),
            attempts=0, circuit_open=True,
        )

    try:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as e:
        return LLMCallResult(
            ok=False, error_class="payload_encode",
            error_detail=f"payload could not be JSON-encoded: {e}",
            latency_ms=int((time.time() - started) * 1000),
            attempts=0,
        )

    last_error_class = None
    last_error_detail = None
    last_status = None

    for attempt in range(max_retries + 1):
        attempts = attempt + 1
        req = urllib.request.Request(
            url=vendor_url.rstrip("/") + path,
            data=body, method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json; charset=utf-8",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as e:
                last_error_class = "json_decode"
                last_error_detail = f"response not valid JSON: {e}"
                # Don't retry JSON-decode failures (deterministic from vendor)
                break
            try:
                content = parsed["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as e:
                last_error_class = "schema_mismatch"
                last_error_detail = (
                    f"response missing choices[0].message.content: {e}; "
                    f"got keys={list(parsed.keys())[:5] if isinstance(parsed, dict) else type(parsed).__name__}")
                break
            if not content or not content.strip():
                last_error_class = "empty_response"
                last_error_detail = "vendor returned empty message.content"
                # Don't retry empty responses; vendor consistently returns empty
                break
            _record_success(vendor_url)
            return LLMCallResult(
                ok=True, payload=content,
                latency_ms=int((time.time() - started) * 1000),
                attempts=attempts, http_status=200,
            )
        except urllib.error.HTTPError as e:
            last_status = e.code
            if 500 <= e.code < 600:
                last_error_class = "http_5xx"
                last_error_detail = f"HTTP {e.code}: {e.reason}"
                # retry below
            elif 400 <= e.code < 500:
                if e.code in (401, 403):
                    last_error_class = "auth"
                    last_error_detail = f"HTTP {e.code}: authentication failed"
                else:
                    last_error_class = "http_4xx"
                    last_error_detail = f"HTTP {e.code}: {e.reason}"
                # Don't retry 4xx (deterministic)
                break
            else:
                last_error_class = "http_other"
                last_error_detail = f"HTTP {e.code}: {e.reason}"
                break
        except urllib.error.URLError as e:
            if isinstance(e.reason, TimeoutError) or "timed out" in str(e.reason).lower():
                last_error_class = "timeout"
                last_error_detail = f"URL timeout: {e.reason}"
            else:
                last_error_class = "network"
                last_error_detail = f"network error: {e.reason}"
            # retry below
        except TimeoutError as e:
            last_error_class = "timeout"
            last_error_detail = f"timeout: {e}"
            # retry below
        except Exception as e:
            last_error_class = "unknown"
            last_error_detail = f"{type(e).__name__}: {e}"
            # retry below

        # Retry decision
        if attempt < max_retries and last_error_class in ("timeout", "http_5xx", "network", "unknown"):
            sleep_for = retry_backoff_s * (2 ** attempt)
            time.sleep(sleep_for)
            continue
        else:
            break

    # All attempts exhausted
    _record_failure(vendor_url, time.time())
    return LLMCallResult(
        ok=False,
        error_class=last_error_class or "unknown",
        error_detail=last_error_detail or "no detail captured",
        latency_ms=int((time.time() - started) * 1000),
        attempts=attempts,
        http_status=last_status,
        circuit_open=_is_circuit_open(vendor_url, time.time()),
    )


def safe_llm_call_with_fallback(primary_url: str, primary_key: str,
                                 fallback_url: str, fallback_key: str,
                                 payload: Dict[str, Any],
                                 **kwargs) -> Tuple[LLMCallResult, str]:
    """Try primary vendor; on failure, try fallback. Returns (result, vendor_used)."""
    res = safe_llm_call(primary_url, primary_key, payload, **kwargs)
    if res.ok:
        return res, "primary"
    res2 = safe_llm_call(fallback_url, fallback_key, payload, **kwargs)
    if res2.ok:
        return res2, "fallback"
    # Both failed; return the primary's error envelope
    return res, "both_failed"


# Self-test
if __name__ == "__main__":
    # Synthetic vendor that's guaranteed to fail (unroutable port)
    r = safe_llm_call(
        "http://127.0.0.1:1",  # invalid port
        "fake-key",
        {"model": "test", "messages": [{"role": "user", "content": "test"}]},
        timeout=2.0, max_retries=1, retry_backoff_s=0.1,
    )
    print(f"unreachable: ok={r.ok} error_class={r.error_class} attempts={r.attempts} latency_ms={r.latency_ms}")
    assert not r.ok and r.error_class in ("network", "timeout"), f"expected network/timeout failure, got {r.error_class}"

    # Trigger circuit-breaker by hammering the dead endpoint
    reset_circuit()
    for i in range(CIRCUIT_THRESHOLD + 1):
        r = safe_llm_call("http://127.0.0.1:1", "fake-key",
                          {"model": "test", "messages": [{"role": "user", "content": "x"}]},
                          timeout=1.0, max_retries=0)
        print(f"  attempt {i+1}: ok={r.ok} circuit_open={r.circuit_open} error_class={r.error_class}")
    assert r.circuit_open, "circuit should be open after threshold failures"

    print("\n✓ safe_llm_call self-test PASS")

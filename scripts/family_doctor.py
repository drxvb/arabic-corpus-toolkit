#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
family_doctor.py — v1.1.0 cross-asset + cross-sibling health check.

Inventories every asset in this toolkit, validates each via its soft_validate(),
reports counts, and checks whether each known consumer (humanizer, translator,
authoring-suite) is reachable at the sibling-repo path.

Run:
    python scripts/family_doctor.py            # human-readable report
    python scripts/family_doctor.py --json     # machine-readable

Exit code 0 if all assets soft-validate clean and consumers are reachable.
Exit code 1 if any asset fails validation. Exit code 2 if validation OK but
one or more consumers are missing.

Python 3 stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_PUBLIC_REPOS = _ROOT.parent
sys.path.insert(0, str(_HERE))


ASSET_LOADERS: List[Dict[str, Any]] = [
    {
        "label": "A — calque-dictionary",
        "file": _ROOT / "corpus" / "calque-dictionary.json",
        "module": "dictionary",
        "validate": "stats",
        "count_key": None,
    },
    {
        "label": "B — empirical-patterns",
        "file": _ROOT / "corpus" / "empirical-patterns.json",
        "module": "corpus_stats",
        "validate": "metadata",
        "count_key": None,
    },
    {
        "label": "C — lexical-tables",
        "file": _ROOT / "corpus" / "lexical-tables.json",
        "module": "lexical_tables",
        "validate": "soft_validate",
        "count_key": None,
    },
    {
        "label": "D — typography-rules",
        "file": _ROOT / "corpus" / "typography-rules.json",
        "module": None,
        "validate": None,
        "count_key": None,
    },
    {
        "label": "E — reader-respect-patterns",
        "file": _ROOT / "corpus" / "reader-respect-patterns.json",
        "module": None,
        "validate": None,
        "count_key": None,
    },
    {
        "label": "F.tech — terminology-candidates (technology)",
        "file": _ROOT / "corpus" / "terminology-candidates-technology.json",
        "module": "terminology",
        "validate": "soft_validate",
        "validate_args": ("technology",),
        "count_key": "candidates",
    },
    {
        "label": "F.news — terminology-candidates (news)",
        "file": _ROOT / "corpus" / "terminology-candidates-news.json",
        "module": "terminology",
        "validate": "soft_validate",
        "validate_args": ("news",),
        "count_key": "candidates",
    },
    {
        "label": "G.tech — domain-terminology (technology)",
        "file": _ROOT / "corpus" / "domain-terminology.json",
        "module": "domain_terminology",
        "validate": "soft_validate",
        "count_key": "pairs",
    },
    {
        "label": "G.news — domain-terminology (news)",
        "file": _ROOT / "corpus" / "domain-terminology-news.json",
        "module": None,
        "validate": None,
        "count_key": "pairs",
    },
]


CONSUMERS = [
    {"name": "arabic-ai-text-humanizer", "path": _PUBLIC_REPOS / "arabic-ai-text-humanizer",
     "marker": "scripts/humanize_v2.py", "expected_min_version": "2.7.0"},
    {"name": "arabic-corpus-translator", "path": _PUBLIC_REPOS / "arabic-corpus-translator",
     "marker": "scripts/translate.py", "expected_min_version": "1.0.0"},
    {"name": "arabic-authoring-suite", "path": _PUBLIC_REPOS / "arabic-authoring-suite",
     "marker": "scripts/author.py", "expected_min_version": "1.0.0"},
]


PROXY_HEALTH_URLS = {
    "kimi":    "http://192.168.80.107:11435/health",
    "codex":   "http://192.168.80.107:11436/health",
    "gemini":  "http://192.168.80.107:11437/health",
    "minimax": "http://192.168.80.107:11438/health",
}


def _check_asset(loader_spec: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "label": loader_spec["label"],
        "path": str(loader_spec["file"]),
        "exists": loader_spec["file"].exists(),
        "size_bytes": loader_spec["file"].stat().st_size if loader_spec["file"].exists() else None,
    }
    if not out["exists"]:
        out["status"] = "MISSING"
        return out
    # Try to load and get a count
    if loader_spec.get("module"):
        try:
            mod = __import__(loader_spec["module"])
            args = loader_spec.get("validate_args", ())
            validator_name = loader_spec.get("validate")
            if validator_name == "soft_validate":
                errs = mod.soft_validate(*args)
                out["soft_validate"] = "OK" if not errs else f"{len(errs)} error(s)"
                if errs:
                    out["errors"] = errs[:3]
            elif validator_name == "metadata":
                meta = mod.metadata()
                out["soft_validate"] = "OK" if meta else "empty metadata"
            elif validator_name == "stats":
                stats = mod.stats()
                out["soft_validate"] = f"OK ({stats.get('entry_count', 0)} entries)"
            # Get count
            ck = loader_spec.get("count_key")
            if ck:
                try:
                    data = json.loads(loader_spec["file"].read_text(encoding="utf-8"))
                    out["item_count"] = len(data.get(ck, []))
                    out["schema_version"] = data.get("$schema_version")
                except Exception:
                    pass
        except Exception as e:
            out["soft_validate"] = f"loader error: {e}"
    else:
        # Pure-data assets without a loader — read directly
        try:
            data = json.loads(loader_spec["file"].read_text(encoding="utf-8"))
            out["schema_version"] = data.get("$schema_version") if isinstance(data, dict) else None
            ck = loader_spec.get("count_key")
            if ck and isinstance(data, dict):
                out["item_count"] = len(data.get(ck, []))
            out["soft_validate"] = "OK (no loader; direct read)"
        except Exception as e:
            out["soft_validate"] = f"read error: {e}"

    if "MISSING" not in out.get("status", "") and ("OK" in out.get("soft_validate", "") or out["exists"]):
        out["status"] = "OK"
    return out


def _check_consumer(spec: Dict[str, Any]) -> Dict[str, Any]:
    p = spec["path"]
    marker = p / spec["marker"]
    return {
        "name": spec["name"],
        "path": str(p),
        "marker_present": marker.exists(),
        "expected_min_version": spec["expected_min_version"],
        "status": "OK" if marker.exists() else "MISSING",
    }


def _check_proxies() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for name, url in PROXY_HEALTH_URLS.items():
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                resp = json.loads(r.read().decode())
            out[name] = {"reachable": True, "status": resp.get("status", "unknown")}
        except Exception as e:
            out[name] = {"reachable": False, "error": str(e)[:80]}
    return out


def report(as_json: bool = False) -> int:
    assets = [_check_asset(spec) for spec in ASSET_LOADERS]
    consumers = [_check_consumer(spec) for spec in CONSUMERS]
    proxies = _check_proxies()

    asset_failures = [a for a in assets if a.get("status") != "OK"]
    consumer_failures = [c for c in consumers if c["status"] != "OK"]

    if as_json:
        print(json.dumps({
            "toolkit_root": str(_ROOT),
            "assets": assets,
            "consumers": consumers,
            "proxies": proxies,
            "summary": {
                "asset_count": len(assets),
                "asset_failures": len(asset_failures),
                "consumer_count": len(consumers),
                "consumer_failures": len(consumer_failures),
                "proxy_reachable": sum(1 for p in proxies.values() if p["reachable"]),
            }
        }, ensure_ascii=False, indent=2))
    else:
        print("═" * 78)
        print(f"  arabic-corpus-toolkit family doctor — {_ROOT}")
        print("═" * 78)
        print()
        print(f"ASSETS ({len(assets)} total)")
        for a in assets:
            status = a.get("status", "?")
            marker = "✓" if status == "OK" else "✗"
            extras = []
            if "schema_version" in a:
                extras.append(f"schema={a['schema_version']}")
            if "item_count" in a:
                extras.append(f"items={a['item_count']}")
            if "size_bytes" in a and a["size_bytes"]:
                extras.append(f"{a['size_bytes']:,} bytes")
            extra_str = "  ".join(extras)
            print(f"  [{marker}] {a['label']:50s} {extra_str}")
            if a.get("errors"):
                for e in a["errors"]:
                    print(f"        - {e}")
        print()
        print(f"CONSUMERS ({len(consumers)} total)")
        for c in consumers:
            marker = "✓" if c["status"] == "OK" else "✗"
            print(f"  [{marker}] {c['name']:40s} {c['path']}")
        print()
        print(f"LLM PROXIES")
        for name, info in proxies.items():
            marker = "✓" if info["reachable"] else "✗"
            extra = info.get("status", info.get("error", ""))
            print(f"  [{marker}] {name:10s} {extra}")
        print()
        print("─" * 78)
        if asset_failures:
            print(f"⚠ {len(asset_failures)} asset(s) failing validation.")
        if consumer_failures:
            print(f"⚠ {len(consumer_failures)} consumer(s) not reachable.")
        if not asset_failures and not consumer_failures:
            unreached_proxies = sum(1 for p in proxies.values() if not p["reachable"])
            if unreached_proxies:
                print(f"✓ Assets and consumers healthy. {unreached_proxies} proxies unreachable (LAN issue).")
            else:
                print("✓ Full family healthy: all assets validate, all consumers reachable, all proxies up.")
        print("─" * 78)

    if asset_failures:
        return 1
    if consumer_failures:
        return 2
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="arabic-corpus-toolkit family doctor")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable")
    args = p.parse_args()
    return report(as_json=args.json)


if __name__ == "__main__":
    sys.exit(main())

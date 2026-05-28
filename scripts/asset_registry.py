#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
asset_registry.py — v1.6.0 typed Asset Version Registry (Gap G2).

The third foundational debt all three evaluators (Sonnet/Codex/Gemini) flagged
independently: consumers hardcode `schema_major == "1"` checks and have no
queryable way to ask "what versions of this asset can I read?"

This module provides:
  - current_version(asset_id) → semver string
  - compatibility_band(asset_id) → e.g. "^1.0.0"
  - is_compatible(asset_id, observed_version) → bool
  - required_for(consumer_name) → {asset_id: range}
  - check_consumer(consumer_name) → CompatibilityReport (multi-asset audit)

Backed by `corpus/asset-registry.json`. Python 3 stdlib only.

# Usage

    from asset_registry import is_compatible, check_consumer
    if not is_compatible("G.technology", observed="1.4.0"):
        raise IncompatibleAssetError(...)

    report = check_consumer("translator")
    if report.has_problems:
        for problem in report.problems:
            print(problem)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_HERE = Path(__file__).resolve().parent
_CORPUS = _HERE.parent / "corpus"
_REGISTRY_PATH = _CORPUS / "asset-registry.json"

_registry_cache: Optional[Tuple[float, Dict[str, Any]]] = None


def _load() -> Dict[str, Any]:
    """Return the parsed registry. mtime-cached."""
    global _registry_cache
    if not _REGISTRY_PATH.exists():
        raise FileNotFoundError(f"asset registry not found: {_REGISTRY_PATH}")
    mtime = _REGISTRY_PATH.stat().st_mtime
    if _registry_cache is None or _registry_cache[0] != mtime:
        data = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
        _registry_cache = (mtime, data)
    return _registry_cache[1]


def _parse_semver(s: str) -> Tuple[int, int, int]:
    """Parse "1.2.3" → (1, 2, 3). Accepts trailing pre-release/build tags but ignores them."""
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", s)
    if not m:
        raise ValueError(f"invalid semver: {s!r}")
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _parse_range(spec: str) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """Parse a range spec.
       "^1.0.0"   → [1.0.0, 2.0.0)         (any 1.x.y)
       "~1.2.0"   → [1.2.0, 1.3.0)         (any 1.2.y)
       ">=1.0.0"  → [1.0.0, infinity)
       "1.0.0"    → [1.0.0, 1.0.1)         (exact)
    Returns (lower_inclusive, upper_exclusive) as tuple-semver pairs.
    """
    s = spec.strip()
    INF = (9999, 0, 0)
    if s.startswith("^"):
        base = _parse_semver(s[1:])
        upper = (base[0] + 1, 0, 0)
        return base, upper
    if s.startswith("~"):
        base = _parse_semver(s[1:])
        upper = (base[0], base[1] + 1, 0)
        return base, upper
    if s.startswith(">="):
        base = _parse_semver(s[2:].strip())
        return base, INF
    # Exact match
    base = _parse_semver(s)
    upper = (base[0], base[1], base[2] + 1)
    return base, upper


def _in_range(version: str, spec: str) -> bool:
    """Is `version` within the npm-style range `spec`?"""
    try:
        v = _parse_semver(version)
        lower, upper = _parse_range(spec)
    except ValueError:
        return False
    return lower <= v < upper


def list_assets() -> List[str]:
    """Return all asset IDs in the registry."""
    return sorted(_load().get("assets", {}).keys())


def current_version(asset_id: str) -> str:
    """Return the current shipped version of an asset."""
    assets = _load().get("assets", {})
    if asset_id not in assets:
        raise KeyError(f"unknown asset: {asset_id!r}. Known: {list_assets()}")
    return assets[asset_id]["current_version"]


def compatibility_band(asset_id: str) -> str:
    """Return the compatibility range string for the asset (e.g. '^1.0.0')."""
    assets = _load().get("assets", {})
    if asset_id not in assets:
        raise KeyError(f"unknown asset: {asset_id!r}")
    return assets[asset_id]["compatibility"]


def breaking_versions(asset_id: str) -> List[str]:
    """Explicit deny-list for known-broken point releases."""
    assets = _load().get("assets", {})
    if asset_id not in assets:
        raise KeyError(f"unknown asset: {asset_id!r}")
    return list(assets[asset_id].get("breaking_versions", []))


def is_compatible(asset_id: str, observed_version: str,
                  consumer_requirement: Optional[str] = None) -> bool:
    """Check whether `observed_version` of `asset_id` is acceptable.

    Logic:
      1. If observed is in breaking_versions → False
      2. If consumer specified a requirement → check observed satisfies it
      3. Otherwise → check observed satisfies the asset's declared compatibility band
    """
    try:
        if observed_version in breaking_versions(asset_id):
            return False
        spec = consumer_requirement or compatibility_band(asset_id)
        return _in_range(observed_version, spec)
    except (KeyError, ValueError):
        return False


def required_for(consumer_name: str) -> Dict[str, str]:
    """Return the consumer's declared asset requirements (asset_id → range)."""
    reqs = _load().get("consumer_declared_requirements", {})
    if consumer_name not in reqs:
        raise KeyError(f"unknown consumer: {consumer_name!r}. Known: {sorted(reqs.keys())}")
    return dict(reqs[consumer_name].get("asset_requirements", {}))


@dataclass
class CompatibilityReport:
    consumer: str
    checked_assets: int = 0
    compatible_assets: List[str] = field(default_factory=list)
    incompatible_assets: List[Tuple[str, str, str]] = field(default_factory=list)
    missing_assets: List[str] = field(default_factory=list)

    @property
    def has_problems(self) -> bool:
        return bool(self.incompatible_assets or self.missing_assets)

    @property
    def problems(self) -> List[str]:
        out: List[str] = []
        for asset_id, observed, required in self.incompatible_assets:
            out.append(
                f"Asset {asset_id}: observed v{observed}, consumer requires {required}")
        for asset_id in self.missing_assets:
            out.append(f"Asset {asset_id}: file not present")
        return out


def check_consumer(consumer_name: str) -> CompatibilityReport:
    """Audit consumer's declared requirements against current registry state."""
    report = CompatibilityReport(consumer=consumer_name)
    reqs = required_for(consumer_name)
    report.checked_assets = len(reqs)
    for asset_id, required_range in reqs.items():
        try:
            observed = current_version(asset_id)
        except KeyError:
            report.missing_assets.append(asset_id)
            continue
        if is_compatible(asset_id, observed, consumer_requirement=required_range):
            report.compatible_assets.append(asset_id)
        else:
            report.incompatible_assets.append((asset_id, observed, required_range))
    return report


def registry_version() -> str:
    """Schema version of the registry itself."""
    return _load().get("$registry_version", "unknown")


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    import argparse
    ap = argparse.ArgumentParser(description="Asset Version Registry")
    ap.add_argument("--check", help="Audit a specific consumer (humanizer/translator/authoring)")
    ap.add_argument("--list", action="store_true", help="List all assets + current versions")
    ap.add_argument("--asset", help="Show details for a single asset id")
    args = ap.parse_args()

    if args.list:
        print(f"Registry version: {registry_version()}\n")
        print(f"{'Asset':<20} {'Current':<10} {'Band':<12} {'Consumers'}")
        print("─" * 70)
        for aid in list_assets():
            ver = current_version(aid)
            band = compatibility_band(aid)
            consumers = ", ".join(_load()["assets"][aid].get("consumers", []))
            print(f"{aid:<20} {ver:<10} {band:<12} {consumers}")
        sys.exit(0)

    if args.asset:
        a = _load()["assets"].get(args.asset)
        if a is None:
            print(f"unknown asset: {args.asset}")
            sys.exit(1)
        print(json.dumps(a, ensure_ascii=False, indent=2))
        sys.exit(0)

    if args.check:
        r = check_consumer(args.check)
        print(f"Consumer: {r.consumer}")
        print(f"Checked {r.checked_assets} required assets")
        print(f"  ✓ {len(r.compatible_assets)} compatible: {r.compatible_assets}")
        if r.incompatible_assets:
            print(f"  ✗ {len(r.incompatible_assets)} INCOMPATIBLE:")
            for problem in r.problems:
                print(f"      {problem}")
        if r.missing_assets:
            print(f"  ? {len(r.missing_assets)} missing: {r.missing_assets}")
        sys.exit(1 if r.has_problems else 0)

    # default: list
    print(f"Registry version: {registry_version()}")
    print(f"Assets: {list_assets()}")
    print(f"Consumers with declared requirements: "
          f"{sorted(_load().get('consumer_declared_requirements', {}).keys())}")
    print(f"\nRun with --list, --check <consumer>, or --asset <id> for details.")

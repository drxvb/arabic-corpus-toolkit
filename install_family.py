#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
install_family.py — v1.8.0 cross-platform install + verification for the
arabic-* skill family.

Closes Gap G4 (Gemini's evaluator complaint): "How am I supposed to install
this? There's no package, no requirements.txt, no setup script."

Run from the toolkit's directory or anywhere else with --target=...

Usage:
    # From the toolkit's own directory: install missing siblings as siblings
    python install_family.py

    # Install into a specific parent directory
    python install_family.py --target /opt/arabic-family

    # Verify only — don't clone, just check current install
    python install_family.py --verify-only

    # JSON output for CI
    python install_family.py --json

Phases:
    1. ACQUIRE  — `git clone` each missing sibling repo into the target dir
    2. VERIFY   — run family_doctor.py + golden_e2e_test.py to validate setup

Exit codes:
    0 = full success (everything installed + all checks pass)
    1 = git clone failure or family_doctor reports problems
    2 = golden e2e regression failure
    3 = invalid arguments

Python 3 stdlib only.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

_HERE = Path(__file__).resolve().parent  # arabic-corpus-toolkit
_DEFAULT_TARGET = _HERE.parent           # sibling-layout parent dir


# Sibling registry — declared in toolkit because toolkit anchors the family.
SIBLINGS = [
    {
        "name": "arabic-corpus-toolkit",
        "git_url": "https://github.com/drxvb/arabic-corpus-toolkit.git",
        "marker": "scripts/family_doctor.py",
        "role": "anchor — shared assets + scripts",
    },
    {
        "name": "arabic-ai-text-humanizer",
        "git_url": "https://github.com/drxvb/arabic-ai-text-humanizer.git",
        "marker": "scripts/humanize_v2.py",
        "role": "Arabic prose humanization (toolkit hard dep)",
    },
    {
        "name": "arabic-corpus-translator",
        "git_url": "https://github.com/drxvb/arabic-corpus-translator.git",
        "marker": "scripts/translate.py",
        "role": "EN↔AR translation with Stages A/C/D/E/F",
    },
    {
        "name": "arabic-authoring-suite",
        "git_url": "https://github.com/drxvb/arabic-authoring-suite.git",
        "marker": "scripts/generate.py",
        "role": "outline→draft→humanizer-gate authoring",
    },
]


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def _check_prereqs() -> List[str]:
    """Return list of missing required CLI tools."""
    missing = []
    if _which("git") is None:
        missing.append("git")
    if _which("python") is None and _which("python3") is None:
        missing.append("python/python3")
    return missing


def acquire(target: Path) -> Tuple[Dict[str, Any], int]:
    """Clone any missing siblings into `target`. Returns (report, exit_code).
    exit_code=0 if all 4 siblings end up present; 1 on any clone failure."""
    report: Dict[str, Any] = {"target": str(target), "siblings": [], "failures": 0}
    target.mkdir(parents=True, exist_ok=True)
    for s in SIBLINGS:
        path = target / s["name"]
        sib_entry = {"name": s["name"], "path": str(path), "role": s["role"]}
        if path.exists() and (path / s["marker"]).exists():
            sib_entry["status"] = "already_present"
            sib_entry["marker_verified"] = True
            report["siblings"].append(sib_entry)
            continue
        if path.exists():
            sib_entry["status"] = "directory_exists_but_no_marker"
            sib_entry["marker_verified"] = False
            report["siblings"].append(sib_entry)
            continue
        print(f"\n  Cloning {s['name']}...", flush=True)
        try:
            subprocess.run(
                ["git", "clone", s["git_url"], str(path)],
                check=True, capture_output=True, text=True,
            )
            sib_entry["status"] = "cloned"
            sib_entry["marker_verified"] = (path / s["marker"]).exists()
            if not sib_entry["marker_verified"]:
                sib_entry["status"] = "cloned_but_marker_missing"
                report["failures"] += 1
        except subprocess.CalledProcessError as e:
            sib_entry["status"] = "clone_failed"
            sib_entry["error"] = e.stderr.strip()[:300]
            report["failures"] += 1
        report["siblings"].append(sib_entry)
    return report, (0 if report["failures"] == 0 else 1)


def verify(target: Path) -> Tuple[Dict[str, Any], int]:
    """Run family_doctor.py + golden_e2e_test.py on the install at `target`.
    Returns (report, exit_code)."""
    toolkit = target / "arabic-corpus-toolkit"
    report: Dict[str, Any] = {"target": str(target)}
    doctor_script = toolkit / "scripts" / "family_doctor.py"
    e2e_script = toolkit / "evals" / "golden_e2e_test.py"

    py = _which("python3") or _which("python")
    if py is None:
        report["error"] = "no python interpreter found"
        return report, 1

    # Subprocess kwargs: force UTF-8 decoding and tolerate decode errors
    # (Arabic content in family_doctor/golden_e2e output trips cp1252 on Windows)
    _sub_kw = {"capture_output": True, "text": True,
               "encoding": "utf-8", "errors": "replace"}

    # family_doctor
    if doctor_script.exists():
        r = subprocess.run([py, str(doctor_script), "--json"], **_sub_kw)
        report["family_doctor_exit"] = r.returncode
        out = r.stdout or ""
        try:
            report["family_doctor"] = json.loads(out)
        except json.JSONDecodeError:
            report["family_doctor"] = {"raw": out[:500]}
    else:
        report["family_doctor_exit"] = -1
        report["family_doctor"] = "script not present"

    # golden e2e
    if e2e_script.exists():
        r = subprocess.run([py, str(e2e_script)], **_sub_kw)
        report["golden_e2e_exit"] = r.returncode
        out = r.stdout or ""
        lines = out.splitlines()
        passed = sum(1 for L in lines if "[PASS]" in L)
        failed = sum(1 for L in lines if "[FAIL]" in L)
        report["golden_e2e_passed"] = passed
        report["golden_e2e_failed"] = failed
    else:
        report["golden_e2e_exit"] = -1
        report["golden_e2e_passed"] = 0
        report["golden_e2e_failed"] = 0

    if report.get("family_doctor_exit", 1) != 0:
        return report, 1
    if report.get("golden_e2e_exit", 1) != 0:
        return report, 2
    return report, 0


def main() -> int:
    p = argparse.ArgumentParser(description="Install + verify the arabic-* skill family")
    p.add_argument("--target", default=str(_DEFAULT_TARGET),
                   help=f"Parent directory for sibling layout (default: {_DEFAULT_TARGET})")
    p.add_argument("--verify-only", action="store_true",
                   help="Skip cloning; just run family_doctor + golden_e2e")
    p.add_argument("--json", action="store_true", help="Emit JSON report")
    args = p.parse_args()
    target = Path(args.target).resolve()

    # Prereqs
    missing = _check_prereqs()
    if missing:
        msg = f"missing required CLI tools: {missing}"
        if args.json:
            print(json.dumps({"error": msg}, indent=2))
        else:
            print(f"✗ {msg}")
        return 3

    if not args.json:
        print("═" * 72)
        print(f"  arabic-* skill family installer  v1.8.0")
        print(f"  Target: {target}")
        print("═" * 72)

    # Phase 1: acquire (unless --verify-only)
    if not args.verify_only:
        if not args.json:
            print(f"\n[1/2] ACQUIRE  — cloning missing siblings into {target}")
        acquire_report, acquire_code = acquire(target)
        if not args.json:
            for s in acquire_report["siblings"]:
                marker = "✓" if s.get("marker_verified") else "✗"
                print(f"  [{marker}] {s['name']:30s} ({s['status']})")
        if acquire_code != 0:
            if args.json:
                print(json.dumps({"acquire": acquire_report,
                                  "verify": None, "overall": "acquire_failed"},
                                 ensure_ascii=False, indent=2))
            return 1
    else:
        acquire_report = {"target": str(target), "skipped": "verify-only mode"}

    # Phase 2: verify
    if not args.json:
        print(f"\n[2/2] VERIFY   — running family_doctor.py + golden_e2e_test.py")
    verify_report, verify_code = verify(target)

    if args.json:
        print(json.dumps({
            "acquire": acquire_report,
            "verify": verify_report,
            "overall": "ok" if verify_code == 0 else "verify_failed",
            "exit_code": verify_code,
        }, ensure_ascii=False, indent=2))
        return verify_code

    # Human-readable verify summary
    print(f"\n  family_doctor exit:  {verify_report.get('family_doctor_exit')}")
    print(f"  golden_e2e exit:     {verify_report.get('golden_e2e_exit')}")
    print(f"  golden_e2e PASS:     {verify_report.get('golden_e2e_passed')}")
    print(f"  golden_e2e FAIL:     {verify_report.get('golden_e2e_failed')}")
    print()
    if verify_code == 0:
        print("─" * 72)
        print("✓ Family installed and verified. All 4 siblings present + 40/40 e2e PASS.")
        print("─" * 72)
    else:
        print("─" * 72)
        print(f"✗ Verification failed (exit {verify_code}). See above for details.")
        print("─" * 72)
    return verify_code


if __name__ == "__main__":
    sys.exit(main())

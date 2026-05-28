#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
register.py — register policy lookup.

Per the Codex-style API design (v0.2 multi-agent review): the register
policy lives next to the lookup logic, not in a JSON file. Reason:
the policy table is small, rarely changes, and adding a register
requires consumer code changes anyway — coupling them in one source
file is the right discipline.

Encodes the `classical / news / opinion / technical` × {transformation-gating}
matrix that v2.6.x of the humanizer has been using by convention. The toolkit
makes it queryable so future consumers (translator, authoring suite) don't
re-implement the matrix and drift.

Python 3 stdlib only.
"""
from __future__ import annotations

import sys
from typing import Dict, FrozenSet

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class UnknownRegisterError(ValueError):
    pass


# Single source of truth. Adding a register here is a deliberate choice
# that all consumers must explicitly handle.
_POLICIES: Dict[str, Dict[str, object]] = {
    "classical": {
        "register": "classical",
        "applies_calque_dictionary": False,
        "applies_connector_rebalance": True,
        "preserves_borrowings": True,
        "allows_passive_voice_relaxation": False,
        "tashkeel_reduction": False,
        "applies_rhetorical_figures": True,
        "description": "Traditional MSA; no English calques present, leave borrowings verbatim.",
    },
    "news": {
        "register": "news",
        "applies_calque_dictionary": True,
        "applies_connector_rebalance": True,
        "preserves_borrowings": False,
        "allows_passive_voice_relaxation": True,
        "tashkeel_reduction": True,
        "applies_rhetorical_figures": False,
        "description": "Modern editorial; full calque substitution; safe default.",
    },
    "opinion": {
        "register": "opinion",
        "applies_calque_dictionary": True,
        "applies_connector_rebalance": True,
        "preserves_borrowings": False,
        "allows_passive_voice_relaxation": True,
        "tashkeel_reduction": True,
        "applies_rhetorical_figures": False,
        "description": "Editorial opinion; full calque substitution; allows pronoun diversification.",
    },
    "technical": {
        "register": "technical",
        "applies_calque_dictionary": False,
        "applies_connector_rebalance": False,
        "preserves_borrowings": True,
        "allows_passive_voice_relaxation": False,
        "tashkeel_reduction": False,
        "applies_rhetorical_figures": False,
        "description": "Technical/spec prose; preserve borrowed terms; minimal transformation.",
    },
}


def policy_for(register: str) -> Dict[str, object]:
    """Return a defensive copy of the policy dict for `register`."""
    if register not in _POLICIES:
        raise UnknownRegisterError(
            f"unknown register: {register!r} (known: {sorted(_POLICIES)})"
        )
    return dict(_POLICIES[register])


def known_registers() -> FrozenSet[str]:
    return frozenset(_POLICIES)


def applies(transform: str, register: str) -> bool:
    """True if `transform` is enabled for `register`.
    Convention: transform names match the boolean keys without the
    `applies_` prefix (e.g., transform='calque_dictionary' checks
    'applies_calque_dictionary')."""
    policy = policy_for(register)
    key = f"applies_{transform}" if not transform.startswith("applies_") else transform
    return bool(policy.get(key, False))


def cli_main() -> int:
    import argparse, json
    p = argparse.ArgumentParser(description="Register policy lookup")
    p.add_argument("--register", help="Show policy for register (classical/news/opinion/technical)")
    p.add_argument("--list", action="store_true", help="List known registers")
    p.add_argument("--applies", nargs=2, metavar=("TRANSFORM", "REGISTER"),
                   help="Check if TRANSFORM applies in REGISTER")
    args = p.parse_args()

    if args.list:
        print("Known registers:")
        for r in sorted(known_registers()):
            policy = _POLICIES[r]
            print(f"  - {r}: {policy['description']}")
        return 0

    if args.applies:
        transform, register = args.applies
        try:
            result = applies(transform, register)
        except UnknownRegisterError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2
        print("yes" if result else "no")
        return 0

    if args.register:
        try:
            policy = policy_for(args.register)
        except UnknownRegisterError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2
        print(json.dumps(policy, ensure_ascii=False, indent=2))
        return 0

    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(cli_main())

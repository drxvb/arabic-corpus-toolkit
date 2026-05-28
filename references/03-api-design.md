# 03 — API Design Rationale (v0.3)

Compiled from the Codex-style API-design lens of the v0.2 multi-agent review. This file documents **why** the toolkit's API surface looks the way it does, so future maintainers don't re-litigate decisions that were already made deliberately.

## Three modules, three responsibilities

| Module | Owns | Cache | Errors raised |
|---|---|---|---|
| `dictionary.py` | Calque dictionary lookup (find_by_en, find_canonical, iter_entries, calque_index) | mtime-keyed dict, thread-safe | (none — empty results, not exceptions) |
| `corpus_stats.py` (planned v0.4) | Empirical-pattern queries (connector_distribution, ngram_frequency, token_total) | load-once | ValueError on unknown register key |
| `register.py` | Register policy lookup (policy_for, applies, known_registers) | static — no I/O | `UnknownRegisterError` |
| `validate.py` | Schema validation across all corpus/*.json | none | (none — SchemaReport encapsulates) |

**Design discipline**: each module does one thing. `dictionary.py` doesn't know about register policies; `register.py` doesn't read JSON. Consumers compose them.

## JSON stays — Aho-Corasick is the forward-compat door

The Codex-style review explicitly **pushed back on SQLite-FTS** for the dictionary at >2K entries (the conventional advice). Reasons:

1. **Review-ability of triage diffs.** A binary SQLite file kills `git diff` — but the v2.6.0 dictionary triage *worked* precisely because the 14 fixes were visible PR-diffable lines. The forensic value of `git blame` on individual entries outweighs any lookup-speed argument.
2. **Schema migration tooling.** SQLite needs Alembic-grade migrations on a stdlib-only project; JSON Schema does the same work with no extra tooling.
3. **The actual perf concern at 2K+ entries** isn't lookup — it's the longest-first regex sweep in the humanizer's hot path. That's solved by an **Aho-Corasick automaton** built once at load time (stdlib-only via a trie), not by SQLite.

So the v0.3 decision: JSON source-of-truth + in-memory index + a forward-compat door for a stdlib-built trie matcher (`dictionary.compiled_matcher() -> Matcher`) when regex sweep becomes the bottleneck. **One concession**: if `empirical-patterns.json` grows to multi-MB (per Kimi-style lens this is a realistic concern), *that* file is a candidate for SQLite as a **derived artifact**, not as the source of truth. Source stays human-readable.

## Per-asset SemVer over monolithic toolkit version

Per Kimi-style asset-promotion lens. The connector inventory won't change at the same rate as the calque dictionary. Coupling them under one monolithic SemVer means a dictionary tweak forces a connector-table version bump, forces a consumer re-test, discourages dictionary tweaks.

Concrete impl:

- Each JSON file in `corpus/` carries `$schema_version` (string, SemVer).
- A sibling `*.schema.json` file declares the JSON Schema for that asset.
- `validate.py` reads `$schema_version` and selects the appropriate validation rules.
- Consumers pin: `TOOLKIT_DICTIONARY_COMPAT = ">=1.0.0, <2.0.0"`.
- Breaking changes require an explicit `--allow-break` flag plus a CHANGELOG entry.

See `CHANGELOG.md` for the per-asset version table.

## Errors as data, not exceptions (mostly)

`dictionary.py` raises only for **I/O failures** (`DictionaryNotFoundError`) and **schema-shape failures** (`DictionarySchemaError`). It does NOT raise on:

- Missing entry for `find_canonical("term not in dict")` → returns `None`
- Empty dictionary → returns `([], {})`
- Entries with missing optional fields → silently filtered with defaults

This is deliberate: consumers (humanizer, translator, authoring suite) should treat "no rule applies" as a no-op, not as an exceptional condition. The exception is `register.py`'s `UnknownRegisterError` — that's a programmer error (typo in the register name), not a data issue, so loud fail is correct.

`validate.py` is the opposite: it never raises, it captures everything into the `SchemaReport` dataclass. The validator's job is to *describe* problems, not signal them by raising.

## TypedDict over dataclass over dict

For shapes that flow across module boundaries (CalqueEntry, RegisterPolicy), `TypedDict` is the right tool:

- Compatible with the existing JSON-derived dicts (no copy needed)
- Type-checked by mypy / pyright if the consumer cares
- Stdlib-only — no `dataclasses` import for the data shapes

`SchemaReport` is the exception — it's an output type with formatting methods (`to_dict`, `to_json`), so dataclass earns its weight. Internal caches use plain dicts (no public contract).

## Cache invalidation

Three cache strategies in play:

1. **`dictionary.py`**: mtime-keyed, thread-safe. Fresh read if file changed. Use case: maintainer edits the JSON in an editor mid-session, validator runs in another shell — the second call sees the fresh data.
2. **`corpus_stats.py`** (planned v0.4): load-once. The file is large (~MB-scale) and rarely changes during a process lifetime. Consumer calls `clear_cache()` explicitly if regenerating mid-process.
3. **`register.py`**: no cache, static config in code. Adding a register requires a code change, which restarts the consumer anyway.

## What's deferred to v0.4+

- `corpus_stats.py` — implemented per Codex-style spec; ships v0.4 after `empirical-patterns.json` schema is formalized.
- `scripts/lookup.py` — the merged unified-API surface Kimi-style recommended. v0.3 ships `dictionary.py` + `register.py` separately; v0.5 merges them under a single `lookup.py` re-export if consumer feedback shows that's better.
- `scripts/diff_schema.py` — Kimi-style recommended a CLI that diffs two schema versions and refuses MAJOR breaks without a flag. v0.5 candidate; v0.3 ships the validation half (`validate.py`) but not the diff-detection half.
- `scripts/export_consumer_view.py` — produces a flat snapshot pinned to a specific schema version. v0.6 once we have >1 consumer actually depending on the toolkit.

## Provenance

This design was synthesized from the v0.2 multi-agent review (Gemini-style + Kimi-style + Codex-style lenses running concurrently). See `references/04-multi-agent-synthesis.md` for the lens outputs in full and `M:\Main\AI\Corpus\humanizer-v2.6-multi-agent-synthesis.md` for the original method.

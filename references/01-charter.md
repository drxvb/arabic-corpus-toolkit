# 01 — Charter

## Mission

Be the **single source of truth** for shared Arabic linguistic assets across a family of three sibling skills. Hold the dictionary, the empirical-pattern statistics, the register policies, and the MSA style guide. Serve them read-only. Never transform text. Never call LLMs.

## Scope

**In scope:**

- `corpus/calque-dictionary.json` (migration target from humanizer v2.6.0)
- `corpus/empirical-patterns.json` (migration target from humanizer mining output)
- `references/02-register-policies.md` (extracted from humanizer's `13-inherited-lexical-tables.md`)
- `references/03-msa-style-guide.md` (synthesized from humanizer's references 14-16)
- `references/04-connector-tables.md` (extracted from humanizer's `16-fasl-wa-wasl.md`)
- A read-only Python API (`scripts/dictionary.py`, `scripts/corpus_stats.py`, `scripts/register.py`) for consumers

**Out of scope (explicitly):**

- Text transformation of any kind (humanization, translation, generation, scoring) — those live in consumer skills
- LLM calls — consumers may call LLMs; this skill never does
- Sacred-text guard module — currently in humanizer, will migrate here only when ≥2 skills consume it
- Write API for end users — toolkit modifications are maintainer-only and go through the toolkit's own versioned write path

## Anti-scope (what tempts but must be refused)

- **Becoming an Arabic NLP library.** This is data + lookup, not a tokenizer/POS-tagger/morphology engine. If a consumer needs morphological analysis, it owns that dependency.
- **Becoming the humanizer's `references/` directory.** The humanizer's references that aren't about *shared* assets (e.g., `references/01-cognitive-structure.md` is about the humanizer's 16-dim framework specifically) stay in the humanizer.
- **Drift between consumers' assumed schemas.** Schema is versioned; breaking changes bump the toolkit's major version; consumers pin against compatible ranges.

## Quality bar for migrated content

Migration from the humanizer is **not a copy operation** — it's an opportunity for a quality pass. Each migrated file must:

1. Be machine-readable (JSON / CSV) where it's data; markdown where it's narrative.
2. Carry provenance metadata (source skill, source version, native-review status if applicable).
3. Survive a lint pass enforcing schema-version + required-field presence.
4. Be re-readable by the original humanizer paths via a thin compatibility shim during the v0.2 transition (no big-bang migration).

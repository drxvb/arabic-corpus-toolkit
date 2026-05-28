---
name: arabic-corpus-toolkit
description: "Shared Arabic-language corpus infrastructure: calque dictionary, corpus statistics, register policies, style guide. Consumed by arabic-ai-text-humanizer (16-dim humanizer + 5-axis English path) and the upcoming arabic-corpus-translator (corpus-grounded EN↔AR translation) + arabic-authoring-suite. Centralizes the load-bearing assets so dictionary fixes propagate to all consumers in one place. NOT a standalone humanizer or translator — it's the data + reference layer those skills read from. Triggers on 'arabic corpus toolkit', 'shared arabic dictionary', 'arabic calque dictionary lookup', 'arabic linguistic resources', 'MSA register policy', 'arabic terminology base'. Do NOT use for direct text transformation (use arabic-ai-text-humanizer), for translation (use arabic-corpus-translator when released), or for content generation. Read-only reference + lookup layer."
---

# arabic-corpus-toolkit — Shared Arabic Linguistic Infrastructure

**Status:** v0.2 — assets migrated from `arabic-ai-text-humanizer` (340-entry calque dictionary + 71.28M-token empirical-patterns mining output). Read API (`scripts/dictionary.py`) ships with six functions: `load_dictionary`, `find_by_en`, `find_canonical`, `iter_entries`, `has_topic_guard`, `stats`. External-sources catalog (`references/02-external-sources.md`) compiled from the multi-agent Gemini-style grounding lens — 12 authoritative institutions for cross-referencing, three dictionary claims flagged as needing external verification, and the fiqh-adjacent sacred-text-adjacency gap that no LLM can solve. The Kimi-style asset-promotion lens and Codex-style API-design lens are still running and will inform v0.3.

## Why this skill exists

Per Agent C's architectural review (multi-agent synthesis in `M:\Main\AI\Corpus\humanizer-v2.6-multi-agent-synthesis.md`), the calque dictionary, corpus statistics, and register policies currently embedded inside `arabic-ai-text-humanizer` are about to be consumed by three sibling skills:

1. **`arabic-ai-text-humanizer`** (existing) — detects + transforms AR/EN AI-slop prose
2. **`arabic-corpus-translator`** (v0.1 scheduled v2.8.0 of the humanizer family) — EN↔AR corpus-grounded translation
3. **`arabic-authoring-suite`** (Q1 2027) — long-form AR/EN: books, articles, courses, news, with corpus-grounded outline discipline

If each sibling vendors its own copy of the calque dictionary, **a single bad entry takes 3× the work to fix** and the dictionaries WILL drift. This toolkit is the load-bearing shared module — one location, one set of fixes, all consumers benefit.

## What this skill owns

| Asset | Source (today) | Migration target (v0.2) |
|---|---|---|
| `calque-dictionary.json` | `arabic-ai-text-humanizer/corpus/calque-dictionary.json` (340 entries, v2.6.0 triaged) | `arabic-corpus-toolkit/corpus/calque-dictionary.json` |
| `empirical-patterns.json` | `arabic-ai-text-humanizer/corpus/empirical-patterns.json` (100K-record mining output) | `arabic-corpus-toolkit/corpus/empirical-patterns.json` |
| Register policies | `arabic-ai-text-humanizer/references/13-inherited-lexical-tables.md` | `arabic-corpus-toolkit/references/02-register-policies.md` |
| MSA style guide | scattered across `references/14-reader-respect.md`, `15-typography-hygiene.md`, `16-fasl-wa-wasl.md` | `arabic-corpus-toolkit/references/03-msa-style-guide.md` |
| Connector tables | `arabic-ai-text-humanizer/references/16-fasl-wa-wasl.md` | `arabic-corpus-toolkit/references/04-connector-tables.md` |

## What this skill does NOT own

- The 16-dimension humanizer analyzer (lives in arabic-ai-text-humanizer)
- The 5-axis English scorer (lives in arabic-ai-text-humanizer)
- Translation logic (will live in arabic-corpus-translator)
- Content generation (will live in arabic-authoring-suite)
- Sacred-text guard (lives in arabic-ai-text-humanizer/scripts/sacred_text_guard.py — moved here in a later version once two skills need it)

## Read-only API (intent for v0.2)

Three Python helper modules will expose the assets to consumers:

```python
# Consumers import like this:
from arabic_corpus_toolkit import dictionary, corpus_stats, register

entries = dictionary.find_by_en("personalization")     # 1+ entries with full schema
entry = dictionary.find_canonical("personalization")   # single best entry
stats = corpus_stats.connector_distribution("news")    # per-register stats
policy = register.policy_for("classical")              # which transformations gate on
```

Each helper is pure Python 3 stdlib — no SQLite, no FAISS, no LLM call. The intent is read-only lookup; modifications go through the toolkit's own write API (versioned, audited).

## Roadmap

| Version | Ships | Status |
|---|---|---|
| **v0.1** | Scaffold (this release): SKILL.md, README, LICENSE, directory structure, intent docs | ✅ Current |
| **v0.2** | Migrate `calque-dictionary.json` + `empirical-patterns.json`; `arabic-ai-text-humanizer` v2.7.0 reads from here | Pending humanizer v2.7.0 |
| **v0.3** | Migrate register policies + connector tables + MSA style guide | Pending humanizer v2.7.0 |
| **v0.4** | Add `arabic-corpus-translator` integration layer (the read API translator needs) | Pending translator scaffold |
| **v0.5** | Add `arabic-authoring-suite` integration layer (fact-pack schema, outline discipline) | Pending authoring scaffold |
| **v1.0** | All three consumers stable on toolkit ≥ v0.5; semantic versioning enforced for breaking changes | Q2 2027 |

## Constraints

- **No transformations.** The toolkit reads and serves data. Any transformation (humanize, translate, author) belongs in the consumer skill, not here.
- **No LLM calls.** Pure data + lookup. Consumers may call LLMs; this skill never does.
- **Schema is versioned.** Breaking schema changes bump the toolkit's major version, and consumers pin against a compatible range. v2.5.1 of the dictionary schema (post-v2.6.0 triage) is the first stable schema.
- **No vendoring.** The whole point is that consumers DON'T vendor a copy. They import or read by path.

## Provenance

The migrated assets retain their full multi-source provenance:
- Calque dictionary built from 8,850-article AITNews tech-news corpus + multi-LLM swarm (Claude + Codex) on 361 seed terms, validated against `Y:\Linguistics\News\Technology\AITNews`. Native-MSA review (v2.6.0) added `regional_sensitivity` / `political_sensitivity` / `disambiguation_pair_id` annotations.
- Empirical patterns mined from 100K records (1.31M sentences, 71.28M tokens, 4 register categories) of the source corpora.
- Sacred-text-guard heuristics derived from classical hadith citation conventions + Quranic typography (U+06D6–U+06ED).

## License

MIT. Inherits the humanizer's license; English-pattern-catalogue portions trace to `hardikpandya/stop-slop` (MIT). See LICENSE file once v0.2 ships with the migrated assets.

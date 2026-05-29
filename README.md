# arabic-corpus-toolkit

> Shared Arabic linguistic infrastructure: calque dictionary, corpus stats, register policies, MSA style guide. Consumed by `arabic-ai-text-humanizer`, the upcoming `arabic-corpus-translator`, and the future `arabic-authoring-suite`.

**Status:** **v1.12.1 — stable.** 13 assets (A/B/B'/C/D/E + F.technology/F.news + G.technology/G.news/G.business/G.legal/G.politics) plus four foundational contract scripts (G1 arabic_normalize / G2 asset_registry / G3 influence_telemetry / G4 install_family). All three consumer siblings live and pinned to per-asset SemVer: `arabic-ai-text-humanizer` v2.16.0, `arabic-corpus-translator` v1.8.0, `arabic-authoring-suite` v1.6.0. Inter-sibling contract conformance: 56/56 PASS. Golden e2e: 40/40 PASS.

## Why this exists

Three sibling skills are about to consume the same calque dictionary, empirical-pattern statistics, and register policies that currently live inside `arabic-ai-text-humanizer`. Letting each sibling vendor its own copy guarantees they will drift. This toolkit is the shared, versioned, read-only foundation.

Architecturally validated by the multi-agent review documented at `M:\Main\AI\Corpus\humanizer-v2.6-multi-agent-synthesis.md` (Agent C: scope critic — recommended this as the "load-bearing keystone" of the 4-sibling family).

## Family map

```
                              ┌──────────────────────────────────────────┐
                              │  arabic-corpus-toolkit  (v1.12.1)        │
                              │  · 13 assets (A/B/B'/C/D/E/F.*/G.*)      │
                              │  · 4 contracts (G1-G4: normalize,        │
                              │    registry, telemetry, install)         │
                              │  · 56-assert conformance gate            │
                              │  · 40-assert golden e2e gate             │
                              └────────────────────┬─────────────────────┘
                                                   │ read-only consumption
                  ┌────────────────────────────────┼────────────────────────────────┐
                  ▼                                ▼                                ▼
   ┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
   │ arabic-ai-text-      │    │ arabic-corpus-       │    │ arabic-authoring-    │
   │ humanizer  (v2.16.0) │    │ translator (v1.8.0)  │    │ suite     (v1.6.0)   │
   │                      │    │                      │    │                      │
   │ humanize prose       │    │ EN↔AR translation    │    │ books/articles/      │
   │ 16-dim Arabic +      │    │ 4-stage pipeline +   │    │ courses/news with    │
   │ 5-axis English       │    │ Stage E cross-vendor │    │ fact-pack discipline │
   │                      │    │ review               │    │                      │
   └──────────────────────┘    └──────────────────────┘    └──────────────────────┘
```

All four siblings hard-depend on toolkit ≥ v1.5.0 for the G1-G4 contracts. Per-asset SemVer means schema bumps within v1.x are additive; consumers query `asset_registry.is_compatible(asset_id, observed)` rather than hardcoding versions.

## Roadmap (current)

See `SKILL.md` Roadmap section and `CHANGELOG.md` for full per-release detail. Highlights:

| Phase | Ships | Status |
|---|---|---|
| v0.2 – v0.7.1 | Asset migration (A/B/B'/C/D/E) from humanizer | ✅ |
| v0.8 – v0.10 | Asset F mining + Asset G pairing + cross-LLM swarm validation | ✅ |
| v1.0 – v1.4.2 | Stable freeze; consumer family integrated; domain-keyed loaders | ✅ |
| **v1.5.0 – v1.8.0** | **Foundational contracts**: G1 arabic_normalize / G2 asset_registry / G3 influence_telemetry / G4 install_family | ✅ |
| **v1.9.0** | Domain expansion via single-pass classify+pair (G.business/G.legal/G.politics from Elaph) | ✅ |
| **v1.10.0 – v1.10.1** | 4-vendor consensus tier prune + inter-sibling conformance suite + SPA corpus ingestion | ✅ |
| **v1.11.0** | SPA-2024 mining: G.legal escapes placeholder (0→23 active), G.business 51→69, multi-corpus heritage | ✅ |
| **v1.12.0 + v1.12.1** | G.politics era-locked metadata + mined-pair acceptance criteria formalized | ✅ |
| v1.13+ | Either ingest new bilingual corpus for healthcare/science terminology, or wire usage telemetry when a real consumer asks, or run A6 audit cycle | Pending demand signal |

Items explicitly deferred per A5 panel verdict: usage telemetry dashboard (P2, requires infra), audit variance root cause (research for A6), Aho-Corasick consumer integration (YAGNI), 5th sibling extraction (premature). See `SKILL.md` Roadmap section for the full deferral rationale.

## License

MIT. See `LICENSE`. Migrated content retains upstream provenance (humanizer → stop-slop for the English portions; humanizer's own multi-LLM-swarm + AITNews mining for Arabic calque dictionary).

## Full charter

See `SKILL.md` for the full skill specification, including frontmatter triggers, scope boundaries, read-only API intent, and migration plan.

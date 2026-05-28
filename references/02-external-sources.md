# 02 — External Sources for Authoritative Grounding

The toolkit's data has provenance via the AITNews corpus, multi-LLM swarm, and the 71.28M-token mining run that produced `corpus/empirical-patterns.json`. **None of these are reliable substitutes for institutional authority on fine-grained Arabic linguistic decisions.** Agent A's v2.6.0 multi-agent review demonstrated this concretely — 10+ wrong dictionary entries shipped through three minors with green tests because LLM consensus systematically miscalled register-sensitive and politically-loaded entries.

This file catalogs the external authoritative sources the toolkit should cross-reference. **Compiled from the Gemini-style grounding lens of the v0.2 multi-agent review.** Each entry's accuracy is the user's responsibility to verify against the cited publisher — the toolkit treats these as candidate authorities, not as drop-in truth.

## Sources by asset class

| # | Source | Publisher / Backing | Strengthens |
|---|---|---|---|
| 1 | **UN Arabic Language Style Guide / دليل الترجمة العربية** | UN Department for General Assembly and Conference Management (DGACM); Arabic Translation Service, NY | Terminology (diplomatic / legal / technical); register (formal MSA); calque correction |
| 2 | **Al Jazeera Arabic Stylebook / الدليل الأسلوبي للجزيرة** (2013, updates ongoing) | Al Jazeera Media Institute, Doha | Register policies (news vs. opinion); punctuation; transliteration; sacred-text handling |
| 3 | **Mu'jam al-Wasīṭ / المعجم الوسيط** (4th ed., 2004) | Academy of the Arabic Language in Cairo (مجمع اللغة العربية بالقاهرة), est. 1932 | Canonical MSA lexis; morphological standards; root-pattern validation |
| 4 | **Mu'jam al-Lughah al-'Arabiyyah al-Mu'āṣirah / معجم اللغة العربية المعاصرة** | Ahmad Mukhtar Omar, 'Ālam al-Kutub, Cairo, 2008 ⚠️ *edition/year unverified* | Contemporary MSA terminology (post-1970 neologisms); attested-usage calque entries |
| 5 | **ALECSO Arabization Bureau / مكتب تنسيق التعريب** (Rabat, est. 1961) | Arab League Educational, Cultural and Scientific Organization | Scientific/technical Arabization; cross-academy consensus for loanword policy |
| 6 | **Academy of the Arabic Language in Damascus** (est. 1919) — *Majallat al-Majma'* journal | Government of Syria | Classical-derived neologisms; literary register; oldest continuously active source |
| 7 | **King Salman Global Academy for Arabic Language** (est. 2020) — kasla.org.sa | KSA, Riyadh | Modern policy-aligned terminology; KSAA-CAD and KSAA-RD reference datasets |
| 8 | **WHO EMRO Arabic Health Terminology** | WHO Regional Office for the Eastern Mediterranean, Cairo | Medical/scientific MSA; technical-register calque correction |
| 9 | **IPCC AR6 Arabic Glossary** | IPCC working-group translations, UN-coordinated ⚠️ *standalone glossary PDF availability unverified* | Climate/scientific terminology; cross-register validation |
| 10 | **Hans Wehr Dictionary of Modern Written Arabic** (4th ed., J. M. Cowan, Spoken Language Services, 1994) | Spoken Language Services / Otto Harrassowitz | Historical baseline; etymology; root validation |
| 11 | **Mushaf Madinah orthographic conventions** | King Fahd Complex for the Printing of the Holy Qur'an, Madinah — qurancomplex.gov.sa | Qur'anic citation; diacritization; basmala typography; honorific formulas (ﷺ, ﷻ) |
| 12 | **Unicode Arabic block documentation + W3C Arabic Layout Requirements** (W3C i18n WG Note, 2022) | Unicode Consortium; W3C Internationalization WG | Bidi, kashida, presentation forms; punctuation Unicode codepoints (U+060C, U+061B, U+061F) |

## Three current dictionary claims needing external verification

These are entries currently in `corpus/calque-dictionary.json` (migrated from the humanizer at v0.2) that depend on multi-LLM frequency consensus rather than institutional authority. They should be verified before being treated as ground truth.

1. **`personalization → الشخصنة`** (post-v2.6.0 corrected direction). The Wamda / Al Jazeera Net post-2015 attribution is plausible **but classically `الشخصنة` means "personal attack / ad hominem"** (the verb شخصن = "to make personal"). Verify against Mu'jam al-Wasīṭ and a frequency count in Al Jazeera Net archives. The safer tech-register calque may be **التخصيص** (when context disambiguates it from the Saudi "privatization" sense) or **التشخيص الفردي**.

2. **`platform → منصة`** vs. the older `أرضية`. Now near-universal in news, but ALECSO Arabization records favor `أرضية` historically. Verify against ALECSO bulletins and the King Salman Academy's terminology database. AITNews corpus likely confirms `منصة` at >95% frequency, but the policy choice deserves an institutional anchor, not just frequency.

3. **`content (digital) → محتوى` collective plural**. Multi-LLMs accept both `محتويات` and `مُحتَوى` as collective. Mu'jam al-Wasīṭ and Ahmad Mukhtar Omar's contemporary lexicon should be the authority on which plural is correct for digital-content contexts vs. physical-container contexts.

## The gap no LLM can solve

**Sacred-text and honorific adjacency rules.** The toolkit currently has no policy on:

- Required spacing between Qur'anic citations and surrounding secular prose
- Line-break prohibitions inside ayah / hadith chains
- Font-switching conventions (some publishers switch to a Qur'anic typeface)
- Honorific-formula placement: ﷺ (Sallallahu alayhi wa-sallam), ﷻ (jalla jalāluhu), رضي الله عنه, عليه السلام
- When transliteration of sacred names is permitted vs. forbidden

This is a **fiqh-adjacent typographic question**, not a linguistic-frequency question. Multi-LLM consensus is unreliable because training data conflates Sunni, Shia, and academic-Orientalist conventions.

**Recommended sourcing:**

1. King Fahd Complex for the Printing of the Holy Qur'an (Madinah) — orthographic baseline
2. Al Jazeera Stylebook §sacred-text — newsroom-secular adjacency rules
3. One peer-reviewed source — *Journal of Qur'anic Studies* (Edinburgh University Press) or al-Azhar's *Majallat al-Buḥūth al-Islāmiyyah* — for the scholarly convention

Commission a one-page policy memo from a native MSA editor with Azhari or equivalent training. **Do not synthesize this from LLM output.**

## Verification status

Sources marked ⚠️ have unverified edition / year / standalone-publication details and should be looked up before relying on them as ground truth. Sources without that mark are verified as existing institutions or publications; specific edition / volume should still be confirmed before citing.

## Provenance

This catalog was assembled by the Gemini-style grounding lens during the multi-agent review for v0.2 of `arabic-corpus-toolkit`. Two complementary lenses (Kimi-style asset promotion, Codex-style API design) ran concurrently; their findings will inform v0.3+ enhancements. See `M:\Main\AI\Corpus\humanizer-v2.6-multi-agent-synthesis.md` for the full method.

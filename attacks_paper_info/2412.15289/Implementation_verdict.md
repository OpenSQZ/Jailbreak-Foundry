## Audit Iteration 2 - 2025-12-26

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Missing instruction paraphrasing (`ins_paraphrase`) in ELP pipeline | ❌ | ⚠️ Partially Fixed | `_ins_paraphrase` has been added and is now called in `_generate_elp_attack` (`sata_gen.py:170–187, 266–279`), mirroring the reference repo’s stubbed `ins_paraphrase` that returns the instruction unchanged; this restores pipeline structure but still does not implement the paraphrasing semantics described in the paper. |
| Simplified multi-word/phrase MLM (missing per-mask ensembles) | ❌ | ⚠️ Partially Fixed | `_generate_mlm_attack` now loops over all `masked_words` and builds a separate wiki entry and MLM prompt per word (`sata_gen.py:207–263`), but due to the framework’s single-string return, only the first prompt is exposed; ensemble-style evaluation over all prompts remains outside the attack class. |
| Differences in multi-word ELP prompt wording and mapping | ⚠️ | ✅ Fixed | `_create_elp_prompt_multiple` now branches on `granularity` and matches `SWQAttackPrompt_mw` vs `SWQAttackPrompt_mp` almost verbatim, including `[MASK%d]` vs `[MASKi]` usage and the lowercasing of the first character for `mw` (`sata_gen.py:497–527`). |
| Commendatory word vocabulary source and sampling | ⚠️ | ⚠️ Partially Fixed | `_load_commendatory_words` attempts to load the curated JSON from the cloned SATA repo and flatten categories (`sata_gen.py:103–127`), but the relative path points under `src/attacks_paper_info/...` rather than the repo root, so in practice it always falls back to the embedded subset list; vocabulary therefore still deviates from the official JSON file. |
| Weaker wiki-entry fallback behavior | ⚠️ | ✅ Fixed | `_get_wiki_entry` now caches and returns the raw LLM response when parsing fails after 8 attempts (`sata_gen.py:529–577`), aligning with the reference repo’s `wiki_entry = response` fallback; Wikipedia-based retrieval is still omitted but the previous generic “safe sentence” fallback has been removed. |
| Model naming and configuration differences | ⚠️ | ⚠️ Partially Fixed | `attack_model`’s default has been updated to `"gpt-3.5-turbo-1106"` (`sata_gen.py:58–62`), matching the official repo; `wiki_model` and temperature defaults remain consistent, but advanced sampling knobs (`top_p`, `frequency_penalty`, `best_of`) are still not exposed or documented. |
| Lack of attack-level search/restart controls inside the attack class | ⚠️ (context-only) | ⚠️ Unchanged | As before, `SATAAttack.generate_attack` produces one prompt per call, and global retry/search hyperparameters like `num_retries` are expected to live in higher-level evaluation code; this remains a framework design choice rather than an attack-fidelity bug. |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Single-word masking (`sw`) prompt and parsing | ✅ | ✅ | `_get_mask_word_prompt` and `_mask_keywords` (`sata_gen.py:281–333, 334–355`) are unchanged and still match `GPTMaskWordPrompt` plus `generate_msk_wd_ins` in the SATA repo. |
| Multi-word/phrase masking prompts and parsing (`mw`/`mp`) | ✅ | ✅ | `_get_mask_words_prompt` and `_get_mask_phrases_prompt` (`sata_gen.py:378–402, 404–436`) still mirror `GPTMaskWordsPrompt`/`GPTMaskPhrasesPrompt` prompts and regex structures. |
| MLM paraphrasing and text-infilling prompt construction | ✅ | ✅ | `_paraphrase_to_wiki` and `_create_mlm_prompt` (`sata_gen.py:579–645`) are unchanged and remain aligned with `GPTParaToWikiPrompt` and `GPTTextInfillPrompt` in `base_prompt.py`. |

**NEW Issues Found This Iteration:**
- No fundamentally new algorithmic deviations were found beyond refinements of previously documented issues; remaining gaps are improved but still stem from the same components (ELP paraphrasing semantics, commendatory vocabulary source, multi-word MLM ensembles, and hyperparameter surface).

**Summary:**
- Fixed: 2 issues
- Partially Fixed: 4 issues
- Still Broken: 0 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2412.15289
- Attack: sata_gen (SATAAttack)
- Verdict: Not 100% Fidelity
- Coverage: 15/15 components (100%)
- Iteration: 2

## Executive Summary
The `SATAAttack` implementation in `sata_gen.py` continues to capture the core SATA paradigm from Dong et al. (ELP sequence-word-query and wiki-style MLM text infilling) and now more closely mirrors the official SATA repository. This iteration restores the explicit `ins_paraphrase` call in the ELP pipeline (matching the repo’s stubbed behavior), corrects the multi-word ELP prompt to align with `SWQAttackPrompt_mw/mp`, adds a curated-JSON loader for commendatory words (albeit with a path that currently misses the actual file), and upgrades MLM multi-word/phrase handling to generate per-mask prompts even though only the first is returned. Wiki-entry fallback is also strengthened to reuse raw LLM outputs instead of a generic sentence. Despite these improvements, several deviations remain—most notably the lack of true paraphrasing semantics before ELP masking (as described in the paper), the fact that MLM ensembles are not fully exposed within the attack interface, continued reliance on an embedded subset of commendatory words due to the path bug, and a narrower hyperparameter surface—so the implementation still falls short of 100% fidelity.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| SATA masking (§Method – keyword masking) | Single-word masking (`sw`) prompt and parsing | `src/jbfoundry/attacks/generated/sata_gen.py:281–333, 334–355` | ✅ | `_mask_keywords` with `granularity == "sw"` plus `_get_mask_word_prompt` matches the official `GPTMaskWordPrompt` text and regex parsing structure. |
| SATA masking (§Method – keyword masking) | Single-phrase masking (`sp`) prompt and parsing | `src/jbfoundry/attacks/generated/sata_gen.py:281–333, 356–376` | ✅ | `_mask_keywords` with `granularity == "sp"` and `_get_mask_phrase_prompt` closely mirror `GPTMaskPhrasePrompt` and its parse pattern. |
| SATA masking (§Method – keyword masking) | Multi-word masking (`mw`) prompt and parsing | `src/jbfoundry/attacks/generated/sata_gen.py:281–333, 378–402` | ✅ | Multi-word masking prompt and parsing follow `GPTMaskWordsPrompt` semantics, including “at most 2 words” and the same output format. |
| SATA masking (§Method – keyword masking) | Multi-phrase masking (`mp`) prompt and parsing | `src/jbfoundry/attacks/generated/sata_gen.py:281–333, 404–436` | ✅ | Multi-phrase masking prompt and parsing mirror `GPTMaskPhrasesPrompt` (multi-phrase `[MASKi]`) with equivalent regex extraction. |
| SATA masking (§Method – robustness) | LLM retry and regex-based parsing for masking | `src/jbfoundry/attacks/generated/sata_gen.py:281–333` | ✅ | The 5-attempt retry loop with regex parsing is equivalent to `generate_msk_wd_ins` in the reference repo (`SATA/src/attack_wiki.py:94–109`). |
| SATA ELP (§3.x ELP/Sequence-Word-Query) | Commendatory word list and random selection | `src/jbfoundry/attacks/generated/sata_gen.py:103–157, 170–205` | ⚠️ | Attempts to load the curated `comendatory_terms-manually.json` from the cloned SATA repo and then falls back to an embedded list; due to an incorrect relative path, the JSON is never actually used and behavior effectively reduces to a fixed in-code subset, unlike the full vocabulary in `random_choose` (`SATA/src/attack_wiki.py:22–32`). |
| SATA ELP (§3.x ELP/Sequence-Word-Query) | Sequence construction and masked-word positioning (single & multiple) | `src/jbfoundry/attacks/generated/sata_gen.py:438–488` | ✅ | `_merge_single` and `_merge_multiple` reimplement `SWQ_sequence` construction and position constraints identically to `merge_and_shuffle_with_order` and the single-word logic (`SATA/src/attack_wiki.py:161–180, 278–281`). |
| SATA ELP (§3.x ELP prompt design) | Single-word/phrase ELP attack prompt | `src/jbfoundry/attacks/generated/sata_gen.py:490–495` | ✅ | `_create_elp_prompt_single` matches `SWQAttackPrompt_sw/sp.get_prompt` (`SATA/src/base_prompt.py:313–330`) up to immaterial newline/spacing differences. |
| SATA ELP (§3.x ELP prompt design) | Multi-word/phrase ELP attack prompt | `src/jbfoundry/attacks/generated/sata_gen.py:497–527` | ✅ | `_create_elp_prompt_multiple` now splits `mw` vs `mp` and mirrors `SWQAttackPrompt_mw` and `SWQAttackPrompt_mp` (demo sequence, ordinal wording, `[MASK%d]` vs `[MASKi]`, and the lowercase tweak for `mw`) from `SATA/src/base_prompt.py:335–352`. |
| SATA MLM (§3.x MLM – wiki entry generation) | Wiki-style entry generation and caching | `src/jbfoundry/attacks/generated/sata_gen.py:529–577` | ⚠️ | Uses the same `GPTCreateWiki`-style prompt and 8-attempt retry loop as `create_wiki_entry` (`SATA/src/attack_wiki.py:112–137`), and now falls back to the raw LLM response when parsing fails; however, it does not perform the Wikipedia lookup path or persist the wiki cache to disk. |
| SATA MLM (§3.x MLM – paraphrasing) | Paraphrasing masked instruction into wiki-style text | `src/jbfoundry/attacks/generated/sata_gen.py:579–610` | ✅ | `_paraphrase_to_wiki` reproduces the `GPTParaToWikiPrompt` template and model configuration (attack model at temperature 0.9), aligning with `para_to_wiki` (`SATA/src/attack_wiki.py:140–147` and `SATA/src/base_prompt.py:422–446`). |
| SATA MLM (§3.x MLM – text infilling attack) | Text infilling prompt construction and truncation | `src/jbfoundry/attacks/generated/sata_gen.py:612–645` | ✅ | `_create_mlm_prompt` follows `GPTTextInfillPrompt.get_prompt` (`SATA/src/base_prompt.py:382–397`), including the 1–3 enumerated steps, “[MASK] and Infill” note, and word-count-based truncation with an equivalent token-budget heuristic. |
| SATA ELP/MLM pipeline (§Method – assistive task composition) | Instruction paraphrasing (`ins_paraphrase`) before masking in ELP pipeline | `src/jbfoundry/attacks/generated/sata_gen.py:170–205, 266–279` | ⚠️ | `_generate_elp_attack` now calls `_ins_paraphrase`, which structurally matches `ins_paraphrase` in the SATA repo (`SATA/src/attack_wiki.py:35–49`), but both implementations leave the instruction unchanged; this matches the gold repo but still falls short of the paper’s intended paraphrasing step. |
| SATA MLM ensembles (§3.x MLM – multi-word/phrase settings) | Per-mask wiki entries and text-infilling prompts for `mw`/`mp` | `src/jbfoundry/attacks/generated/sata_gen.py:207–263` | ⚠️ | For `granularity in {"mw", "mp"}`, `_generate_mlm_attack` now loops over each masked word and builds a separate wiki entry and MLM prompt (as in `wiki-text-infilling-mw/mp` in `attack_wiki.py:437–541`), but only the first constructed prompt is returned to the caller instead of exposing the full ensemble. |
| SATA parameters & models (§Experiments / Implementation details) | Model/parameter mapping (attack model, wiki model, temperature, num selections, method/granularity) | `src/jbfoundry/attacks/generated/sata_gen.py:27–72, 83–101, 103–157, 170–205, 207–264, 529–577, 579–610` | ⚠️ | Parameters are well-mapped (`attack_model`, `wiki_model`, `temperature`, `num_selections`, `method`, `granularity`) and the default attack model now matches `"gpt-3.5-turbo-1106"`, but some CLI-level controls from the original scripts (`ps` string settings, `top_p`, `frequency_penalty`, `best_of`, and `num_retries`) remain unexposed or consolidated. |

## Parameter Mapping
| Paper/Repo Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Attack model for masking/paraphrasing (`model_name` in `args`) | `attack_model` (`PARAMETERS["attack_model"]`) | str | `"gpt-3.5-turbo-1106"` | ✅ | Default now matches the reference repo’s `"gpt-3.5-turbo-1106"` (`SATA/utility/argsparse.py:58–65`); the fixed provider `"wenwen"` is a framework detail and does not affect model choice. |
| Wiki simulation model for wiki entry generation (`gpt-4o`) | `wiki_model` (`PARAMETERS["wiki_model"]`) | str | `"gpt-4o"` | ✅ | Matches the repo’s use of `"gpt-4o"` in `create_wiki_entry` (`SATA/src/attack_wiki.py:115`); the implementation also uses temperature 0.9 for wiki generation as in the repo. |
| Temperature for attack LLM (`temperature`) | `temperature` (`PARAMETERS["temperature"]`) | float | `0.3` | ✅ | Default matches `args.temperature` default (`SATA/utility/argsparse.py:73–77`) and is used for attack-side masking; wiki generation uses a fixed 0.9, consistent with the reference. |
| Number of commendatory words (`num_selections`) | `num_selections` (`PARAMETERS["num_selections"]`) | int | `10` | ✅ | Default aligns with `--num_selections` default 10 in `argsparse.py:56–57`; remaining mismatch is in the underlying vocabulary loader rather than this parameter. |
| Prompt setting (`ps` ∈ {`swq-mask-sw`, `swq-mask-sp`, `swq-mask-mw`, `swq-mask-mp`, `wiki-text-infilling-*`}) | `method` (`"elp"` / `"mlm"`) + `granularity` (`"sw"`, `"sp"`, `"mw"`, `"mp"`) | str | `method="elp"`, `granularity="sw"` | ⚠️ | The implementation factorizes `ps` into two parameters; behavior is equivalent for the supported settings, but users cannot specify the original string-valued `ps` (including naive baselines) directly. |
| Retry count for masked-word extraction (`<=5` attempts) | Implicit loop in `_mask_keywords` | int | 5 | ✅ | Exactly matches the retry behavior in `generate_msk_wd_ins` (`SATA/src/attack_wiki.py:94–107`). |
| Retry count for wiki entry generation (`<=8` attempts) | Implicit loop in `_get_wiki_entry` | int | 8 | ✅ | Mirrors the 8-attempt loop in `create_wiki_entry` (`SATA/src/attack_wiki.py:116–127`). |
| Wiki-entry dictionary cache (`wiki_dict.json`) | `self.wiki_cache` (in-memory dict) | dict | `{}` | ⚠️ | Caching granularity (per-masked-word key) matches, but entries are not persisted to disk as in `wiki_entry.json`, so reuse across runs is lost. |
| Instruction paraphrasing before ELP masking (`ins_paraphrase`) | `_ins_paraphrase` call in `_generate_elp_attack` | function/pipeline step | N/A | ⚠️ | The pipeline now matches the repo by calling a paraphrase helper, but both the repo and this implementation return the instruction unchanged; this conflicts with the paper’s stated paraphrasing step, so it is structurally but not semantically aligned. |
| Global retry / restart count for attacks (`num_retries`) | (not represented) | int | `1` | ⚠️ | `num_retries` remains a top-level experimental knob; the attack class still produces one prompt per call, consistent with the original `single_inference` structure but different from the monolithic script’s CLI surface. |

## Misalignments / Missing Items

1. **ELP instruction paraphrasing semantics not implemented (paper vs. repo)**
   - **Paper/Repo context**: The SATA paper and high-level descriptions specify an `ins_paraphrase` step before ELP masking to better align with the assistive-task framing, and the official repo exposes an `ins_paraphrase` function that is called before all `swq-mask-*` settings (`SATA/src/attack_wiki.py:35–49, 161–163, 205–207, 256–258, 304–306`).
   - **Expected behavior**: For ELP (`method="elp"`), the instruction should conceptually be paraphrased (where needed) before masking, so that the sequence-word-query operates on a lightly rephrased but semantically equivalent instruction.
   - **Observed behavior**: `_generate_elp_attack` now calls `_ins_paraphrase` (`sata_gen.py:170–187`), and `_ins_paraphrase` is deliberately implemented as a no-op to mirror the reference repo stub (`sata_gen.py:266–279`); as a result, the instruction text is never actually changed prior to masking, and the pipeline matches the repo but not the paper’s described behavior.
   - **Impact**: This retains alignment with the gold repository but still diverges from the conceptual algorithm in the paper, potentially understating the intended role of paraphrasing in avoiding safety triggers; it remains a mild but real semantic gap relative to the paper.

2. **Partially implemented multi-word/phrase MLM ensembles**
   - **Paper/Repo context**: For `wiki-text-infilling-mw` and `wiki-text-infilling-mp` settings, the reference implementation generates **separate** wiki entries and text-infilling prompts for each masked word/phrase and obtains multiple responses (`resp_list`) per instruction (`SATA/src/attack_wiki.py:437–488, 490–541`). These ensembles are then evaluated, and best responses can be selected.
   - **Expected behavior**: For `granularity in {"mw", "mp"}` and `method="mlm"`, the algorithm should create a distinct text-infilling prompt for each masked word/phrase (each with its own wiki entry and paraphrased instruction), and these prompts should be available for downstream ensemble-style evaluation.
   - **Observed behavior**: `_generate_mlm_attack` now builds separate wiki entries and MLM prompts for every masked word/phrase (`sata_gen.py:239–259`), closely following `wiki-text-infilling-mw/mp` in the repo, but due to the framework’s `str` return type it only returns `attack_prompts[0]` (`sata_gen.py:261–262`); the other prompts are neither returned nor surfaced via parameters.
   - **Impact**: Compared to the previous iteration, the internal logic now better matches the repo, but from the framework’s point of view the search space is still effectively restricted to a single MLM prompt per call; full ensemble power must be recovered by extending the API or performing multiple calls with different index selections.

3. **Commendatory vocabulary still diverges from JSON ground truth**
   - **Paper/Repo context**: The SATA repo derives commendatory words from `data/comendatory_terms-manually.json` and deduplicates them (`SATA/src/attack_wiki.py:22–32`), producing a relatively large curated vocabulary.
   - **Expected behavior**: Commendatory words used in ELP should be sampled from this full curated JSON vocabulary (or an equivalent asset) so that sequence-word-query prompts match the distribution used in the original experiments.
   - **Observed behavior**: `_load_commendatory_words` now tries to open `attacks_paper_info/2412.15289/SATA/data/comendatory_terms-manually.json` relative to `sata_gen.py` (`sata_gen.py:108–112`), but because the real file lives at the repo root, `os.path.exists(json_path)` is false and the function always falls back to a hard-coded subset list (`sata_gen.py:132–157`).
   - **Impact**: Compared to the previous audit, the intent to use the curated JSON is present, but in practice the behavior is unchanged: commendatory sequences are still drawn from a smaller, embedded vocabulary, which weakens strict reproducibility relative to the paper and repo.

4. **Wiki-entry retrieval still omits Wikipedia-based enrichment**
   - **Paper/Repo context**: On repeated parsing failure, `create_wiki_entry` in the repo uses `wikipediaapi` to fetch a real page and concatenates the summary and top sections if available, falling back to the raw LLM `response` otherwise (`SATA/src/attack_wiki.py:112–137`).
   - **Expected behavior**: Failure cases should still try to provide rich, topic-relevant context via Wikipedia where possible, so MLM text infilling operates over realistic background information.
   - **Observed behavior**: `_get_wiki_entry` now stores and returns the raw LLM response on failure (`sata_gen.py:573–577`), which fixes the previous generic-sentence fallback but does not attempt any Wikipedia lookup; all knowledge still comes from the LLM rather than external retrieval.
   - **Impact**: Single-call attack behavior is now closer to the repo and no longer pathologically weak on parse failures, but the lack of Wikipedia-backed enrichment means some edge cases may still lack the richer context used in the reference experiments.

5. **Model and hyperparameter surface remains narrower than in scripts**
   - **Paper/Repo context**: The repo’s CLI exposes `ps` prompt settings and additional hyperparameters such as `top_p`, `frequency_penalty`, `best_of`, and `num_retries` (`SATA/utility/argsparse.py:58–119`), whereas the core attack logic in `single_inference` only consumes a subset of these.
   - **Expected behavior**: Either the attack class or its documentation should make clear how these hyperparameters map into the framework, so users can reproduce experimental settings if desired.
   - **Observed behavior**: `SATAAttack` exposes a concise configuration surface (`attack_model`, `wiki_model`, `temperature`, `num_selections`, `method`, `granularity`) and now matches the default attack model name, but still does not surface `ps` string settings, `top_p`, `frequency_penalty`, `best_of`, or `num_retries` (`sata_gen.py:27–72, 83–101`).
   - **Impact**: The core algorithm is unaffected, but exact reproduction of specific experimental hyperparameter grids from the scripts still requires out-of-band configuration or framework-level extensions.

## Extra Behaviors Not in Paper
- **Embedded commendatory word list**: The attack ships with a hard-coded commendatory word list rather than loading from an external asset; this is an implementation convenience and not described in the paper.
- **In-memory wiki cache**: `self.wiki_cache` caches wiki entries within a single process/lifecycle instead of persisting them to JSON as in the reference repo. This is a performance optimization that does not change single-call logic.
- **Provider choice and abstraction (`LLMLiteLLM`)**: The use of `LLMLiteLLM.from_config(provider="wenwen", ...)` is an integration detail of this framework and not part of the paper; it is acceptable as long as models and sampling parameters remain consistent.

## Required Changes to Reach 100%

1. **Implement meaningful instruction paraphrasing for ELP (if targeting paper-level fidelity)**
   - **File/Location**: `src/jbfoundry/attacks/generated/sata_gen.py` (`_ins_paraphrase` and `_generate_elp_attack`, lines 170–205, 266–279).
   - **Change**: Replace the no-op `_ins_paraphrase` with a real paraphrasing helper that conditionally rewrites the instruction (e.g., via a lightweight LLM call and a `need_paraphrase` heuristic), while keeping the call site intact; this would go beyond the current stub in the official repo but would better satisfy the paper’s description.
   - **Justification**: Resolves the remaining discrepancy between the conceptual algorithm in the paper and both codebases, while preserving the ELP pipeline structure now shared with the repo.

2. **Expose or control MLM ensembles for multi-word/phrase settings**
   - **File/Location**: `src/jbfoundry/attacks/generated/sata_gen.py:_generate_mlm_attack` (lines 207–263).
   - **Change**: Add a mechanism to either (a) return all constructed MLM prompts (e.g., via a list-returning helper or a separate API) or (b) parameterize which masked word index is used when collapsing to a single prompt; document the intended strategy so it clearly approximates the ensemble behavior of `wiki-text-infilling-mw/mp`.
   - **Justification**: Ensures that the broader search over masked components described in the paper and implemented in the repo can be reproduced within this framework’s abstraction.

3. **Fix commendatory JSON path and prefer curated vocabulary**
   - **File/Location**: `src/jbfoundry/attacks/generated/sata_gen.py:_load_commendatory_words` (lines 103–157).
   - **Change**: Correct `json_path` so it points to the actual cloned SATA data directory (e.g., by resolving from the project root) and prefer the JSON-loaded vocabulary whenever present, using the embedded list only as a true fallback.
   - **Justification**: Brings the ELP commendatory-word distribution into alignment with the original experiments and removes the silent reliance on the subset fallback.

4. **Optionally integrate Wikipedia-backed wiki enrichment**
   - **File/Location**: `src/jbfoundry/attacks/generated/sata_gen.py:_get_wiki_entry` (lines 529–577).
   - **Change**: On repeated parse failure, attempt a lightweight Wikipedia lookup similar to `exact_match_search`/`concat_sections` in `attack_wiki.py`, falling back to the current raw-response behavior only if retrieval fails.
   - **Justification**: More closely reproduces the rich-context behavior of `create_wiki_entry`, especially for difficult or rare masked terms.

5. **Document or extend the hyperparameter surface**
   - **File/Location**: `src/jbfoundry/attacks/generated/sata_gen.py:27–72` (PARAMETERS definition).
   - **Change**: Either (a) explicitly document in parameter descriptions that advanced sampling options (`top_p`, `frequency_penalty`, `best_of`, `num_retries`) are handled elsewhere in the framework, or (b) add optional parameters that pass these through to `LLMLiteLLM.from_config` for closer parity with the scripts.
   - **Justification**: Clarifies remaining differences between the framework-integrated attack and the original CLI configuration, helping users understand how to match experimental setups.

## Final Verdict
Given the restored ELP pipeline structure, improved multi-word ELP prompts, stronger wiki-entry fallback, and closer model defaults, the `SATAAttack` implementation is now a tighter match to the official SATA repository while still adhering to this framework’s interfaces. However, gaps remain relative to the combined paper+repo specification: ELP paraphrasing is structurally present but semantically a no-op, MLM ensembles for multi-word/phrase settings are not fully exposed through the attack API, commendatory words still come from a subset list due to an incorrect JSON path, and some hyperparameter controls are consolidated or omitted. As a result, the implementation **still does not achieve 100% fidelity** to the SATA paper and its gold-standard repository, though the remaining deviations are narrower and more clearly localized than in the previous audit.


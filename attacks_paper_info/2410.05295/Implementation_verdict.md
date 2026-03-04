## Audit Iteration 3 - 2025-12-26

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Scoring based on jailbreak prompts instead of target responses | ✅ Fixed | ✅ Fixed | `_score_target_response` still scores the target LLM’s response using a scorer LLM and `_extract_score`, matching the paper/repo pattern (`autodanturbo_gen.py:447–485`). |
| Embeddings derived from prompt-hash instead of response embeddings from a model | ✅ Fixed | ✅ Fixed | `_get_embedding` continues to call `litellm.embedding` on the previous target response with the configured `embedding_model` / `embedding_provider`, mirroring `Retrieval.embed` (`autodanturbo_gen.py:721–755`; `framework/retrival.py:14–22`). |
| Retrieval selection misclassifying medium-score strategies as ineffective | ✅ Fixed | ✅ Fixed | `_retrieve_strategies` still returns `(valid, strategies)` with `valid=True` for both high- and medium-score strategies and `valid=False` only for low-score ones, and `generate_attack` branches accordingly (`autodanturbo_gen.py:581–719`; `framework/retrival.py:27–153`). |
| `epochs` default smaller than paper/repo (reduced search depth) | ✅ Fixed | ✅ Fixed | `PARAMETERS["epochs"].default` remains 150, aligned with `AutoDANTurbo.__init__` in the repo (`autodanturbo_gen.py:49–56`; `pipeline.py:6–19`). |
| Missing `warm_up_iterations` and `lifelong_iterations` search controls | ⚠️ Partially Fixed | ⚠️ Still Present | These dataset-level iteration controls are no longer parameters of `AutoDANTurboAttack`; instead, the docstring states that warm-up and lifelong passes are handled by external orchestration calling `generate_attack` over dataset splits (`autodanturbo_gen.py:30–43`, `PARAMETERS` block). |
| Missing explicit warm-up / lifelong / test stages mirroring pipeline execution flow | ⚠️ Partially Fixed | ⚠️ Partially Fixed | Per-request epoch flow and retrieval logic remain faithful, and the new `freeze_library` flag now supports a fixed-library “test-like” mode, but dataset-level warm-up/lifelong loops over `data['warm_up']` / `data['lifelong']` are still left to external evaluation (`autodanturbo_gen.py:209–306`; `pipeline.py:94–156, 158–280, 282–323`). |
| Scorer and summarizer wrappers differ slightly from repo (potential brittleness) | ⚠️ Still Present | ⚠️ Still Present | `_extract_score` and `_extract_strategy_json` still reimplement the wrapper pattern without the repo’s explicit retry loops, so robustness to malformed outputs may be lower (`autodanturbo_gen.py:773–800, 802–833`; `framework/scorer.py:33–45`; `framework/summarizer.py:56–64`). |
| `embedding_model` / `embedding_provider` and `retrieval_k` semantics | ✅ Fixed | ✅ Fixed | `embedding_model` / `embedding_provider` now directly drive `litellm.embedding` in `_get_embedding`, and `retrieval_k` still bounds retrieval as in the repo (`autodanturbo_gen.py:120–137, 721–755, 648–649`; `framework/retrival.py:27–46, 96–104`). |
| `max_tokens` vs `max_length` naming in attacker calls | ✅ Fixed (equivalent) | ✅ Fixed (equivalent) | Attacker generations still use `max_tokens=10000`, which is semantically equivalent to the repo’s `max_length=10000` (`autodanturbo_gen.py:141–147, 337–344, 392–396, 439–443`; `pipeline.py:105–107, 175–176, 285–287`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Warm-up jailbreak prompt generation (`_warm_up_attack`) | ✅ | ✅ | Prompt templates and tag-based extraction still match `Attacker.warm_up_attack`, up to interface differences (`autodanturbo_gen.py:308–347`; `framework/attacker.py:8–24`). |
| Strategy-guided attack generation (`_use_strategy` / `_find_new_strategy`) | ✅ | ✅ | System prompts, strategy formatting, and avoidance prompts remain aligned with the repo (`autodanturbo_gen.py:349–398, 400–445`; `framework/attacker.py:26–55, 57–82`). |
| Strategy library structure and updates | ✅ | ✅ | Library entries are still stored as `{"Strategy","Definition","Example","Score","Embeddings"}` lists and updated on improvements, consistent with `Library.add` usage (`autodanturbo_gen.py:487–580`; `framework/library.py:27–39`; `pipeline.py:63–66, 223–227, 282–285`). |

**NEW Issues Found This Iteration:**
- No new algorithmic deviations were identified; the new `freeze_library` parameter provides a reasonable fixed-library test mode, and the remaining gaps concern dataset-level stage controls and wrapper robustness as already documented.

**Summary:**
- Fixed: 0 issues
- Partially Fixed: 2 issues
- Still Broken: 0 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2410.05295
- Attack: autodanturbo_gen
- Verdict: Not 100% Fidelity
- Coverage: 12/12 components (100%)
- Iteration: 3

## Executive Summary
The current `AutoDANTurboAttack` implementation continues to closely match the core AutoDAN-Turbo algorithm as described in the paper (ArXiv: 2410.05295) and implemented in the official `AutoDAN-Turbo` repository, preserving the fixes from earlier audits for scoring, embeddings, retrieval, and strategy extraction. The main new change is the addition of a `freeze_library` parameter, which lets this class operate in a test-like, fixed-library mode analogous to `AutoDANTurbo.test`, while the unused embedding client has been removed in favor of a direct `litellm.embedding` call controlled by `embedding_model` / `embedding_provider`. However, dataset-level warm-up and lifelong iteration controls (`warm_up_iterations`, `lifelong_iterations`) and their staging over explicit warm-up/lifelong/test splits remain outside this attack class, and the scorer/summarizer wrappers still omit the repo’s retry loops, meaning the implementation cannot yet be considered fully faithful to the original experimental protocol. Per-request attack behavior is now high-fidelity, but end-to-end search-control fidelity across datasets is still delegated to external orchestration.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 (Overview) / Plan §2.1 | Warm-up attack generation: jailbreak prompt without strategy constraints | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:308–347`; repo `AutoDAN-Turbo/framework/attacker.py:8–24` | ✅ | System/user/assistant pattern and [START/END OF JAILBREAK PROMPT] tag usage match `Attacker.warm_up_attack`, modulo LLMLite vs custom model wrapper. |
| §3 / Plan §2.1 | Attack generation with effective strategies (`use_strategy`) | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:349–398`; repo `AutoDAN-Turbo/framework/attacker.py:26–55` | ✅ | Strategy text is injected into the system prompt with the same formatting and examples; behavior when multiple strategies are present is equivalent. |
| §3 / Plan §2.1 | Attack generation avoiding ineffective strategies (`find_new_strategy`) | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:400–445`; repo `AutoDAN-Turbo/framework/attacker.py:57–82` | ✅ | Implementation instructs the attacker to avoid listed strategies and otherwise explore freely, matching the paper/repo semantics. |
| §3 / Plan §3 Execution Flow | Refusal-detection safeguard on generated jailbreak prompts | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:265–269`; repo `AutoDAN-Turbo/pipeline.py:105–110, 175–179, 287–291` | ✅ | Same heuristic (checking for `"I cannot"`, `"I am unable"`, `"I can't"`) is used to fall back to the original request. |
| §3.1 / Plan §2.1–2.2 | Response scoring using a scorer LLM on target responses | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:447–485, 773–800`; repo `AutoDAN-Turbo/framework/scorer.py:9–31, 33–45`; `pipeline.py:106–126, 181–207, 293–316` | ✅ | The attack scores the target LLM’s response (not the prompt), using a scoring prompt and a separate extraction wrapper to obtain a numeric score, aligning with `Scorer.scoring` + `Scorer.wrapper`. |
| §3.2 / Plan §2.2 | Summarizer-based strategy extraction from (weak, strong) prompt pairs and strategy pool | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:487–580, 802–833`; repo `AutoDAN-Turbo/framework/summarizer.py:5–55, 56–64`; `pipeline.py:214–235` | ✅ | Weak/strong prompts and existing strategies are passed to a summarizer LLM, whose output is post-processed into `{"Strategy","Definition"}` JSON and stored with Example/Score/Embeddings in the library, as in the repo. |
| §3.2 / Plan §2.2 | Strategy library structure and updates (Strategy, Definition, Example, Score, Embeddings) | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:487–580`; repo `AutoDAN-Turbo/pipeline.py:63–66, 223–227, 282–285`; `framework/library.py:27–39` | ✅ | Library entries store strategy metadata and accumulate additional examples, scores, and embeddings per strategy exactly as in the official pipeline. |
| §3.3 / Plan §2.3 | Embedding computation for retrieval using response embeddings \(E_R\) | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:561–563, 610–616, 721–755`; repo `AutoDAN-Turbo/framework/retrival.py:5–22`; `pipeline.py:65, 225` | ✅ | Embeddings are computed by an external embedding model (via `litellm.embedding`) on previous target responses and stored in the library, matching `Retrieval.embed` behavior. |
| §3.3 / Plan §2.3 | FAISS-based retrieval and strategy selection logic (effective vs ineffective) | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:581–719`; repo `AutoDAN-Turbo/framework/retrival.py:27–153` | ✅ | Uses an L2 FAISS index, aggregates per-example scores, and applies the same three-way selection: high-score (≥5) single strategy, medium-score (2–<5) list up to `k`, else ineffective list with `valid=False`. |
| §3 / Plan §3 Execution Flow | Per-request iterative search with warm-up, retrieval, and `break_score` termination | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:209–306`; repo `AutoDAN-Turbo/pipeline.py:166–176, 170–176, 282–322` | ✅ | For a single request, the epoch loop reproduces the repo’s pattern: warm-up at epoch 0, retrieval-guided prompting thereafter, strategy extraction on score improvement, and early stopping when `score ≥ break_score`. |
| §3 / Plan §3 Execution Flow | Warm-up exploration phase over a dedicated warm-up dataset | Repo `AutoDAN-Turbo/pipeline.py:94–156` (dataset-level) | ⚠️ | This attack class does not implement dataset-level warm-up over `data['warm_up']`; instead, it starts from an empty `strategy_library` and performs per-request warm-up in the first epoch, leaving any full warm-up dataset pass to external orchestration. |
| §3 / Plan §3 Execution Flow | Lifelong learning phase over a lifelong dataset with persistent strategy library | Repo `AutoDAN-Turbo/pipeline.py:158–280` (dataset-level) | ⚠️ | The persistent in-memory `strategy_library` enables cross-request reuse within a single attack instance, but there is no explicit `lifelong_iterations` loop or dataset-split handling inside this class; that responsibility remains with the surrounding framework. |
| §3 / Plan §3 Execution Flow | Testing phase using a fixed strategy library for new requests | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:228–231, 285–293`; repo `AutoDAN-Turbo/pipeline.py:282–323` | ✅ | The `freeze_library` parameter disables strategy extraction and library updates while still using retrieval-guided attacks, enabling a fixed-library “test” mode analogous to `AutoDANTurbo.test` given an externally pre-built library. |

## Parameter Mapping
| Paper/Repo Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| `epochs` (max attack iterations per request) – `AutoDANTurbo.__init__ epochs=150` | `epochs` in `AutoDANTurboAttack.PARAMETERS` | int | 150 | ✅ | Default and semantics (max epochs for a single request with `break_score` early stopping) match the official pipeline. |
| `break_score` (termination threshold) – `AutoDANTurbo.__init__ break_score=8.5` | `break_score` in `PARAMETERS` | float | 8.5 | ✅ | Used as an early-stopping threshold when `score ≥ break_score`, aligned with the paper and repo. |
| `warm_up_iterations` (warm-up passes) – `AutoDANTurbo.__init__ warm_up_iterations=1` | Not exposed in `AutoDANTurboAttack` (external orchestration only) | int | N/A | ❌ | This search-control parameter exists in the repo’s dataset-level pipeline but is not configurable via this attack class; users must emulate it in higher-level evaluation code. |
| `lifelong_iterations` (lifelong passes) – `AutoDANTurbo.__init__ lifelong_iterations=4` | Not exposed in `AutoDANTurboAttack` (external orchestration only) | int | N/A | ❌ | Likewise, the number of lifelong passes is controlled only by external evaluation logic, not by this attack’s parameters. |
| Attacker model (attacker LLM) | `attacker_model` / `attacker_provider` | str | `"gpt-4o"` / `"wenwen"` | ✅ | Roles are correctly separated and configurable; exact model names need not match the repo as long as the attacker role is preserved. |
| Target model (attacked LLM) | `target_model` / `target_provider` | str | `"gpt-4o"` / `"wenwen"` | ✅ | Used exclusively for answering jailbreak prompts, as in the repo’s `target.respond`. |
| Scorer model (scoring LLM) | `scorer_model` / `scorer_provider` | str | `"gpt-4o"` / `"wenwen"` | ✅ | Applied to target responses via `_score_target_response` and `_extract_score`, implementing the same two-stage scoring pattern as `Scorer.scoring` + `Scorer.wrapper`. |
| Summarizer model (strategy extraction LLM) | `summarizer_model` / `summarizer_provider` | str | `"gpt-4o"` / `"wenwen"` | ✅ | Used only for analyzing prompt pairs and extracting strategy JSON, matching the repo’s summarizer role. |
| Embedding model for retrieval (`text_embedding_model` in `Retrieval`) | `embedding_model` / `embedding_provider` | str | `"text-embedding-3-small"` / `"wenwen"` | ✅ | These parameters now directly determine the `model` argument to `litellm.embedding` in `_get_embedding`, providing a configurable embedding backend analogous to `text_embedding_model.encode`. |
| `retrieval_k` (max strategies to retrieve) | `retrieval_k` in `PARAMETERS` and `_retrieve_strategies` | int | 5 | ✅ | Correctly limits the number of medium- or low-score strategies returned, matching the repo’s `k` behavior. |
| Attacker generation temperature | `temperature` in `PARAMETERS` | float | 1.0 | ✅ | Passed to attacker LLM in all three generation modes and matches the default used in the official pipeline. |
| Attacker output length (`max_tokens` / `max_length`) | `max_tokens` in `PARAMETERS` | int | 10000 | ✅ | Semantically equivalent to the repo’s `max_length=10000` for attacker generations; only the parameter name differs. |

## Misalignments / Missing Items
- **Dataset-level warm-up and lifelong iteration controls not exposed in this attack class**
  - **Paper/Repo**: `AutoDANTurbo.__init__` and `pipeline.py:94–156, 158–280` define `warm_up_iterations` and `lifelong_iterations` to control how many times the algorithm iterates over designated warm-up and lifelong datasets.
  - **Implementation**: `AutoDANTurboAttack` performs per-request iterative search with `epochs` and `break_score`, and its docstring notes that dataset-level iteration is delegated to external orchestration; there are no `warm_up_iterations` / `lifelong_iterations` parameters here.
  - **Impact**: Users cannot configure these dataset-level search controls through the attack interface alone; faithfully reproducing the paper’s full training schedule requires additional evaluation-side logic.

- **Scorer and summarizer wrappers still omit repo-style retry loops**
  - **Paper/Repo**: `pipeline.py` wraps both scoring and summarization with retry loops to handle transient LLM or parsing failures (`pipeline.py:112–126, 181–207, 214–235`).
  - **Implementation**: `_score_target_response`, `_extract_score`, `_extract_and_add_strategy`, and `_extract_strategy_json` assume single-call success, falling back to conservative defaults (e.g., score `1.0` or dropping a strategy) when parsing fails.
  - **Impact**: Under unreliable LLM behavior, this implementation may under-estimate scores or miss valid strategies more often than the repo, slightly weakening robustness even though core logic and prompts are aligned.

## Extra Behaviors Not in Paper
- **FAISS-absent fallback retrieval**
  - When `faiss` is unavailable, `_retrieve_strategies` falls back to random sampling from the strategy library, whereas the official repo assumes FAISS is present. This provides a graceful degradation path but is not described in the paper.
- **`freeze_library` parameter for in-place test mode**
  - The `freeze_library` flag (default `False`) allows users to reuse a fixed strategy library without further updates while still running the standard per-request loop, approximating the repo’s `test` phase from within the same attack method.

## Required Changes to Reach 100%
- **Expose or emulate dataset-level warm-up and lifelong iteration controls**
  - **Change**: Either (a) add attack-level parameters (or helper methods) that emulate `warm_up_iterations` and `lifelong_iterations` over appropriate request subsets, or (b) clearly document and provide companion evaluation utilities in this codebase that implement the paper’s dataset-level loops using these names.
  - **Justification**: §3 and the official `pipeline.py` treat these as core search controls across datasets; leaving them entirely to external code keeps this attack file from fully encoding the algorithm’s prescribed exploration schedule.

- **Optionally, add simple retry loops around scorer/summarizer wrappers**
  - **Change**: Wrap calls to `_score_target_response` / `_extract_score` and `_extract_and_add_strategy` / `_extract_strategy_json` in a small retry loop (1–2 retries) to better match the robustness of `pipeline.py`.
  - **Justification**: This would reduce sensitivity to occasional malformed LLM outputs without changing the algorithm’s core semantics.

## Final Verdict
The `AutoDANTurboAttack` now faithfully captures the per-request behavior of AutoDAN-Turbo—including warm-up, retrieval-guided prompting, response-based scoring, strategy extraction, and FAISS-based retrieval—and introduces a configurable fixed-library mode that mirrors the repo’s test phase. However, dataset-level search controls (`warm_up_iterations`, `lifelong_iterations`) and their associated warm-up/lifelong loops remain outside this attack class, and robustness differences in the scorer/summarizer wrappers persist. Consequently, while the implementation achieves full coverage of the paper’s core components at the per-request level, it is still **Not 100% Fidelity** with respect to the full algorithm and experimental protocol described in the paper and official repository.

## Audit Iteration 2 - 2025-12-26

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Scoring based on jailbreak prompts instead of target responses | ❌ | ✅ Fixed | `generate_attack` now queries the target LLM and `_score_target_response` scores the target's response, matching the paper/repo design (`autodanturbo_gen.py:275–280, 452–490, 778–805`). |
| Embeddings derived from prompt-hash instead of response embeddings from a model | ❌ | ✅ Fixed | `_get_embedding` now calls `litellm.embedding` using `embedding_model` / `embedding_provider` on the previous target response, aligning with `Retrieval.embed` in the official repo (`autodanturbo_gen.py:492–499, 566–568, 615–616, 726–760`; `framework/retrival.py:14–22`). |
| Retrieval selection misclassifying medium-score strategies as ineffective | ⚠️ | ✅ Fixed | `_retrieve_strategies` now mirrors `Retrieval.pop` by returning `(valid, strategies)` where `2 ≤ score < 5` yields `valid=True` and medium-score strategies are passed to `_use_strategy` (`autodanturbo_gen.py:586–724`; `framework/retrival.py:27–153`). |
| `epochs` default smaller than paper/repo (reduced search depth) | ❌ | ✅ Fixed | `PARAMETERS["epochs"].default` is now 150, matching `AutoDANTurbo.__init__` in the official pipeline (`autodanturbo_gen.py:44–51`; `AutoDAN-Turbo/pipeline.py:6–19`). |
| Missing `warm_up_iterations` and `lifelong_iterations` search controls | ❌ | ⚠️ Partially Fixed | Parameters are now defined with correct defaults but are not used anywhere in this codebase; dataset-level stage controls are still not wired into this framework (`autodanturbo_gen.py:59–72` and repository-wide grep). |
| Missing explicit warm-up / lifelong / test stages mirroring pipeline execution flow | ⚠️ / ❌ | ⚠️ Partially Fixed | Per-request epoch loop now faithfully mirrors the repo’s inner warm-up/retrieval logic, but dataset-level warm-up, lifelong, and test stages (over separate splits) remain absent from this attack class and are left to external evaluation logic (`autodanturbo_gen.py:215–311`; `AutoDAN-Turbo/pipeline.py:94–156, 158–280, 282–323`). |
| Scorer and summarizer wrappers differ slightly from repo (potential brittleness) | ⚠️ | ⚠️ Still Present | `_extract_score` and `_extract_strategy_json` still reimplement the wrapper pattern using LLMLite messages; semantics are close to `Scorer.wrapper` / `Summarizer.wrapper` but without the repo’s retry loops (`autodanturbo_gen.py:778–805, 807–838`; `framework/scorer.py:33–45`; `framework/summarizer.py:56–64`). |
| `embedding_model` / `embedding_provider` and `retrieval_k` semantics | ❌ / ⚠️ | ✅ Fixed | Embedding parameters now drive `_get_embedding`, and `retrieval_k` correctly bounds both FAISS-based and fallback retrievals (`autodanturbo_gen.py:101–114, 129–135, 586–613, 652–663, 721–722`). |
| `max_tokens` vs `max_length` naming in attacker calls | ⚠️ | ✅ Fixed (equivalent) | No code change, but upon re-evaluation the behavior is equivalent: `max_tokens=10000` is passed directly to LLMLite’s generation, matching the repo’s `max_length=10000` usage (`autodanturbo_gen.py:157–163, 342–349, 394–401, 441–448`; `AutoDAN-Turbo/pipeline.py:105–107, 175–176, 285–287`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Warm-up jailbreak prompt generation (`_warm_up_attack`) | ✅ | ✅ | Prompt template and tag-based extraction still closely mirror `Attacker.warm_up_attack`, with only API-specific differences (`autodanturbo_gen.py:313–353`; `framework/attacker.py:8–24`). |
| Strategy-guided attack generation (`_use_strategy` / `_find_new_strategy`) | ✅ | ✅ | System prompts and strategy formatting remain aligned with the official repo (`autodanturbo_gen.py:354–450`; `framework/attacker.py:26–55, 57–82`). |
| Strategy library structure and updates | ✅ | ✅ | Library entries still store `Strategy`, `Definition`, `Example`, `Score`, and `Embeddings` lists in the same way as the repo’s `Library` usage (`autodanturbo_gen.py:510–582`; `AutoDAN-Turbo/pipeline.py:63–66, 223–227, 282–285`). |

**NEW Issues Found This Iteration:**
- No new algorithmic deviations were identified beyond the partially addressed stage-level search controls; all other discrepancies from the prior audit were either fixed or remain as documented above.

**Summary:**
- Fixed: 6 issues
- Partially Fixed: 2 issues
- Still Broken: 0 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2410.05295
- Attack: autodanturbo_gen
- Verdict: Not 100% Fidelity
- Coverage: 11/12 components (92%)
- Iteration: 2

## Executive Summary
The updated `AutoDANTurboAttack` in `autodanturbo_gen.py` now closely matches the core AutoDAN-Turbo algorithm as described in the paper (ArXiv: 2410.05295) and implemented in the official `AutoDAN-Turbo` repository. Major deviations from the first audit—prompt-based scoring, hash-based “embeddings,” and incorrect retrieval semantics—have been corrected so that scoring is based on target responses, embeddings come from a configurable embedding model applied to responses, and retrieval follows the FAISS-based selection logic from the repo. The remaining gaps are primarily around dataset-level search controls and execution staging: `warm_up_iterations` and `lifelong_iterations` are defined but unused, and this attack class does not internally implement the warm-up / lifelong / test phases over dataset splits that the original pipeline uses. Because these stage-level controls and the test-only phase are not yet plumbed into this framework, the implementation cannot be considered fully faithful, but its per-request attack behavior is now very close to the source algorithm.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 (Overview) / Plan §2.1 | Warm-up attack generation: jailbreak prompt without strategy constraints | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:313–353`; repo `attacks_paper_info/2410.05295/AutoDAN-Turbo/framework/attacker.py:8–24` | ✅ | System/user/assistant pattern and [START/END OF JAILBREAK PROMPT] tag usage match the official `Attacker.warm_up_attack`, modulo LLMLite vs custom model wrapper. |
| §3 / Plan §2.1 | Attack generation with effective strategies (`use_strategy`) | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:354–404`; repo `AutoDAN-Turbo/framework/attacker.py:26–55` | ✅ | Strategy text is injected into the system prompt with the same formatting and examples; behavior when multiple strategies are present is equivalent. |
| §3 / Plan §2.1 | Attack generation avoiding ineffective strategies (`find_new_strategy`) | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:405–450`; repo `AutoDAN-Turbo/framework/attacker.py:57–82` | ✅ | Implementation instructs the attacker to avoid listed strategies and otherwise explore freely, matching the paper/repo semantics. |
| §3 / Plan §3 Execution Flow | Refusal-detection safeguard on generated jailbreak prompts | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:247–274`; repo `AutoDAN-Turbo/pipeline.py:105–110, 175–179, 287–291` | ✅ | Same heuristic (checking for `"I cannot"`, `"I am unable"`, `"I can't"`) is used to fall back to the original request; extra `"Sorry"` token from the previous iteration has been removed. |
| §3.1 / Plan §2.1–2.2 | Response scoring using a scorer LLM on target responses | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:275–280, 452–490, 778–805`; repo `AutoDAN-Turbo/framework/scorer.py:9–31, 33–45`; `pipeline.py:106–126, 181–207, 293–316` | ✅ | The attack now scores the target LLM’s response (not the prompt), using a nearly identical scoring prompt and a separate extraction wrapper to obtain a numeric score. |
| §3.2 / Plan §2.2 | Summarizer-based strategy extraction from (weak, strong) prompt pairs and strategy pool | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:492–585, 807–838`; repo `AutoDAN-Turbo/framework/summarizer.py:5–55, 56–64`; `pipeline.py:214–235` | ✅ | Weak/strong prompts and existing strategies are passed to a summarizer LLM, whose output is post-processed into `{"Strategy", "Definition"}` JSON and stored with Example/Score/Embeddings in the library, as in the repo. |
| §3.2 / Plan §2.2 | Strategy library structure and updates (Strategy, Definition, Example, Score, Embeddings) | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:510–582`; repo `AutoDAN-Turbo/pipeline.py:63–66, 223–227, 282–285` | ✅ | Library entries store strategy metadata and accumulate additional examples, scores, and embeddings per strategy exactly as in the official pipeline. |
| §3.3 / Plan §2.3 | Embedding computation for retrieval using response embeddings \(E_R\) | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:492–499, 566–568, 615–616, 726–760`; repo `AutoDAN-Turbo/framework/retrival.py:5–22`; `pipeline.py:65, 225` | ✅ | Embeddings are now computed by an external embedding model (via `litellm.embedding`) on previous target responses, and stored in the library, matching the repo’s `Retrieval.embed` behavior. |
| §3.3 / Plan §2.3 | FAISS-based retrieval and strategy selection logic (effective vs ineffective) | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:586–724`; repo `AutoDAN-Turbo/framework/retrival.py:27–153` | ✅ | Uses an L2 FAISS index, aggregates per-example scores, and applies the same three-way selection: high-score (≥5) single strategy, medium-score (2–<5) list up to `k`, else ineffective list with `valid=False`. |
| §3 / Plan §3 Execution Flow | Per-request iterative search with warm-up, retrieval, and `break_score` termination | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:215–311`; repo `AutoDAN-Turbo/pipeline.py:166–176, 170–176, 282–322` | ✅ | For a single request, the epoch loop reproduces the repo’s pattern: warm-up at epoch 0, retrieval-guided prompting thereafter, strategy extraction on score improvement, and early stopping when `score ≥ break_score`. |
| §3 / Plan §3 Execution Flow | Warm-up exploration phase over a dedicated warm-up dataset | Repo `AutoDAN-Turbo/pipeline.py:94–156` | ⚠️ | This attack class does not implement dataset-level warm-up over `data['warm_up']`; instead, it starts from an empty `strategy_library` and performs per-request warm-up in the first epoch, leaving any full warm-up dataset pass to external orchestration. |
| §3 / Plan §3 Execution Flow | Lifelong learning phase over a lifelong dataset with persistent strategy library | Repo `AutoDAN-Turbo/pipeline.py:158–280` | ⚠️ | The persistent in-memory `strategy_library` enables cross-request reuse within a single attack instance, but there is no explicit `lifelong_iterations` loop or dataset-split handling inside this class; that responsibility must be handled by the surrounding framework. |
| §3 / Plan §3 Execution Flow | Testing phase using a fixed strategy library for new requests | Repo `AutoDAN-Turbo/pipeline.py:282–323` | ❌ | No explicit test-only phase is implemented; there is no method analogous to `AutoDANTurbo.test`, and the attack class provides only the unified `generate_attack` loop. |

## Parameter Mapping
| Paper/Repo Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| `epochs` (max attack iterations per request) – `AutoDANTurbo.__init__ epochs=150` | `epochs` in `AutoDANTurboAttack.PARAMETERS` | int | 150 | ✅ | Default and semantics (max epochs for a single request with `break_score` early stopping) now match the official pipeline. |
| `break_score` (termination threshold) – `AutoDANTurbo.__init__ break_score=8.5` | `break_score` in `PARAMETERS` | float | 8.5 | ✅ | Used as an early-stopping threshold when `score ≥ break_score`, aligned with the paper and repo. |
| `warm_up_iterations` (warm-up passes) – `AutoDANTurbo.__init__ warm_up_iterations=1` | `warm_up_iterations` in `PARAMETERS` | int | 1 | ❌ | Parameter exists with the correct default but is unused anywhere in this repository; users cannot control warm-up passes via this value. |
| `lifelong_iterations` (lifelong passes) – `AutoDANTurbo.__init__ lifelong_iterations=4` | `lifelong_iterations` in `PARAMETERS` | int | 4 | ❌ | Similarly defined but unused; the class does not expose or honor this iteration count for lifelong red-teaming. |
| Attacker model (attacker LLM) | `attacker_model` / `attacker_provider` | str | `"gpt-4o"` / `"wenwen"` | ✅ | Roles are correctly separated and configurable; exact model names need not match the repo as long as the attacker role is preserved. |
| Target model (attacked LLM) | `target_model` / `target_provider` | str | `"gpt-4o"` / `"wenwen"` | ✅ | Used exclusively for answering jailbreak prompts, as in the repo’s `target.respond`. |
| Scorer model (scoring LLM) | `scorer_model` / `scorer_provider` | str | `"gpt-4o"` / `"wenwen"` | ✅ | Now applied to target responses via `_score_target_response` and `_extract_score`, implementing the same two-stage scoring pattern as `Scorer.scoring` + `Scorer.wrapper`. |
| Summarizer model (strategy extraction LLM) | `summarizer_model` / `summarizer_provider` | str | `"gpt-4o"` / `"wenwen"` | ✅ | Used only for analyzing prompt pairs and extracting strategy JSON, matching the repo’s summarizer role. |
| Embedding model for retrieval (`text_embedding_model` in `Retrieval`) | `embedding_model` / `embedding_provider` and `embedding_llm` | str | `"text-embedding-3-small"` / `"wenwen"` | ❌ | Although the parameters and an `embedding_llm` client are defined, `_get_embedding` calls `litellm.embedding` directly instead of using `embedding_llm`, and the dimensionality is implicitly tied to the external service; behavior is close but not fully plumbed through the configured client. |
| `retrieval_k` (max strategies to retrieve) | `retrieval_k` in `PARAMETERS` and `_retrieve_strategies` | int | 5 | ✅ | Correctly limits the number of medium- or low-score strategies returned, matching the repo’s `k` behavior. |
| Attacker generation temperature | `temperature` in `PARAMETERS` | float | 1.0 | ✅ | Passed to attacker LLM in all three generation modes and matches the default used in the official pipeline. |
| Attacker output length (`max_tokens` / `max_length`) | `max_tokens` in `PARAMETERS` | int | 10000 | ✅ | Semantically equivalent to the repo’s `max_length=10000` for attacker generations; only the parameter name differs. |

## Misalignments / Missing Items
- **Dataset-level warm-up and lifelong iteration controls are not wired into this framework**
  - **Paper/Repo**: `AutoDANTurbo.__init__` and `pipeline.py:94–156, 158–280` define `warm_up_iterations` and `lifelong_iterations` to control how many times the algorithm iterates over the warm-up and lifelong datasets, significantly affecting strategy discovery.
  - **Implementation**: While `warm_up_iterations` and `lifelong_iterations` now appear in `PARAMETERS` with the correct defaults, they are not used anywhere in the codebase; all per-request search is driven solely by `epochs` and `break_score`.
  - **Impact**: Users cannot reproduce the paper’s multi-pass warm-up/lifelong schedule within this framework without writing additional orchestration; search depth across datasets is effectively fixed by external code rather than these hyperparameters.

- **Missing explicit test-only phase using a fixed strategy library**
  - **Paper/Repo**: `AutoDANTurbo.test` (`pipeline.py:282–323`) defines a test phase where a frozen strategy library is applied to new requests using retrieval-guided attacks without further strategy extraction.
  - **Implementation**: `AutoDANTurboAttack` exposes only a single `generate_attack` method that always runs the full warm-up/retrieval/extraction loop; there is no attack-level abstraction for a pure test phase.
  - **Impact**: While evaluation code can approximate testing by freezing the library and ignoring new strategies, the lack of a dedicated test method means the framework cannot mirror the paper’s testing protocol exactly from this attack class alone.

- **Embedding client plumbing is slightly inconsistent**
  - **Paper/Repo**: `Retrieval` wraps a generic `text_embedding_model` with an `.encode` interface to obtain embeddings.
  - **Implementation**: An `embedding_llm` is constructed but not used; instead, `_get_embedding` calls `litellm.embedding` directly.
  - **Impact**: Behavior is very similar in practice, but the unused `embedding_llm` is a minor plumbing inconsistency that could confuse users or future maintainers.

- **Scorer and summarizer wrappers omit retry loops**
  - **Paper/Repo**: `pipeline.py` uses retry loops around both scoring and summarization wrappers to handle transient LLM failures.
  - **Implementation**: `_score_target_response`, `_extract_score`, and `_extract_strategy_json` assume single-call success; on parse failures, scores default to 1.0 or strategies are dropped without retries.
  - **Impact**: Under unreliable LLM behavior, the implementation may under-estimate scores or miss valid strategies more often than the repo, slightly weakening robustness even though the core logic is aligned.

## Extra Behaviors Not in Paper
- **FAISS-absent fallback retrieval**
  - When `faiss` is unavailable, `_retrieve_strategies` falls back to random sampling from the strategy library, whereas the official repo assumes FAISS is present. This provides a graceful degradation path but is not described in the paper.
- **Unused `embedding_llm` attribute**
  - An `embedding_llm` client is constructed in `__init__` but never used; embeddings instead rely on `litellm.embedding` directly, which is functionally similar but leaves dead configuration.

## Required Changes to Reach 100%
- **Wire dataset-level warm-up and lifelong iteration controls into the framework**
  - **Change**: Either (a) remove `warm_up_iterations` and `lifelong_iterations` from `PARAMETERS` and clearly document that dataset-level iteration is handled externally, or (b) add orchestration code (in this file or a closely related module) that uses these parameters to mirror the repo’s warm-up and lifelong loops over explicit data splits.
  - **Justification**: §3 and the official `pipeline.py` treat these as core search controls across datasets; leaving them unused breaks fidelity for experiments that depend on multi-pass exploration.

- **Expose a test-only pathway that uses a fixed strategy library**
  - **Change**: Add a method (e.g., `generate_attack_test`) that takes a pre-built `strategy_library`, uses `_retrieve_strategies` and `_use_strategy` / `_find_new_strategy` without calling `_extract_and_add_strategy`, and stops according to `epochs` / `break_score`, analogous to `AutoDANTurbo.test`.
  - **Justification**: This would allow the framework to reproduce the paper’s testing behavior using a fixed library without conflating test-time attacks with further lifelong learning.

- **Clean up embedding client usage**
  - **Change**: Either remove `embedding_llm` from `__init__` and rely solely on `litellm.embedding`, or refactor `_get_embedding` to call `self.embedding_llm` (or a small wrapper) so that all embedding behavior flows through the configured client.
  - **Justification**: Aligns with the repo’s `Retrieval` abstraction and avoids confusion from unused configuration.

- **Optionally, add simple retry loops around scorer/summarizer wrappers**
  - **Change**: Wrap calls to `_score_target_response` / `_extract_score` and `_extract_and_add_strategy` / `_extract_strategy_json` in a small retry loop (1–2 retries) to better match the robustness of `pipeline.py`.
  - **Justification**: This would reduce sensitivity to occasional malformed LLM outputs without changing the algorithm’s core semantics.

## Final Verdict
The revised `AutoDANTurboAttack` fixes all major algorithmic discrepancies identified in the first audit for per-request behavior—scoring, embeddings, retrieval, and strategy extraction now match the AutoDAN-Turbo paper and official repository very closely. However, dataset-level search controls (`warm_up_iterations`, `lifelong_iterations`) remain unused, and there is no explicit test-only phase corresponding to `AutoDANTurbo.test`, leaving some aspects of the original experimental protocol unimplemented in this framework. As a result, while the core attack logic is now high-fidelity, the implementation is still **Not 100% Fidelity** overall.

# Implementation Fidelity Verdict
- Paper ID: 2410.05295
- Attack: autodanturbo_gen
- Verdict: Not 100% Fidelity
- Coverage: 8/12 components (67%)
- Iteration: 1

## Executive Summary
The `AutoDANTurboAttack` implementation in `autodanturbo_gen.py` captures the high-level structure of AutoDAN-Turbo—warm-up attack generation, strategy-guided prompting, strategy extraction, and retrieval-based re-use—but diverges from both the paper blueprint and the official AutoDAN-Turbo repository in several core algorithmic details. Most notably, it scores jailbreak quality based on the jailbreak prompt alone rather than the target model's response, uses prompt-based, hash-derived embeddings instead of response embeddings from an embedding model, and modifies the retrieval selection logic so that "medium-quality" strategies are treated as ineffective rather than usable. The implementation also collapses the original warm-up / lifelong / test stages into a single per-request loop without exposing some of the search-control parameters described in the paper repository. These deviations materially change how strategies are discovered, stored, and reused, so the implementation cannot be considered 100% faithful to the source algorithm.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 (Overview) / Plan §2.1 | Attack generation: warm-up jailbreak prompt without strategy constraints | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:278–318`; reference implementation `attacks_paper_info/2410.05295/AutoDAN-Turbo/framework/attacker.py:8–24` | ✅ | System/user/assistant prompt pattern closely matches the repo; conditional warm-up generation is preserved. |
| §3 / Plan §2.1 | Attack generation with effective strategies (use_strategy) | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:319–368`; repo `AutoDAN-Turbo/framework/attacker.py:26–55` | ✅ | Strategy formatting, insertion into the system message, and conditional generation logic are aligned with the official implementation. |
| §3 / Plan §2.1 | Attack generation avoiding ineffective strategies (find_new_strategy) | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:370–415`; repo `AutoDAN-Turbo/framework/attacker.py:57–82` | ✅ | Matches the paper/repo description of prompting the attacker to avoid listed ineffective strategies while otherwise being unconstrained. |
| §3 / Plan §3 Execution Flow | Refusal-detection safeguard on generated jailbreak prompts | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:237–241`; repo warm-up/lifelong/test loops `AutoDAN-Turbo/pipeline.py:105–110, 175–179, 287–291` | ✅ | Same basic heuristic (string containment) is used to replace obviously refusing prompts with the original request; implementation adds an extra token ("Sorry") but behavior is consistent. |
| §3.1 / Plan §2.1–2.2 | Response scoring using a scorer LLM on target responses | Intended in repo `AutoDAN-Turbo/framework/scorer.py:9–31` and `pipeline.py:106–126, 181–207, 293–316`; implemented as prompt scoring in `autodanturbo_gen.py:417–456` | ❌ | In the repo/paper, scoring is based on the target LLM's response to the jailbreak prompt; here, `_score_jailbreak_prompt` only scores the jailbreak prompt text itself, not the target's response, changing the signal driving strategy selection. |
| §3.2 / Plan §2.2 | Summarizer-based strategy extraction from (weak, strong) prompt pairs and strategy pool | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:458–551, 753–784`; repo `AutoDAN-Turbo/framework/summarizer.py:5–64`; `pipeline.py:214–235` | ⚠️ | High-level behavior (compare weak/strong prompts, use existing strategy pool, ask summarizer to output Strategy/Definition JSON, then log Strategy/Score/Embeddings/Example) matches; wrapper prompting/JSON extraction differs and uses a slightly different prompt+priming scheme. |
| §3.2 / Plan §2.2 | Strategy library structure and updates (Strategy, Definition, Example, Score, Embeddings) | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:476–548`; repo `AutoDAN-Turbo/pipeline.py:63–66, 223–227`; `framework/library.py` (implied) | ✅ | Library entries use the same fields (Strategy, Definition, Example list, Score list, Embeddings list) and accumulate additional examples/scores/embeddings per strategy. |
| §3.3 / Plan §2.3 | Embedding computation for retrieval using response embeddings ER | Repo `AutoDAN-Turbo/framework/retrival.py:6–26`; `pipeline.py:65, 225`; paper plan §2.3 uses response embedding; implementation `_get_embedding` at `autodanturbo_gen.py:675–706` | ❌ | Official implementation embeds target responses via a dedicated text embedding model; here, `_get_embedding` uses a deterministic SHA-256–based hash of the previous prompt, not the response, and ignores the configured embedding model. |
| §3.3 / Plan §2.3 | FAISS-based retrieval and strategy selection logic (effective vs. ineffective) | `src/jbfoundry/attacks/generated/autodanturbo_gen.py:552–673`; repo `AutoDAN-Turbo/framework/retrival.py:27–153` | ⚠️ | Uses similar FAISS L2 index and per-example Score aggregation, but changes behavior: mid-range strategies (2 ≤ Score < 5) are later treated as ineffective (via `_score` check in `generate_attack`) rather than as valid strategies as in the repo (`valid=True` → `use_strategy`). |
| §3 / Plan §3 Execution Flow | Warm-up exploration loop over a warm-up dataset with `warm_up_iterations` and per-request `epochs` | Repo `AutoDAN-Turbo/pipeline.py:94–156`; corresponding control in `AutoDANTurbo.__init__` at `pipeline.py:6–21` | ⚠️ | `generate_attack` (`autodanturbo_gen.py:180–276`) retains an inner epoch loop with a `break_score` stopping rule but collapses the dedicated warm-up phase and its `warm_up_iterations` hyperparameter into a single per-request loop. |
| §3 / Plan §3 Execution Flow | Lifelong learning loop over a separate lifelong dataset with `lifelong_iterations` | Repo `AutoDAN-Turbo/pipeline.py:158–280` | ⚠️ | The attack class maintains a persistent `strategy_library` across calls (allowing cross-request reuse), but there is no explicit lifelong stage, no `lifelong_iterations` control, and no dataset-level orchestration mirroring the repo's `lifelong_redteaming` procedure. |
| §3 / Plan §3 Execution Flow | Testing phase using a fixed strategy library for new requests | Repo `AutoDAN-Turbo/pipeline.py:282–323` | ❌ | No analogous test-only phase exists in `autodanturbo_gen.py`; the same iterative loop is used for all calls, and evaluation/testing is left entirely to the surrounding framework. |

## Parameter Mapping
| Paper/Repo Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| `epochs` (max attack iterations per request) – `AutoDANTurbo.__init__` `epochs=150` | `epochs` in `AutoDANTurboAttack.PARAMETERS` (`autodanturbo_gen.py:44–51`) | int | 10 | ❌ | Behaviorally similar but default value is much smaller (10 vs 150), affecting search depth. |
| `break_score` (termination threshold) – `AutoDANTurbo.__init__` `break_score=8.5` | `break_score` in `PARAMETERS` (`autodanturbo_gen.py:52–58`) | float | 8.5 | ✅ | Default and semantics (stop when score ≥ break_score) match repo and paper. |
| `warm_up_iterations` (warm-up passes) – `AutoDANTurbo.__init__` `warm_up_iterations=1` | Not exposed in `AutoDANTurboAttack` | int | N/A | ❌ | Attack implementation has no explicit warm-up stage parameter; warm-up is folded into the single per-request loop. |
| `lifelong_iterations` (lifelong passes) – `AutoDANTurbo.__init__` `lifelong_iterations=4` | Not exposed in `AutoDANTurboAttack` | int | N/A | ❌ | No direct equivalent; lifelong behavior is implicit via persistent `strategy_library` but lacks configurable iterations. |
| Attacker model (paper/README specify attacker LLM; repo passes a model object into `Attacker`) | `attacker_model` / `attacker_provider` (`autodanturbo_gen.py:59–72, 141–147`) | str | `"gpt-4o"` / `"wenwen"` | ✅ | Roles are correctly separated (attacker vs scorer vs summarizer vs embedding); exact model names are configurable and need not match repo. |
| Scorer model (scoring LLM) | `scorer_model` / `scorer_provider` (`autodanturbo_gen.py:73–86, 149–154`) | str | `"gpt-4o"` / `"wenwen"` | ⚠️ | Role mapping is correct, but scoring is applied to jailbreak prompts rather than target responses, changing semantics. |
| Summarizer model (strategy extraction LLM) | `summarizer_model` / `summarizer_provider` (`autodanturbo_gen.py:87–100, 156–161`) | str | `"gpt-4o"` / `"wenwen"` | ✅ | Used exclusively for strategy summarization, consistent with repo and paper. |
| Embedding model for retrieval (`text_embedding_model` in `Retrieval`) | `embedding_model` / `embedding_provider` in `PARAMETERS` and `embedding_llm` in `__init__` (`autodanturbo_gen.py:101–114, 163–168`) | str | `"text-embedding-3-small"` / `"wenwen"` | ❌ | Parameters are defined and an LLM client is constructed, but `_get_embedding` ignores this model and instead uses a hash-based pseudo-embedding. |
| `retrieval_k` (max strategies to retrieve) | `retrieval_k` in `PARAMETERS` and used in `_retrieve_strategies` (`autodanturbo_gen.py:115–121, 567–571, 611–612, 620–663`) | int | 5 | ⚠️ | The parameter is correctly exposed and used to cap retrieved strategies, but the downstream logic misclassifies mid-range strategies as ineffective. |
| Generation temperature for attacker | `temperature` in `PARAMETERS` and used in `_warm_up_attack`, `_use_strategy`, `_find_new_strategy` (`autodanturbo_gen.py:122–128, 307–313, 359–365, 406–412`) | float | 1.0 | ✅ | Matches the intended role; exact default matches repo's attacker temperature. |
| `max_tokens` / `max_length` for attacker outputs | `max_tokens` in `PARAMETERS` and used in attacker calls (`autodanturbo_gen.py:129–135, 307–314, 359–365, 406–413`) | int | 10000 | ⚠️ | Semantically similar to repo's `max_length=10000`; naming difference only, but tied to LLMLiteLLM API rather than original wrapper. |

## Misalignments / Missing Items
- **Scoring signal uses jailbreak prompts instead of target responses**
  - **Paper/Repo**: §3.1 and `framework/scorer.py:9–31`, `pipeline.py:106–126, 181–207, 293–316` define scoring over the **target LLM's response** to the jailbreak prompt, using a scorer LLM and a subsequent wrapper to extract a numeric danger score.
  - **Implementation**: `_score_jailbreak_prompt` in `autodanturbo_gen.py:417–456` constructs a scoring prompt about the **jailbreak prompt itself**, never calling the target model, and `_extract_score` (`autodanturbo_gen.py:724–751`) parses that output.
  - **Impact**: This changes the optimization objective from "how harmful is the actual model response" to "how dangerous does the jailbreak prompt look", which can lead to very different strategy rankings and library contents; any behavior depending on real target responses is not faithfully reproduced.

- **Embeddings based on prompts and hash heuristics, not response embeddings from a model**
  - **Paper/Plan**: §2.3 and the plan specify retrieval over response embeddings \(E_R\); repo `framework/retrival.py:6–26` uses a `text_embedding_model.encode(text)` call on responses (e.g., `target_response_i`, `prev_target_response`).
  - **Implementation**: `_get_embedding` (`autodanturbo_gen.py:675–706`) uses a SHA-256 hash of the previous prompt text, maps bytes into a fixed 1536-dim vector, and normalizes it; response content and the configured `embedding_model` are ignored.
  - **Impact**: Strategy similarity is computed in an artificial hash space unrelated to semantic similarity of responses; retrieval behavior can diverge drastically from the paper/repo's embedding-based retrieval, and the `embedding_model` parameter is effectively non-functional.

- **Retrieval selection misclassifies medium-score strategies as ineffective**
  - **Repo behavior**: In `framework/retrival.py:130–153`, strategies with `Score ≥ 5` yield a single "most effective" strategy; strategies with `2 ≤ Score < 5` are treated as **valid** (returned with `valid=True`), leading the pipeline to call `use_strategy` (`pipeline.py:190–195`).
  - **Implementation behavior**: `_retrieve_strategies` (`autodanturbo_gen.py:552–673`) returns a list of strategies with an internal `_score`, and `generate_attack` (`autodanturbo_gen.py:220–233, 223–232`) sets `has_effective = any(s.get("_score", 0) >= 5)`; medium-score strategies (2–<5) therefore fall into the "ineffective" branch and trigger `_find_new_strategy` rather than `_use_strategy`.
  - **Impact**: The algorithm's exploration–exploitation balance changes: strategies that the original algorithm would directly exploit are instead treated as failures to avoid, altering the distribution of prompts and strategy updates.

- **Warm-up, lifelong, and test phases collapsed and partially parameterized**
  - **Repo**: `AutoDANTurbo.__init__` and `pipeline.py:94–156, 158–280, 282–323` implement distinct **warm-up**, **lifelong**, and **test** stages with `warm_up_iterations`, `lifelong_iterations`, and `epochs` controlling search depth per stage, plus explicit datasets (`data['warm_up']`, `data['lifelong']`).
  - **Implementation**: `generate_attack` (`autodanturbo_gen.py:180–276`) runs a single per-request loop over `epochs` with `break_score`, mixing warm-up (epoch 0) and lifelong-style retrieval (later epochs) and omitting any test-only loop; `warm_up_iterations` and `lifelong_iterations` are not exposed.
  - **Impact**: While a single long loop per request may be acceptable in this framework, it does not expose or mirror the paper/repo's staged search controls and testing procedure; users cannot reproduce the same exploration schedule or separate warm-up from lifelong and test phases.

- **Scorer and summarizer wrappers differ from repo, potentially affecting robustness**
  - **Repo**: `Scorer.wrapper` (`framework/scorer.py:33–45`) and `Summarizer.wrapper` (`framework/summarizer.py:56–64`) use a dedicated model/wrapper pattern with clear separation of "analysis" vs "extraction" calls.
  - **Implementation**: `_extract_score` and `_extract_strategy_json` (`autodanturbo_gen.py:724–784`) re-implement these using different message layouts (e.g., an assistant-prefixed partial JSON literal and manual string prefixing).
  - **Impact**: Semantics are broadly similar, but extraction may be more brittle; if the scorer/summarizer deviate from the narrow expected outputs, parsing failures could silently degrade scores or strategy updates compared with the repo.

## Extra Behaviors Not in Paper
- **Additional refusal token and fallback behavior**
  - `refusal_list` in `AutoDANTurboAttack.__init__` (`autodanturbo_gen.py:177–179`) includes `"Sorry"` in addition to `"I cannot"`, `"I am unable"`, and `"I can't"`, slightly broadening the cases where generated prompts are replaced by the original request.
- **FAISS-absent fallback retrieval**
  - When `faiss` is unavailable, `_retrieve_strategies` falls back to random sampling from the strategy library (`autodanturbo_gen.py:565–570`), which is not described in the paper/repo but serves as a graceful degradation mechanism.
- **Hash-based embedding dimension hard-coded to 1536**
  - `_get_embedding` uses a fixed 1536-dimensional vector regardless of the actual embedding model, aligning with OpenAI embeddings but not with the more general "any model with `.encode()`" design in the repo.

## Required Changes to Reach 100%
- **Align scoring with target responses rather than prompts**
  - **Change**: Modify `generate_attack` (`autodanturbo_gen.py:242–246`) and `_score_jailbreak_prompt` (`autodanturbo_gen.py:417–456`) so that, instead of scoring the jailbreak prompt alone, they (a) query the target LLM with the jailbreak prompt to obtain a response and (b) pass both the malicious request and the target response into a scorer LLM, mirroring `framework/scorer.py:9–31` and `pipeline.py:106–126, 181–207, 293–316`. The scorer wrapper should then extract the numeric score from that assessment. |
- **Use real embedding model on responses and honor `embedding_model`**
  - **Change**: Replace `_get_embedding` (`autodanturbo_gen.py:675–706`) with a call that uses the configured `embedding_llm` (or a dedicated embedding client) on the **target response text**, not the prompt, so that embeddings approximate semantic similarity as in `framework/retrival.py:6–26` and `pipeline.py:65, 225`. |
- **Restore retrieval semantics for medium-score strategies**
  - **Change**: Adjust `_retrieve_strategies` and its caller in `generate_attack` (`autodanturbo_gen.py:220–233, 552–673`) so that strategies with `2 ≤ score < 5` are treated as "valid" and passed into `_use_strategy`, while truly low-score strategies are reserved for `_find_new_strategy`, matching `framework/retrival.py:130–153` and `pipeline.py:188–197`. This likely requires returning a `(valid, strategies)` pair from `_retrieve_strategies` instead of using a single list and `_score` threshold. |
- **Expose and/or emulate paper-level search controls**
  - **Change**: Add optional parameters or internal logic to emulate `warm_up_iterations` and `lifelong_iterations` (e.g., by looping over `generate_attack` stages or by structuring the epochs into warm-up vs retrieval phases) and, if feasible, provide a test-only mode that uses a fixed strategy library with retrieval only, following `pipeline.py:94–156, 158–280, 282–323`. |
- **Optionally, bring scorer/summarizer wrappers closer to repo design**
  - **Change**: Simplify `_extract_score` and `_extract_strategy_json` to more directly match `framework/scorer.py:33–45` and `framework/summarizer.py:56–64`, ensuring they output bare numbers/JSON dictionaries and reducing parsing fragility. |

## Final Verdict
Given the differences in scoring signal (prompt vs target response), embedding source and model usage, retrieval selection logic, and the omission of explicit warm-up/lifelong/test stage controls, the current `AutoDANTurboAttack` implementation is **Not 100% Fidelity** with respect to the AutoDAN-Turbo paper and its official repository, though it preserves the broad modular structure and intent of the algorithm.


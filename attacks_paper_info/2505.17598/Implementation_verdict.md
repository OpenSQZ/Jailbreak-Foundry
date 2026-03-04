# Audit Iteration 3 - 2025-12-31

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Missing beam controls `num_beams` and `diversity_penalty` in PARAMETERS | ❌ | ✅ Fixed | Added AttackParameters and beam path guarded by `use_beam_search` (`src/jbfoundry/attacks/generated/arr_attack_gen.py:32-109,233-244`). |
| `max_new_tokens` applied as `max_length`, reducing generation budget | ⚠️ | ✅ Fixed | Generation now uses `max_new_tokens` with separate input truncation (`arr_attack_gen.py:211-254`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Lazy-load T5 paraphraser and MPNet similarity models | ✅ | ✅ Still correct | `_load_models` unchanged lazy init and device move (`arr_attack_gen.py:123-144`). |
| Sampling with `do_sample=True`, `top_p=0.9`, `temperature=0.8` | ✅ | ✅ Still correct | Default generation path retains sampling parameters (`arr_attack_gen.py:198-254`). |
| Retry loop and fallback to highest-similarity candidate | ✅ | ✅ Still correct | Loop with `max_retries` and global best retained (`arr_attack_gen.py:289-309`). |

**NEW Issues Found This Iteration:**
- None.

**Summary:**
- Fixed: 2 issues
- Partially Fixed: 0 issues
- Still Broken: 0 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2505.17598
- Attack: arr_attack_gen
- Verdict: 100% Fidelity
- Coverage: 9/9 components (100%)
- Iteration: 3

## Executive Summary
All prior gaps are resolved: beam-search controls are exposed and plumbed behind `use_beam_search`, and `max_new_tokens` now governs generation length with separate input truncation. Sampling defaults (`do_sample=True`, `top_p=0.9`, `temperature=0.8`) remain intact, with small-batch generation, retry-and-filter control flow, and semantic similarity scoring unchanged. No new issues were identified; current code fully matches the implementation plan and framework contract.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §5 Setup | Lazy-load T5 paraphraser and MPNet models | `src/jbfoundry/attacks/generated/arr_attack_gen.py:123-144` | ✅ | Loads on first use, moves to device. |
| §3.2 Generation (sampling default) | Sampling with `do_sample=True`, `top_p=0.9`, `temperature=0.8`, small batch `num_return_sequences=5` | `src/jbfoundry/attacks/generated/arr_attack_gen.py:198-254` | ✅ | Default path uses sampling for per-attempt diversity. |
| Plan §3 Parameter Mapping | Expose beam controls `num_beams=20`, `diversity_penalty=3.0` and enable beam mode when requested | `src/jbfoundry/attacks/generated/arr_attack_gen.py:32-109,233-244` | ✅ | AttackParameters added; beam path guarded by `use_beam_search`. |
| Plan §3 Parameter Mapping | Honor `max_new_tokens` as generation budget with separate input truncation | `src/jbfoundry/attacks/generated/arr_attack_gen.py:211-254` | ✅ | Uses `max_new_tokens`; input truncated at 512 tokens. |
| §3.2 Similarity Scoring | MPNet mean pooling + cosine similarity | `src/jbfoundry/attacks/generated/arr_attack_gen.py:145-197` | ✅ | Mean pooling, L2 norm, dot-product cosine. |
| §3.2 Threshold Filtering | Reject candidates with similarity <0.7 | `src/jbfoundry/attacks/generated/arr_attack_gen.py:289-306` | ✅ | Applies configurable `sim_threshold`. |
| §3.2 Retry Control | Retry generation up to limit when all candidates fail threshold | `src/jbfoundry/attacks/generated/arr_attack_gen.py:289-306` | ✅ | Loops up to `max_retries` regenerations. |
| §3.2 Attempt Randomness | Per-call diversity via sampling randomness (implicit `attempt_index`) | `src/jbfoundry/attacks/generated/arr_attack_gen.py:246-254` | ✅ | Sampling path ensures stochastic outputs each call. |
| §3.2 Fallback | Return highest-similarity candidate if none pass threshold | `src/jbfoundry/attacks/generated/arr_attack_gen.py:289-309` | ✅ | Tracks global best across retries before returning. |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌/⚠️) | Notes |
|---|---|---|---|---|---|
| Paraphraser Model | paraphraser_model | str | humarin/chatgpt_paraphraser_on_T5_base | ✅ | Matches plan mapping. |
| Semantic Model | semantic_model | str | sentence-transformers/all-mpnet-base-v2 | ✅ | Matches plan mapping. |
| Similarity Threshold | sim_threshold | float | 0.7 | ✅ | Used in filtering. |
| Number of Beams | num_beams | int | 20 | ✅ | Exposed; used when `use_beam_search` is enabled. |
| Diversity Penalty | diversity_penalty | float | 3.0 | ✅ | Exposed; applied in beam mode. |
| Max New Tokens | max_new_tokens | int | 256 | ✅ | Passed to `generate` as `max_new_tokens`. |
| Sampling Temperature (plan inference defaults) | temperature | float | 0.8 | ✅ | Used in sampling path. |
| Top-p (plan inference defaults) | top_p | float | 0.9 | ✅ | Used in sampling path. |
| Batch Size (small batch) | num_return_sequences | int | 5 | ✅ | Generates small batch per attempt. |
| Retry Limit | max_retries | int | 3 | ✅ | Controls regeneration loop. |

## Misalignments / Missing Items
- None.

## Extra Behaviors Not in Paper
- Optional `use_beam_search` flag allows switching to beam search; default remains sampling per plan.

## Required Changes to Reach 100%
- None; implementation matches the plan and framework contracts.

## Final Verdict
100% Fidelity

# Audit Iteration 2 - 2025-12-31

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Sampling-based generation (do_sample with top_p=0.9, temperature=0.8) | ❌ | ✅ Fixed | `_paraphrase()` now uses sampling with top_p/temperature (`src/jbfoundry/attacks/generated/arr_attack_gen.py:177-222`). |
| Attempt randomness via sampling per call | ❌ | ✅ Fixed | Sampling generation provides per-call diversity (`arr_attack_gen.py:177-222`). |
| Batch size small (~5) candidates per attempt | ⚠️ | ✅ Fixed | `num_return_sequences` default changed to 5 (`arr_attack_gen.py:61-67`). |
| Retry loop when all candidates fail similarity threshold | ⚠️ | ✅ Fixed | `generate_attack` regenerates up to `max_retries` times (`arr_attack_gen.py:223-269`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Lazy-load T5 and MPNet models | ✅ | ✅ Still correct | `_load_models` still lazily loads and moves to device (`arr_attack_gen.py:102-123`). |
| Semantic similarity via mean pooling + cosine | ✅ | ✅ Still correct | `_get_similarity` unchanged behavior (`arr_attack_gen.py:141-175`). |
| Fallback to highest-similarity candidate | ✅ | ✅ Still correct | Returns best candidate when none meet threshold (`arr_attack_gen.py:268-271`). |

**NEW Issues Found This Iteration:**
- Missing exposure of beam search controls `num_beams` and `diversity_penalty` that the plan enumerates in Parameter Mapping; PARAMETERS omit them entirely, so users cannot configure or inspect these plan-listed parameters (`arr_attack_gen.py:32-89`).
- `max_new_tokens` parameter is applied as `max_length` in generation, reducing effective new-token budget and diverging from the plan’s “max new tokens” behavior (`arr_attack_gen.py:196-216`).

**Summary:**
- Fixed: 4 issues
- Partially Fixed: 0 issues
- Still Broken: 0 issues
- Regressions: 0 issues
- New Issues: 2 issues

# Implementation Fidelity Verdict
- Paper ID: 2505.17598
- Attack: arr_attack_gen
- Verdict: Not 100% Fidelity
- Coverage: 7/9 components (78%)
- Iteration: 2

## Executive Summary
The updated implementation fixes the prior deficiencies by switching to sampling-based generation with `top_p=0.9`, `temperature=0.8`, a small batch size of 5, and a retry loop that regenerates when all candidates fail the similarity threshold. Core behaviors—lazy loading, MPNet similarity with mean pooling, and fallback selection—remain intact. Two fidelity gaps remain relative to the implementation plan: (1) the plan’s Parameter Mapping lists `num_beams` and `diversity_penalty`, but these parameters are now missing entirely; (2) the `max_new_tokens` parameter is applied as `max_length`, which reduces the allowed new-token budget versus the plan’s intended semantics. Due to these deviations, fidelity is not yet 100%.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §5 Setup | Lazy-load T5 paraphraser and MPNet similarity models | `src/jbfoundry/attacks/generated/arr_attack_gen.py:102-123` | ✅ | Matches plan lazy loading and device placement. |
| §3.2 Generation Diversity | Use sampling with `do_sample=True`, `top_p=0.9`, `temperature=0.8` | `src/jbfoundry/attacks/generated/arr_attack_gen.py:177-222` | ✅ | Sampling replaces beam search per plan. |
| §3.2 Batch Size | Generate small batch (~5) candidates per attempt | `src/jbfoundry/attacks/generated/arr_attack_gen.py:61-67,191-216` | ✅ | Default batch size set to 5. |
| §3.2 Similarity Scoring | MPNet mean pooling + cosine similarity | `src/jbfoundry/attacks/generated/arr_attack_gen.py:141-175` | ✅ | Implements mean pooling + normalized cosine. |
| §3.2 Threshold Filtering | Reject candidates <0.7 and retry generation up to a limit | `src/jbfoundry/attacks/generated/arr_attack_gen.py:223-269` | ✅ | Retry loop with `max_retries`, returns on first pass candidate. |
| §3.2 Attempt Randomness | Per-call diversity reflecting attempt_index via sampling | `src/jbfoundry/attacks/generated/arr_attack_gen.py:177-222` | ✅ | Sampling randomness provides per-call variation. |
| §3.2 Fallback | Return highest-similarity candidate if none pass threshold | `src/jbfoundry/attacks/generated/arr_attack_gen.py:268-271` | ✅ | Fallback implemented. |
| Plan §3 Parameter Mapping | Expose beam controls (`num_beams=20`, `diversity_penalty=3.0`) | `src/jbfoundry/attacks/generated/arr_attack_gen.py:32-89` | ❌ | PARAMETERS omit these plan-listed controls. |
| Plan §3 Parameter Mapping | Honor `max_new_tokens` as generation budget | `src/jbfoundry/attacks/generated/arr_attack_gen.py:196-216` | ⚠️ | Uses `max_length` instead of `max_new_tokens`, reducing allowed new tokens. |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌/⚠️) | Notes |
|---|---|---|---|---|---|
| Paraphraser Model | paraphraser_model | str | humarin/chatgpt_paraphraser_on_T5_base | ✅ | Matches plan. |
| Semantic Model | semantic_model | str | sentence-transformers/all-mpnet-base-v2 | ✅ | Matches plan. |
| Similarity Threshold | sim_threshold | float | 0.7 | ✅ | Matches plan. |
| Max New Tokens | max_new_tokens | int | 256 | ⚠️ | Applied as `max_length`, not `max_new_tokens`, reducing budget. |
| Number of Beams | (missing) | int | 20 | ❌ | Not exposed or used despite plan mapping. |
| Diversity Penalty | (missing) | float | 3.0 | ❌ | Not exposed or used despite plan mapping. |
| Sampling Temperature | temperature | float | 0.8 | ✅ | Implemented and used for sampling. |
| Top-p | top_p | float | 0.9 | ✅ | Implemented and used for sampling. |
| Batch Size (small batch ~5) | num_return_sequences | int | 5 | ✅ | Provided and used. |
| Retry Limit | max_retries | int | 3 | ✅ | Added for retry loop (plan allows retry control). |

## Misalignments / Missing Items
- **Beam parameters omitted** (Plan Parameter Mapping §3): Plan lists `num_beams=20` and `diversity_penalty=3.0` as configurable parameters. Current PARAMETERS do not expose or use these controls, removing user access to plan-listed knobs (`arr_attack_gen.py:32-89`). Impact: deviates from plan’s parameter surface and prevents beam-style configuration when desired.
- **`max_new_tokens` semantics diverge** (Plan Parameter Mapping §3): Plan expects `max_new_tokens` to cap newly generated tokens. Implementation passes this value to `max_length` (`arr_attack_gen.py:196-216`), which counts input tokens as well, reducing the allowable generation length and altering the constraint relative to the plan.

## Extra Behaviors Not in Paper
- Adds `max_retries` parameter (default 3) to control regeneration loops (`arr_attack_gen.py:82-88,223-269`); while compatible with the plan’s retry concept, this specific default and configurability are not enumerated in the plan.

## Required Changes to Reach 100%
1. **Expose beam controls per plan**: Add `num_beams` (default 20) and `diversity_penalty` (default 3.0) as `AttackParameter`s and plumb them into generation when beam search is selected, or at minimum expose them for configurability to align with the plan’s parameter mapping (`arr_attack_gen.py:32-89`).  
2. **Honor `max_new_tokens` semantics**: Use `max_new_tokens` in `generate` (e.g., `max_new_tokens=max_new_tokens`) and keep encoder truncation separate, so the generation budget matches the plan (`arr_attack_gen.py:196-216`).

## Final Verdict
Not 100% Fidelity

# Implementation Fidelity Verdict
- Paper ID: 2505.17598
- Attack: arr_attack_gen
- Verdict: Not 100% Fidelity
- Coverage: 4/8 components (50%)
- Iteration: 1

## Executive Summary
The implementation captures the basic structure of ArrAttack’s Basic Rewriting-based Jailbreak: lazy-loading the T5 paraphraser and MPNet similarity model, generating multiple paraphrases with beam/diversity settings, computing semantic similarity with mean pooling, and returning the best candidate. However, it diverges from the implementation plan on two key behaviors: (1) the plan requires sampling-based generation with `top_p=0.9` and `temperature=0.8` to provide per-attempt diversity (and implicit `attempt_index` handling), but the code uses deterministic beam search without sampling; and (2) the plan requires retrying generation when all candidates fall below the similarity threshold, but the code performs only a single generation pass and immediately returns the best candidate. These gaps prevent 100% fidelity despite otherwise accurate parameter defaults and similarity computation.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §5 Setup | Lazy-load T5 paraphraser and MPNet similarity models | `src/jbfoundry/attacks/generated/arr_attack_gen.py:109-130` | ✅ | Matches plan lazy loading and device placement. |
| §3.2 Generation Diversity | Use sampling with `do_sample=True`, `top_p=0.9`, `temperature=0.8` for per-attempt diversity | `src/jbfoundry/attacks/generated/arr_attack_gen.py:194-227` | ❌ | Uses deterministic beam search; no sampling or top_p/temperature. |
| §3.2 Beam Parameters | Beam/diversity settings (`num_beams=20`, `diversity_penalty=3.0`, `max_new_tokens=256`) | `src/jbfoundry/attacks/generated/arr_attack_gen.py:55-74,214-223` | ✅ | Defaults align with plan. |
| §3.2 Batch Size | Generate small batch (~5) candidates per attempt | `src/jbfoundry/attacks/generated/arr_attack_gen.py:214-223` | ⚠️ | Generates 10 candidates; larger than planned “small batch (e.g., 5)”. |
| §3.2 Similarity Scoring | MPNet mean pooling + cosine similarity | `src/jbfoundry/attacks/generated/arr_attack_gen.py:148-182` | ✅ | Implements mean pooling + normalized cosine. |
| §3.2 Threshold Filtering | Reject candidates with similarity < 0.7 and retry generation up to a limit | `src/jbfoundry/attacks/generated/arr_attack_gen.py:246-268` | ⚠️ | Applies threshold but no retry/regeneration loop; single pass only. |
| §3.2 Attempt Randomness | Use sampling randomness to reflect `attempt_index` across calls | `src/jbfoundry/attacks/generated/arr_attack_gen.py:194-227` | ❌ | Deterministic beam search; no per-attempt randomness. |
| §3.2 Fallback | Return highest-similarity candidate if none pass threshold | `src/jbfoundry/attacks/generated/arr_attack_gen.py:268-270` | ✅ | Fallback implemented. |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Paraphraser Model | paraphraser_model | str | humarin/chatgpt_paraphraser_on_T5_base | ✅ | Matches plan. |
| Semantic Model | semantic_model | str | sentence-transformers/all-mpnet-base-v2 | ✅ | Matches plan. |
| Similarity Threshold | sim_threshold | float | 0.7 | ✅ | Matches plan. |
| Number of Beams | num_beams | int | 20 | ✅ | Matches plan. |
| Diversity Penalty | diversity_penalty | float | 3.0 | ✅ | Matches plan. |
| Max New Tokens | max_new_tokens | int | 256 | ✅ | Matches plan. |
| Sampling Temperature | (missing) | float | 0.8 (expected) | ❌ | Not implemented; beam search used instead. |
| Top-p | (missing) | float | 0.9 (expected) | ❌ | Not implemented; beam search used instead. |

## Misalignments / Missing Items
- **Sampling-based generation absent** (Plan §3.2, impl instructions lines 82–85): Plan mandates `do_sample=True` with `top_p=0.9` and `temperature=0.8` to provide per-attempt diversity and implicit `attempt_index` handling. Code uses deterministic beam search with no sampling (`arr_attack_gen.py:194-227`), so repeated calls produce the same outputs and do not reflect the planned stochastic behavior.
- **No retry loop when all candidates fail similarity threshold** (Plan §3.2, lines 40–41, 90–91): The plan specifies rejecting candidates below 0.7 and retrying generation up to a limit. Implementation only evaluates the initial batch once and returns the best candidate without regeneration (`arr_attack_gen.py:246-270`), potentially returning low-similarity paraphrases contrary to the plan’s control flow.

## Extra Behaviors Not in Paper
- Additional generation controls (`num_return_sequences=10`, `repetition_penalty=10.0`, `no_repeat_ngram_size=2`, `num_beam_groups=num_beams`) are applied (`arr_attack_gen.py:75-96,214-223`); these are not specified in the plan and may alter paraphrase distribution relative to the planned sampling approach.

## Required Changes to Reach 100%
1. Implement sampling-based generation per plan (use `do_sample=True`, `top_p=0.9`, `temperature=0.8`) and ensure per-call diversity/attempt_index handling. Adjust `_paraphrase` or `generate_attack` to use sampling instead of deterministic beam search (`src/jbfoundry/attacks/generated/arr_attack_gen.py:194-223`).
2. Add a retry loop in `generate_attack` that regenerates paraphrases when all candidates fall below `sim_threshold`, up to a defined retry limit, before falling back to the best candidate (`src/jbfoundry/attacks/generated/arr_attack_gen.py:246-270`).

## Final Verdict
Not 100% Fidelity

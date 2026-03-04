## Audit Iteration 5 - 2025-12-27

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Experience search scoring used additive weights instead of cosine * success_rate | ❌ | ✅ Fixed | `search_within_cluster` now scores `cos_sim * success_rate`, matching the reference formula (`src/jbfoundry/attacks/generated/jailexpert_gen.py:438-473`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Representative pattern extraction | ✅ | ✅ | Still selects most frequent `(mutation, template)` and breaks ties by success rate (`jailexpert_gen.py:408-435`). |
| Cluster ranking | ✅ | ✅ | Ranks clusters via representative-applied drift vs. centers unchanged (`jailexpert_gen.py:650-689`). |
| Attempt sequencing | ✅ | ✅ | Maintains REP then EXP_i ordering with cycling over `top_k` (`jailexpert_gen.py:715-736`). |

**NEW Issues Found This Iteration:**
- `scalar_weight` and `semantic_weight` are exposed and stored but never used in search/ranking, so user-specified weights have no effect on retrieval (`jailexpert_gen.py:438-473,531-574`). This regresses parameter control expected by the plan.

**Summary:**
- Fixed: 1 issues
- Partially Fixed: 0 issues
- Still Broken: 0 issues
- Regressions: 1 issues
- New Issues: 1 issues

# Implementation Fidelity Verdict (Iteration 5)
- Paper ID: 2508.19292
- Attack: jailexpert_gen
- Verdict: Not 100% Fidelity
- Coverage: 12/13 components (92%)
- Iteration: 5

## Executive Summary
Search scoring now matches the reference repo/paper by using cosine similarity scaled by success rate, resolving the prior additive-weight regression. However, the scalar and semantic weighting parameters are now no-ops: they are parsed and passed to `ExperienceIndex` but never applied in similarity scoring or ranking, so users cannot modulate scalar vs. semantic influence as planned. Fidelity remains below 100% due to this missing parameter control.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Experience Formalization | Load JSON into `JailbreakState (I,J,A,s,f)` | `src/jbfoundry/attacks/generated/jailexpert_gen.py:585-629` | ✅ | Parses mutation, method, pre/full query with fallback |
| Semantic Drift Computation | Δ = Φ(J) – Φ(I) for experiences | `src/jbfoundry/attacks/generated/jailexpert_gen.py:297-305` | ✅ | Builds diff vectors from cached embeddings |
| Cluster Count Selection | Silhouette search up to `n_clusters` | `src/jbfoundry/attacks/generated/jailexpert_gen.py:315-344` | ✅ | Picks best_k with PCA + silhouette |
| Clustering & Centers | K-Means on drift vectors, store centers | `src/jbfoundry/attacks/generated/jailexpert_gen.py:347-355` | ✅ | Fits KMeans or mean for single cluster |
| Representative Pattern Extraction | Most frequent/successful (mutation, template) per cluster | `src/jbfoundry/attacks/generated/jailexpert_gen.py:408-435` | ✅ | Counter + success-rate tie-break |
| Cluster Ranking | Sim((Φ(Rep(p))–Φ(p)), Center) ranking | `src/jbfoundry/attacks/generated/jailexpert_gen.py:650-689` | ✅ | Applies rep pattern, embeds, compares to centers |
| Attempt Sequencing | Map attempt_index to [(C,REP),(C,EXP_i)…] | `src/jbfoundry/attacks/generated/jailexpert_gen.py:715-736` | ✅ | Iterates rep then each exp up to `top_k`, cycles |
| Representative Pattern Application | Apply cluster representative mutation+template | `src/jbfoundry/attacks/generated/jailexpert_gen.py:746-775` | ✅ | Mutations then template, placeholder cleanup |
| Experience Search Scoring | Search cluster via cosine_similarity * success_rate | `src/jbfoundry/attacks/generated/jailexpert_gen.py:438-473` | ✅ | Matches reference ExperienceIndex formula |
| Parameter Weighting Controls | `scalar_weight` / `semantic_weight` affect search | `src/jbfoundry/attacks/generated/jailexpert_gen.py:438-473,531-574` | ❌ | Weights parsed/stored but not applied; controls are no-ops |
| Top-K Retrieval | Retrieve multiple experiences per cluster | `src/jbfoundry/attacks/generated/jailexpert_gen.py:717-724,777-795` | ✅ | `exp_idx` selects among `top_k` search results |
| Embedding/Index Caching | Reuse cached embeddings/index across runs | `src/jbfoundry/attacks/generated/jailexpert_gen.py:210-406` | ✅ | Caches embeddings plus clustering artifacts under `cache/jailexpert_gen/` |
| Mutation Engine Coverage | Mutation set from plan/reference | `src/jbfoundry/attacks/generated/jailexpert_gen.py:41-195` | ✅ | Implements Base64/Rot13/Leetspeak/Disemvowel + LLM-based, placeholders |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Experience Pool Path | experience_path | str | `attacks_paper_info/2508.19292/JailExpert/experience/experiences_examples.json` | ✅ | Resolved relative to project root |
| Embedding Model | embedding_model | str | `text-embedding-3-small` | ✅ | Used for litellm embeddings |
| Attack/Mutation Model | attack_model | str | `gpt-3.5-turbo` | ✅ | Passed into MutationEngine |
| Max Clusters | n_clusters | int | 10 | ✅ | Limits KMeans search |
| Top K | top_k | int | 1 | ✅ | Drives attempt mapping and search results |
| Scalar Weight | scalar_weight | float | 0.1 | ❌ | Parsed/passed but unused in similarity scoring |
| Semantic Weight | semantic_weight | float | 0.9 | ❌ | Parsed/passed but unused in similarity scoring |

## Misalignments / Missing Items
- **Weighting parameters are no-ops**: `scalar_weight` and `semantic_weight` are exposed and stored but never applied in cluster search or ranking, so users cannot modulate scalar vs. semantic influence as specified in the plan. Retrieval is fixed to `cosine_similarity * success_rate` regardless of weight settings (`src/jbfoundry/attacks/generated/jailexpert_gen.py:438-473,531-574`).

## Extra Behaviors Not in Paper
- Fallback synthetic experience when the JSON file is missing (`src/jbfoundry/attacks/generated/jailexpert_gen.py:595-609`).
- Hardcoded LiteLLM provider `"wenwen"` for both embedding and attack LLMs (`src/jbfoundry/attacks/generated/jailexpert_gen.py:560-567`).

## Required Changes to Reach 100%
- **Apply scalar/semantic weights in retrieval**: Integrate `scalar_weight` and `semantic_weight` into similarity scoring (e.g., scale semantic cosine by `semantic_weight` and the success-rate term by `scalar_weight` as per the plan) so user-specified weights affect experience ranking (`jailexpert_gen.py:438-473,531-574`).

## Final Verdict
Not 100% Fidelity

# Implementation Fidelity Verdict (Iteration 4)

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| `scalar_weight` / `semantic_weight` unused in search | 🔄 Regressed | ✅ Fixed | Weights are now applied in `search_within_cluster` (`src/jbfoundry/attacks/generated/jailexpert_gen.py:438-467`), though the scoring formula changed (see regression). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Experience search scoring | ✅ | 🔄 Regressed | Scoring switched from success-rate-weighted cosine (reference/paper) to `semantic_weight * cosine + scalar_weight * success_rate` (`jailexpert_gen.py:438-467`). |

**NEW Issues Found This Iteration:**
- Experience search scoring now uses an additive weighted sum (`semantic_weight * cosine + scalar_weight * success_rate`) instead of the reference/paper formulation `cosine_similarity * success_rate`, changing retrieval rankings (`src/jbfoundry/attacks/generated/jailexpert_gen.py:438-467`; reference `attacks_paper_info/2508.19292/JailExpert/codes/ExperienceIndex.py:230-242`).

**Summary:**
- Fixed: 1 issues
- Partially Fixed: 0 issues
- Still Broken: 0 issues
- Regressions: 1 issues
- New Issues: 1 issues

# Implementation Fidelity Verdict (Iteration 4)
- Paper ID: 2508.19292
- Attack: jailexpert_gen
- Verdict: Not 100% Fidelity
- Coverage: 12/13 components (92%)
- Iteration: 4

## Executive Summary
Weights are now applied in cluster experience search, restoring the intended parameter controls. However, the search score changed from the reference/paper’s success-rate-weighted semantic similarity to an additive weighted sum of cosine similarity and success rate, which alters retrieval ordering. Due to this regression in the core search formulation, fidelity remains below 100%.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Experience Formalization | Load JSON into `JailbreakState (I,J,A,s,f)` | `src/jbfoundry/attacks/generated/jailexpert_gen.py:586-629` | ✅ | Parses mutation, method, pre/full query with fallback |
| Semantic Drift Computation | Δ = Φ(J) – Φ(I) for experiences | `src/jbfoundry/attacks/generated/jailexpert_gen.py:297-305` | ✅ | Builds diff vectors from cached embeddings |
| Cluster Count Selection | Silhouette search up to `n_clusters` | `src/jbfoundry/attacks/generated/jailexpert_gen.py:315-344` | ✅ | Picks best_k with PCA + silhouette |
| Clustering & Centers | K-Means on drift vectors, store centers | `src/jbfoundry/attacks/generated/jailexpert_gen.py:347-355` | ✅ | Fits KMeans or mean for single cluster |
| Representative Pattern Extraction | Most frequent/successful (mutation, template) per cluster | `src/jbfoundry/attacks/generated/jailexpert_gen.py:408-435` | ✅ | Counter + success-rate tie-break |
| Cluster Ranking | Sim((Φ(Rep(p))–Φ(p)), Center) ranking | `src/jbfoundry/attacks/generated/jailexpert_gen.py:651-688` | ✅ | Applies rep pattern, embeds, compares to centers |
| Attempt Sequencing | Map attempt_index to [(C,REP),(C,EXP_i)…] | `src/jbfoundry/attacks/generated/jailexpert_gen.py:717-736` | ✅ | Iterates rep then each exp up to `top_k`, cycles |
| Representative Pattern Application | Apply cluster representative mutation+template | `src/jbfoundry/attacks/generated/jailexpert_gen.py:747-775` | ✅ | Mutations then template, placeholder cleanup |
| Experience Search Scoring | Search cluster using semantic+success weighting | `src/jbfoundry/attacks/generated/jailexpert_gen.py:438-467` | ❌ | Uses additive weighted sum; reference/paper uses cosine * success_rate |
| Parameter Weighting Controls | `scalar_weight` / `semantic_weight` affect search | `src/jbfoundry/attacks/generated/jailexpert_gen.py:438-467,533-544` | ✅ | Weights now applied in scoring |
| Top-K Retrieval | Retrieve multiple experiences per cluster | `src/jbfoundry/attacks/generated/jailexpert_gen.py:717-724,777-795` | ✅ | `exp_idx` selects among `top_k` search results |
| Embedding/Index Caching | Reuse cached embeddings/index across runs | `src/jbfoundry/attacks/generated/jailexpert_gen.py:210-406` | ✅ | Caches embeddings plus clustering artifacts under `cache/jailexpert_gen/` |
| Mutation Engine Coverage | Mutation set from plan/reference | `src/jbfoundry/attacks/generated/jailexpert_gen.py:41-195` | ✅ | Implements Base64/Rot13/Leetspeak/Disemvowel + LLM-based, placeholders |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Experience Pool Path | experience_path | str | `attacks_paper_info/2508.19292/JailExpert/experience/experiences_examples.json` | ✅ | Resolved relative to project root |
| Embedding Model | embedding_model | str | `text-embedding-3-small` | ✅ | Used for litellm embeddings |
| Attack/Mutation Model | attack_model | str | `gpt-3.5-turbo` | ✅ | Passed into MutationEngine |
| Max Clusters | n_clusters | int | 10 | ✅ | Limits KMeans search |
| Top K | top_k | int | 1 | ✅ | Drives attempt mapping and search results |
| Scalar Weight | scalar_weight | float | 0.1 | ❌ | Applied additively; reference uses success_rate scaling without weights |
| Semantic Weight | semantic_weight | float | 0.9 | ❌ | Applied additively; reference uses success_rate scaling without weights |

## Misalignments / Missing Items
- **Search scoring deviates from reference/paper**: Retrieval score is `semantic_weight * cosine_similarity + scalar_weight * success_rate`, whereas the reference and plan use success-rate-weighted semantic similarity (`cosine_similarity * success_rate`). This changes experience ranking and diverges from the gold-standard implementation (`src/jbfoundry/attacks/generated/jailexpert_gen.py:438-467`; reference `attacks_paper_info/2508.19292/JailExpert/codes/ExperienceIndex.py:230-242`).

## Extra Behaviors Not in Paper
- Fallback synthetic experience when the JSON file is missing (`src/jbfoundry/attacks/generated/jailexpert_gen.py:595-609`).
- Hardcoded LiteLLM provider `"wenwen"` for both embedding and attack LLMs (`src/jbfoundry/attacks/generated/jailexpert_gen.py:560-567`).

## Required Changes to Reach 100%
- **Align search scoring with reference/paper**: Replace the additive weighted sum in `search_within_cluster` with success-rate-weighted semantic similarity (e.g., `score = cosine_similarity * success_rate`, optionally scaling the semantic term but not adding success_rate separately) to match the gold-standard retrieval behavior (`src/jbfoundry/attacks/generated/jailexpert_gen.py:438-467`; reference `ExperienceIndex.py:230-242`).

## Final Verdict
Not 100% Fidelity

## Audit Iteration 3 - 2025-12-27

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| `scalar_weight` / `semantic_weight` unused in search | ✅ | 🔄 Regressed | Weights are now unused; scoring is cosine * success_rate only (`src/jbfoundry/attacks/generated/jailexpert_gen.py:438-473`, params at 531-544). |
| `top_k` retrieval ignored | ✅ | ✅ Fixed | Attempt mapping still iterates through `top_k` experiences and passes `exp_idx` to `_apply_best_experience` (`jailexpert_gen.py:715-736,776-815`). |
| No embedding/index caching | ⚠️ | ✅ Fixed | Full index artifacts (centers, assignments, patterns) now cached and reloaded via `{cache_key}_index.pkl` (`jailexpert_gen.py:210-406`). |
| Experience search scoring deviates from plan/reference | ❌ | ✅ Fixed | Scoring now matches reference: cosine similarity scaled by success rate; harmfulness term removed (`jailexpert_gen.py:438-473`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Semantic drift computation | ✅ | ✅ | Drift remains `full_emb - pre_emb` when building index (`jailexpert_gen.py:297-305`). |
| Representative pattern application | ✅ | ✅ | Applies mutation tuple then template with placeholder cleanup (`jailexpert_gen.py:746-774`). |
| Attempt sequencing | ✅ | ✅ | REP then EXP_i ordering with cycling preserved (`jailexpert_gen.py:715-736`). |

**NEW Issues Found This Iteration:**
- Parameter weighting controls regressed to no-ops: `scalar_weight` / `semantic_weight` are exposed but never used in search or ranking, so user inputs cannot influence retrieval (`jailexpert_gen.py:200-203,438-473,531-544`).

**Summary:**
- Fixed: 2 issues
- Partially Fixed: 0 issues
- Still Broken: 0 issues
- Regressions: 1 issues
- New Issues: 1 issues

# Implementation Fidelity Verdict (Iteration 3)
- Paper ID: 2508.19292
- Attack: jailexpert_gen
- Verdict: Not 100% Fidelity
- Coverage: 12/13 components (92%)
- Iteration: 3

## Executive Summary
Caching now includes full clustering artifacts and experience search scoring matches the reference formulation (cosine similarity scaled by success rate). However, the scalar/semantic weighting controls regressed: `scalar_weight` and `semantic_weight` are exposed parameters but have no effect on retrieval or ranking, making them no-ops compared to the implementation plan. Fidelity remains below 100% due to this behavioral gap.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Experience Formalization | Load JSON into `JailbreakState (I,J,A,s,f)` | `src/jbfoundry/attacks/generated/jailexpert_gen.py:585-628` | ✅ | Parses mutation, method, pre/full query with fallback |
| Semantic Drift Computation | Δ = Φ(J) – Φ(I) for experiences | `src/jbfoundry/attacks/generated/jailexpert_gen.py:297-305` | ✅ | Builds diff vectors from cached embeddings |
| Cluster Count Selection | Silhouette search up to `n_clusters` | `src/jbfoundry/attacks/generated/jailexpert_gen.py:315-344` | ✅ | Picks best_k with PCA + silhouette |
| Clustering & Centers | K-Means on drift vectors, store centers | `src/jbfoundry/attacks/generated/jailexpert_gen.py:347-355` | ✅ | Fits KMeans or mean for single cluster |
| Representative Pattern Extraction | Most frequent/successful (mutation, template) per cluster | `src/jbfoundry/attacks/generated/jailexpert_gen.py:408-435` | ✅ | Counter + success-rate tie-break |
| Cluster Ranking | Sim((Φ(Rep(p))–Φ(p)), Center) ranking | `src/jbfoundry/attacks/generated/jailexpert_gen.py:650-689` | ✅ | Applies rep pattern, embeds, compares to centers |
| Attempt Sequencing | Map attempt_index to [(C,REP),(C,EXP_i)…] | `src/jbfoundry/attacks/generated/jailexpert_gen.py:715-736` | ✅ | Iterates rep then each exp up to `top_k`, cycles |
| Representative Pattern Application | Apply cluster representative mutation+template | `src/jbfoundry/attacks/generated/jailexpert_gen.py:746-774` | ✅ | Mutations then template, placeholder cleanup |
| Experience Search Scoring | Search cluster via success-rate-weighted semantic similarity | `src/jbfoundry/attacks/generated/jailexpert_gen.py:438-473` | ✅ | Cosine similarity scaled by success rate (matches reference) |
| Parameter Weighting Controls | `scalar_weight` / `semantic_weight` affect search | `src/jbfoundry/attacks/generated/jailexpert_gen.py:200-203,438-473,531-544` | ❌ | Weights stored but unused; user input cannot change retrieval |
| Top-K Retrieval | Retrieve multiple experiences per cluster | `src/jbfoundry/attacks/generated/jailexpert_gen.py:715-724,789-795` | ✅ | `exp_idx` selects among `top_k` search results |
| Embedding/Index Caching | Reuse cached embeddings/index across runs | `src/jbfoundry/attacks/generated/jailexpert_gen.py:210-406` | ✅ | Caches embeddings plus clustering artifacts under `cache/jailexpert_gen/` |
| Mutation Engine Coverage | Mutation set from plan/reference | `src/jbfoundry/attacks/generated/jailexpert_gen.py:41-195` | ✅ | Implements Base64/Rot13/Leetspeak/Disemvowel + LLM-based, placeholders |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Experience Pool Path | experience_path | str | `attacks_paper_info/2508.19292/JailExpert/experience/experiences_examples.json` | ✅ | Resolved relative to project root |
| Embedding Model | embedding_model | str | `text-embedding-3-small` | ✅ | Used for litellm embeddings |
| Attack/Mutation Model | attack_model | str | `gpt-3.5-turbo` | ✅ | Passed into MutationEngine |
| Max Clusters | n_clusters | int | 10 | ✅ | Limits KMeans search |
| Top K | top_k | int | 1 | ✅ | Drives attempt mapping and search results |
| Scalar Weight | scalar_weight | float | 0.1 | ❌ | Exposed but not applied in search/ranking |
| Semantic Weight | semantic_weight | float | 0.9 | ❌ | Exposed but not applied in search/ranking |

## Misalignments / Missing Items
- **Weighting parameters are no-ops**: `scalar_weight` and `semantic_weight` are declared and passed to `ExperienceIndex` but never used in similarity scoring or cluster ranking. Plan expects these to modulate scalar vs semantic influence; current retrieval ignores them (`src/jbfoundry/attacks/generated/jailexpert_gen.py:200-203,438-473,531-544`). Users cannot adjust weighting as documented.

## Extra Behaviors Not in Paper
- Fallback synthetic experience when the JSON file is missing (`src/jbfoundry/attacks/generated/jailexpert_gen.py:595-609`).
- Hardcoded LiteLLM provider `"wenwen"` for both embedding and attack LLMs (`src/jbfoundry/attacks/generated/jailexpert_gen.py:560-567`).

## Required Changes to Reach 100%
- **Reinstate functional weighting controls**: Integrate `scalar_weight` / `semantic_weight` into similarity scoring (e.g., scale semantic cosine by `semantic_weight` and scalar success-rate term by `scalar_weight`, matching plan/reference intent) so user-specified weights affect retrieval. Update `search_within_cluster` (around `jailexpert_gen.py:438-473`) and, if intended, any related ranking steps.

## Final Verdict
Not 100% Fidelity

# Audit Iteration 2 - 2025-12-27

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| `scalar_weight` / `semantic_weight` unused in search | ❌ | ✅ Fixed | Scoring now applies both weights in `search_within_cluster` (jailexpert_gen.py:398-426). |
| `top_k` retrieval ignored | ❌ | ✅ Fixed | Attempt mapping iterates through `top_k` experiences and selects `exp_idx` in `_apply_best_experience` (jailexpert_gen.py:677-706). |
| No embedding/index caching | ❌ | ⚠️ Partially Fixed | Embeddings are cached to `cache/jailexpert_gen`, but clustering/indexing still recomputed each run; no cached centers/assignments (jailexpert_gen.py:224-268,324-365). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Semantic drift computation | ✅ | ✅ | Drift remains `full_emb - pre_emb` (jailexpert_gen.py:274-287). |
| Representative pattern application | ✅ | ✅ | Still applies mutation tuple then template with placeholder cleanup (jailexpert_gen.py:708-736). |
| Attempt sequencing | ✅ | ✅ | REP then EXP actions preserved with cycling (jailexpert_gen.py:677-686). |

**NEW Issues Found This Iteration:**
- Experience search scoring diverges from plan/reference: uses weighted sum of cosine similarity plus averaged harmfulness/success rate, rather than success-rate-weighted semantic similarity; introduces harmfulness term not specified and changes ranking semantics (jailexpert_gen.py:398-426).

**Summary:**
- Fixed: 2 issues
- Partially Fixed: 1 issues
- Still Broken: 0 issues
- Regressions: 0 issues
- New Issues: 1 issues

## Implementation Fidelity Verdict (Iteration 2)
- Paper ID: 2508.19292
- Attack: jailexpert_gen
- Verdict: Not 100% Fidelity
- Coverage: 11/13 components (85%)
- Iteration: 2

## Executive Summary
Weights now influence experience search and `top_k` retrieval is respected across attempts. However, caching still only stores embeddings (clusters rebuilt each run), and the experience search score diverges from the planned/reference formulation by adding harmfulness and summing weighted parts instead of success-rate–scaled semantic similarity. These gaps keep fidelity below 100%.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Experience Formalization | Load JSON into `JailbreakState (I,J,A,s,f)` | `src/jbfoundry/attacks/generated/jailexpert_gen.py:547-599` | ✅ | Parses mutation, method, pre/full query with fallback |
| Semantic Drift Computation | Δ = Φ(J) – Φ(I) for experiences | `src/jbfoundry/attacks/generated/jailexpert_gen.py:274-287` | ✅ | Builds diff vectors from cached embeddings |
| Cluster Count Selection | Silhouette search up to `n_clusters` | `src/jbfoundry/attacks/generated/jailexpert_gen.py:292-321` | ✅ | Picks best_k with PCA + silhouette |
| Clustering & Centers | K-Means on drift vectors, store centers | `src/jbfoundry/attacks/generated/jailexpert_gen.py:324-332` | ✅ | Fits KMeans or mean for single cluster |
| Representative Pattern Extraction | Most frequent/successful (mutation, template) per cluster | `src/jbfoundry/attacks/generated/jailexpert_gen.py:368-396` | ✅ | Counter + success-rate tie-break |
| Cluster Ranking | Sim((Φ(Rep(p))–Φ(p)), Center) ranking | `src/jbfoundry/attacks/generated/jailexpert_gen.py:612-652` | ✅ | Applies rep pattern, embeds, compares to centers |
| Attempt Sequencing | Map attempt_index to [(C,REP),(C,EXP_i)…] | `src/jbfoundry/attacks/generated/jailexpert_gen.py:677-686` | ✅ | Iterates rep then each exp up to `top_k`, cycles |
| Representative Pattern Application | Apply cluster representative mutation+template | `src/jbfoundry/attacks/generated/jailexpert_gen.py:708-736` | ✅ | Mutations then template, placeholder cleanup |
| Experience Search Scoring | Search cluster using semantic + scalar weighting | `src/jbfoundry/attacks/generated/jailexpert_gen.py:398-435` | ⚠️ | Weighted sum with harmfulness; deviates from success-rate–scaled cosine in plan/reference |
| Parameter Weighting Controls | `scalar_weight` / `semantic_weight` affect search | `src/jbfoundry/attacks/generated/jailexpert_gen.py:398-426` | ✅ | Both weights applied in scoring |
| Top-K Retrieval | Retrieve multiple experiences per cluster | `src/jbfoundry/attacks/generated/jailexpert_gen.py:677-706` | ✅ | `exp_idx` selects among `top_k` search results |
| Embedding/Index Caching | Reuse cached embeddings/index across runs | `src/jbfoundry/attacks/generated/jailexpert_gen.py:224-268` | ⚠️ | Caches embeddings only; clusters/index rebuilt each run |
| Mutation Engine Coverage | Mutation set from plan/reference | `src/jbfoundry/attacks/generated/jailexpert_gen.py:41-195` | ✅ | Implements Base64/Rot13/Leetspeak/Disemvowel + LLM-based, placeholders |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Experience Pool Path | experience_path | str | `attacks_paper_info/2508.19292/JailExpert/experience/experiences_examples.json` | ✅ | Resolved relative to project root |
| Embedding Model | embedding_model | str | `text-embedding-3-small` | ✅ | Used for litellm embeddings |
| Attack/Mutation Model | attack_model | str | `gpt-3.5-turbo` | ✅ | Passed into MutationEngine |
| Max Clusters | n_clusters | int | 10 | ✅ | Limits KMeans search |
| Top K | top_k | int | 1 | ✅ | Drives attempt mapping and search results |
| Scalar Weight | scalar_weight | float | 0.1 | ✅ | Applied in search scoring (additive) |
| Semantic Weight | semantic_weight | float | 0.9 | ✅ | Applied in search scoring (additive) |

## Misalignments / Missing Items
- **Caching incomplete**: Only embeddings are cached; clustering, centers, and assignments are recomputed each run, contrary to the plan/reference expectation to cache the full index for reuse (`src/jbfoundry/attacks/generated/jailexpert_gen.py:224-268,324-365`). Impacts performance and reproducibility across runs.
- **Search scoring deviates from plan/reference**: Retrieval score is `semantic_weight * cosine + scalar_weight * mean(harmfulness, success_rate)`, introducing harmfulness and additive mixing. Plan/reference use success-rate-weighted semantic similarity (cosine scaled by success rate), so ranking of experiences can differ (`src/jbfoundry/attacks/generated/jailexpert_gen.py:398-426`).

## Extra Behaviors Not in Paper
- Fallback synthetic experience when the JSON file is missing (`src/jbfoundry/attacks/generated/jailexpert_gen.py:547-571`).
- Hardcoded LiteLLM provider `"wenwen"` for both embedding and attack LLMs (`src/jbfoundry/attacks/generated/jailexpert_gen.py:522-529`).

## Required Changes to Reach 100%
- **Cache full index artifacts**: Persist and reload clustering outputs (centers, assignments, cluster_stats/patterns) keyed by `experience_path`, `embedding_model`, and `n_clusters` under `cache/jailexpert_gen/` to avoid recomputation and match the planned caching behavior (`src/jbfoundry/attacks/generated/jailexpert_gen.py:224-365`).
- **Align search scoring with plan/reference**: Replace additive scoring with success-rate–weighted semantic similarity (e.g., cosine(query, pre_query) scaled by success_rate, optionally modulated by scalar_weight/semantic_weight) and omit harmfulness unless justified by the paper (`src/jbfoundry/attacks/generated/jailexpert_gen.py:398-426`).

## Final Verdict
Not 100% Fidelity

## Previous Verdict (Iteration 1)
- Paper ID: 2508.19292
- Attack: jailexpert_gen
- Verdict: Not 100% Fidelity
- Coverage: 8/12 components (67%)
- Iteration: 1

## Executive Summary
The implementation follows the planned JailExpert flow—experience loading, semantic-drift clustering, representative pattern extraction, cluster ranking, and two-stage attempt sequencing are all present. However, key parameters from the plan are ineffectual (scalar_weight and semantic_weight are never applied), top_k retrieval is hard-coded to use only the single best experience, and no embedding/index caching is implemented despite the plan’s optimization requirement. These deviations leave parameter controls non-functional and miss the planned reuse efficiency, so fidelity is not yet 100%.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Experience Formalization | Load JSON into e = (I,J,A,s,f) | `src/jbfoundry/attacks/generated/jailexpert_gen.py:509–557` | ✅ | Parses mutation, method, pre/full query, success/failure with fallback |
| Semantic Drift Computation | Δ = Φ(J) – Φ(I) for experiences | `src/jbfoundry/attacks/generated/jailexpert_gen.py:224–259` | ✅ | Embeds pre/full queries and subtracts |
| Cluster Count Selection | Choose K via silhouette up to n_clusters | `src/jbfoundry/attacks/generated/jailexpert_gen.py:264–304` | ✅ | Iterates k with PCA+silhouette; handles small sets |
| Clustering & Centers | K-Means on drift vectors, store centers | `src/jbfoundry/attacks/generated/jailexpert_gen.py:296–335` | ✅ | Fits KMeans (or mean for single cluster) and records assignments |
| Representative Pattern Extraction | Most frequent/successful (mutation, template) per cluster | `src/jbfoundry/attacks/generated/jailexpert_gen.py:340–368` | ✅ | Counter + success-rate tie-break |
| Cluster Ranking | Sim((Φ(Rep(p))–Φ(p)), Center) ranking | `src/jbfoundry/attacks/generated/jailexpert_gen.py:569–609` | ✅ | Applies rep pattern, embeds, compares to centers |
| Attempt Sequencing | Map attempt_index to [(C1,REP),(C1,EXP),…] | `src/jbfoundry/attacks/generated/jailexpert_gen.py:634–651` | ✅ | Builds ordered actions and cycles on overflow |
| Representative Pattern Application | Apply cluster representative mutation+template | `src/jbfoundry/attacks/generated/jailexpert_gen.py:662–690` | ✅ | Applies mutations, template, placeholder strip |
| Experience Search Scoring | Search cluster by semantic+success weighting | `src/jbfoundry/attacks/generated/jailexpert_gen.py:370–397` | ⚠️ | Uses cosine * success_rate only; ignores scalar/semantic weights |
| Mutation Engine Coverage | Mutation set from plan/reference | `src/jbfoundry/attacks/generated/jailexpert_gen.py:41–195` | ✅ | Implements Base64/Rot13/Leetspeak/Disemvowel + LLM-based, placeholders |
| Parameter Weighting Controls | scalar_weight & semantic_weight affect search | `src/jbfoundry/attacks/generated/jailexpert_gen.py:455–468` | ❌ | Parameters stored but never used in scoring or clustering |
| Embedding/Index Caching | Reuse cached embeddings/index across runs | `src/jbfoundry/attacks/generated/jailexpert_gen.py:224–259` | ❌ | Always recomputes embeddings; no cache path or reuse |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Experience Pool Path | experience_path | str | `attacks_paper_info/2508.19292/JailExpert/experience/experiences_examples.json` | ✅ | Resolved relative to project root |
| Embedding Model | embedding_model | str | `text-embedding-3-small` | ✅ | Used for litellm embeddings |
| Attack/Mutation Model | attack_model | str | `gpt-3.5-turbo` | ✅ | Passed into MutationEngine |
| Max Clusters | n_clusters | int | 10 | ✅ | Limits KMeans search |
| Top K | top_k | int | 1 | ⚠️ | Search retrieves top_k but only first result is ever used |
| Scalar Weight | scalar_weight | float | 0.1 | ❌ | Parameter unused in search/scoring |
| Semantic Weight | semantic_weight | float | 0.9 | ❌ | Parameter unused in search/scoring |

## Misalignments / Missing Items
- **Unused weighting parameters** (`scalar_weight`, `semantic_weight`): Plan calls for weighting scalar vs semantic similarity, but scoring in `ExperienceIndex.search_within_cluster` uses only cosine similarity * success_rate; weights never applied anywhere (`jailexpert_gen.py:370–397`, `455–468`). Parameters are effectively no-ops.
- **Top-k experience retrieval not realized**: `top_k` is exposed but `_apply_best_experience` always returns `results[0]`, so additional candidates are never surfaced or mapped to attempts (`jailexpert_gen.py:692–724`). Plan intended retrieval of specific experiences per cluster.
- **No embedding/index caching**: Initialization recomputes embeddings for every experience on each instantiation and never checks or writes cache artifacts (`jailexpert_gen.py:224–259`). Plan specified caching if possible; current code misses any cache reuse under `cache/`.

## Extra Behaviors Not in Paper
- Fallback synthetic experience when the JSON file is missing (`jailexpert_gen.py:519–533`).
- Hardcoded LiteLLM provider `"wenwen"` for both embedding and attack LLMs (`jailexpert_gen.py:484–491`).
- Strips `{decryption_function}` placeholders when present (`jailexpert_gen.py:686–727`).

## Required Changes to Reach 100%
- **Apply scalar/semantic weighting**: Incorporate `scalar_weight` and `semantic_weight` into similarity scoring in `ExperienceIndex.search_within_cluster` and, if intended, cluster ranking; ensure parameters alter behavior (e.g., combine semantic cosine with scalar features per weights) (`jailexpert_gen.py:370–397`).
- **Honor top_k retrieval**: Use `top_k` to select which experience is used per attempt (e.g., map attempt_index over ranked experiences within a cluster) or iterate through top_k results instead of hardcoding `results[0]` (`jailexpert_gen.py:692–724`).
- **Add embedding/index caching**: Before recomputing embeddings in `_load_and_index_experiences`/`ExperienceIndex.build_index`, load cached embeddings/cluster data keyed by `experience_path`, `embedding_model`, and `n_clusters`; write back to `cache/jailexpert_gen/` after first build (`jailexpert_gen.py:224–259`).

## Final Verdict
Not 100% Fidelity

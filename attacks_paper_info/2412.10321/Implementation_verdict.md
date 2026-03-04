# Implementation Fidelity Verdict
- Paper ID: 2412.10321
- Attack: advprefix_gen
- Verdict: Not 100% Fidelity
- Coverage: 6/11 components (55%)
- Iteration: 1

## Executive Summary
The current `AdvPrefixAttack` implementation captures the high-level idea of using uncensored models to generate prefixes and scoring them with a combined PASR–NLL objective, but diverges significantly from both the paper and the official `jailbreak-objectives` repository in several core algorithmic details. Major gaps include using heuristic NLL instead of model-based cross-entropy, a simplified PASR evaluation with a single ad-hoc judge (and a heuristic fallback), missing key preprocessing and ablation steps, and lack of multi-model/guided prefix generation and selection controls. These deviations materially change the search space, ranking of prefixes, and the definition of PASR relative to the paper's objective, so the implementation cannot be considered a faithful reproduction of the AdvPrefix objective.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 AdvPrefix objective, candidate generation | Generate candidate prefixes from uncensored models with meta-prefixes and sampling | src/jbfoundry/attacks/generated/advprefix_gen.py:194–247 | ⚠️ | Uses an uncensored model with meta-prefix prompts and sampling, but only supports a single uncensored model and does not match the full multi-model, guided generation pipeline. |
| §3 AdvPrefix objective, multi-model & guided generation | Use multiple uncensored models and optional guided decoding with victim model (DualLLM) | src/jbfoundry/attacks/generated/advprefix_gen.py:194–247 | ❌ | Official pipeline loops over several uncensored models and includes guided decoding via `DualLLMGenerator`, while this implementation only queries a single uncensored model without guided decoding. |
| §3.1 Prefix preprocessing phase 1 | Filter prefixes by token length, refusal patterns, contain-patterns, linebreak requirement, and merge duplicates | src/jbfoundry/attacks/generated/advprefix_gen.py:249–296 | ⚠️ | Implements refusal-start filters and short-prefix removal plus duplicate elimination, but omits token-length-based filtering, linebreak requirements, and the full pattern sets used in the paper implementation. |
| §3.1 Prefix ablation | Ablate multi-line prefixes by truncating second line into multiple token segments | N/A | ❌ | The official `PrefixPreprocessor.ablate` step (preprocessor.py:261–279) is not represented; there is no ablation of multi-line prefixes into shorter variants. |
| §3.2 NLL estimation | Compute prefix negative log-likelihood via victim model cross-entropy using surrogate attack prompt | src/jbfoundry/attacks/generated/advprefix_gen.py:334–364 | ❌ | `_calculate_nll` uses a heuristic function based only on length and a small list of common starts, instead of computing cross-entropy with the victim model as in `PrefixCECalculator` (scorer_nll.py:17–141). |
| §3.2 CE-based filtering | Filter prefixes by NLL threshold and keep top `n_candidates_per_goal` per goal before PASR | src/jbfoundry/attacks/generated/advprefix_gen.py:298–332 | ❌ | All candidates are kept and only scored; there is no CE-based thresholding (`max_ce`) or top-k selection per goal as implemented in `filter_phase2` (preprocessor.py:243–259). |
| §3.3 PASR estimation | Estimate Prefilled Attack Success Rate using multiple completions of the victim model and nuanced-style judges | src/jbfoundry/attacks/generated/advprefix_gen.py:366–406,441–473 | ⚠️ | `_calculate_pasr` samples completions from a `target_llm` and uses `_is_harmful_response` with a nuanced-style judge prompt, but the judge differs from the paper's NuancedEvaluator and omits multi-judge support and the exact evaluation/aggregation pipeline. |
| §3.3 Multi-judge PASR and aggregation | Use multiple judges (`nuanced`, `jailbreakbench`, `harmbench`, `strongreject`) and aggregate PASR across them | src/jbfoundry/attacks/generated/advprefix_gen.py:366–406,441–473 | ❌ | The implementation only uses a single classifier-style judge and does not integrate multiple judges or their aggregation as in `scorer_pasr.py` and `PrefixSelector._calculate_combined_pasr` (selector.py:137–153). |
| §3.3 Combined objective | Use combined score `pasr_weight * log(PASR) - NLL` to rank prefixes | src/jbfoundry/attacks/generated/advprefix_gen.py:298–323,475–500 | ✅ | `_score_candidates` computes `combined_score = pasr_weight * log(pasr + 1e-6) - nll` and `_select_best_prefix` selects the prefix with the best (highest) combined score, which is equivalent to the repository's formulation up to sign conventions. |
| §3.3 Prefix selection strategy | Select up to `n_prefixes_per_goal` prefixes with PASR/NLL tolerances and sub-prefix removal | src/jbfoundry/attacks/generated/advprefix_gen.py:475–500 | ⚠️ | The code selects a single best prefix based on combined score and does not implement tolerances or multiple-prefix selection, but matches the top-1 part of the paper's selection rule. |
| §4 Attack construction | Construct final jailbreak prompt using selected prefixes and surrogate attack prompt/suffix | src/jbfoundry/attacks/generated/advprefix_gen.py:128–163 | ⚠️ | Returns `goal + " " + best_prefix`, which preserves the idea of prefilled prefixes but does not explicitly model the paper's surrogate-attack-prompt and suffix scheme (e.g., the `"! ! !"` pattern). |

## Parameter Mapping
| Paper Parameter (Config / Algorithm) | Code Parameter | Type | Default (Paper/Repo) | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| `uncensored_models` (PipelineConfig.uncensored_models) | `uncensored_model`, `uncensored_provider` | Tuple[str] vs str | 5 uncensored models (default_config.py:34–40) | ❌ | Paper implementation iterates over multiple uncensored models; this attack only supports a single uncensored model string and does not expose the list. |
| `meta_prefixes` (PipelineConfig.meta_prefixes) | `meta_prefixes` | Tuple[str] vs str | `("Here", "To", "Sure", "")` | ❌ | Code stores a comma-separated string `"Here,To,Sure,"` and drops the empty prefix; semantics and defaults are only approximately aligned. |
| `meta_prefix_samples` (PipelineConfig.meta_prefix_samples) | `n_candidates` | Tuple[int] vs int | `(50, 50, 50, 150)` | ❌ | Paper controls samples per meta-prefix; implementation only exposes a total `n_candidates` and splits evenly, losing the per-prefix weighting. |
| `batch_size` (PipelineConfig.batch_size) | None | int | `256` | ❌ | Batch size for generation/evaluation is not configurable in this attack (handled implicitly by API calls instead). |
| `max_new_tokens` (PipelineConfig.max_new_tokens) | `max_prefix_tokens` | int | `32` | ✅ | `max_prefix_tokens` directly controls the number of generated prefix tokens, matching the paper's `max_new_tokens`. |
| `temperature` (PipelineConfig.temperature) | `temperature` | float | `1.0` | ✅ | Default and semantics match: sampling temperature for prefix generation. |
| `min_token_length` (PreprocessConfig.min_token_length) | None | int | `24` (preprocessor.py:26) or `16` (PipelineConfig:50) | ❌ | Implementation uses a crude word-count (`<3` words) filter instead of token-length-based filtering; value and criterion differ. |
| `require_linebreak` (PreprocessConfig.require_linebreak) | None | bool | `True` | ❌ | Paper filters prefixes without internal linebreaks; this attack does not enforce any linebreak requirement. |
| `max_ce` (PreprocessConfig.max_ce / PipelineConfig.max_ce) | None | float | `1e6` (no effective limit by default) | ❌ | No CE-based thresholding is exposed or applied; NLL is heuristic and not comparable to CE values. |
| `min_lines` (PreprocessConfig.min_lines) | None | int | `2` | ❌ | Requirement for minimum non-empty lines is not implemented; the attack treats single-line and multi-line prefixes uniformly. |
| `max_token_segments` (PreprocessConfig.max_token_segments) | None | int | `5` | ❌ | The number of ablation segments for the second line is not present; ablation is not implemented. |
| `n_candidates_per_goal` (PreprocessConfig.n_candidates_per_goal / PipelineConfig.n_candidates_per_goal) | None | int | `100` | ❌ | There is no separate control for how many candidates per goal survive CE filtering; all candidates are scored directly. |
| `surrogate_attack_prompt` (PipelineConfig.surrogate_attack_prompt, SURROGATE_ATTACK_PROMPTS) | None | int / str | `0` (no suffix) | ❌ | The surrogate-attack-prompt index and associated strings are not modeled; attack construction uses a simple `goal + prefix` template instead. |
| `n_samples` (PipelineConfig.n_samples for PASR) | `n_pasr_samples` | int | `25` | ❌ | `n_pasr_samples` default is `5`, significantly fewer samples than the paper's `25`, changing PASR estimation and search control. |
| `max_new_tokens_completion` (PipelineConfig.max_new_tokens_completion) | None (hard-coded 100 in `_calculate_pasr`) | int | `512` | ❌ | Completion length for PASR evaluation is fixed at 100 tokens and not exposed as a parameter, diverging from the paper's longer 512-token completions. |
| `judges` (PipelineConfig.judges) | Implicit single judge via `_is_harmful_response` | Tuple[str] | `("nuanced",)` | ❌ | Paper supports several judges and passes them through config; implementation hardcodes a single nuanced-style judge and does not support multiple judges. |
| `filter_len` (PipelineConfig.filter_len) | None | int | `300` | ❌ | Length-based filtering of too-short responses before nuanced evaluation is absent. |
| `max_new_tokens_eval` (PipelineConfig.max_new_tokens_eval) | None (hard-coded `max_tokens=10` in `_is_harmful_response`) | int | `512` | ❌ | Judge generation length is fixed at 10 tokens, far shorter than in the paper's nuanced evaluation. |
| `batch_size_judge` (PipelineConfig.batch_size_judge) | None | int | `32` | ❌ | Judge batch size is not configurable (and is implicitly `1` in this implementation). |
| `selection_judges` (PipelineConfig.selection_judges) | None | Tuple[str] | `("nuanced",)` | ❌ | Paper lets users select which judge(s) define PASR in selection; implementation always uses its internal nuanced-style judge with no configurability. |
| `pasr_weight` (PipelineConfig.pasr_weight) | `pasr_weight` | float | `10.0` | ✅ | Parameter exists with matching name, type, and default, and is used in the combined score as specified. |
| `n_prefixes_per_goal` (PipelineConfig.n_prefixes_per_goal) | Implicitly fixed to 1 in `_select_best_prefix` | int | `1` | ❌ | Behavior matches top-1 selection but the parameter is not exposed; users cannot adjust the number of prefixes per goal as in the paper. |

## Misalignments / Missing Items
- **NLL computation deviates from model-based cross-entropy (Algorithm §3.2)**  
  - **Paper / repo behavior**: NLL is computed as cross-entropy loss of the prefix under the victim model, using chat templates and optional surrogate attack prompts (`PrefixCECalculator.calculate_ce`, scorer_nll.py:17–141; `SURROGATE_ATTACK_PROMPTS`, pipeline.py:47–51).  
  - **Code behavior**: `_calculate_nll` (src/jbfoundry/attacks/generated/advprefix_gen.py:334–364) uses a heuristic based on prefix length and whether it starts with a small list of common tokens, without querying the victim model or computing true likelihoods.  
  - **Impact**: The NLL term in the combined objective no longer reflects how natural the prefix is under the victim LLM, altering candidate ranking and potentially selecting prefixes the paper would discard; this is a major semantic deviation.

- **PASR evaluation and judges only loosely approximate the paper's nuanced objective (§2, §3.3)**  
  - **Paper / repo behavior**: PASR is estimated by generating many completions per prefix and scoring them with one or more judges (Nuanced, JailbreakBench, HarmBench, StrongReject), then aggregating judge scores per prefix (`NuancedEvaluator`, `JailbreakBenchEvaluator`, etc. in scorer_pasr.py:97–365; aggregation in pipeline.step8 and `PrefixSelector._calculate_combined_pasr`, selector.py:137–153).  
  - **Code behavior**: `_calculate_pasr` and `_is_harmful_response` (advprefix_gen.py:366–406,441–473) use a single lightweight judge model with a simplified prompt and very short generations, and fall back to a heuristic text-based PASR estimate (`_heuristic_pasr`, 408–439) when `target_llm` is not provided; no multi-judge integration or aggregation is implemented.  
  - **Impact**: The PASR estimates can differ substantially from the paper's nuanced evaluation, especially in edge cases, and the heuristic fallback has no grounding in the paper, leading to different objective values and selected prefixes.

- **Missing preprocessing and ablation pipeline (§3.1)**  
  - **Paper / repo behavior**: Prefixes undergo a two-phase preprocessing pipeline: length/start/contain-pattern filters, linebreak requirements, duplicate merging, and then ablation of multi-line prefixes into multiple truncated variants, followed by CE-based filtering and top-k selection per goal (preprocessor.py:134–259, pipeline.py:291–381).  
  - **Code behavior**: `_preprocess_candidates` (advprefix_gen.py:249–296) only filters obvious refusal starters, extremely short prefixes, and performs simple lexical augmentations; it does not enforce token-length or linebreak filters, does not use the full refusal pattern sets, and does not implement any ablation or CE-based candidate pruning.  
  - **Impact**: The candidate pool fed into NLL/PASR scoring is very different from the one described in the paper, both in composition and size, which can change which prefixes are even considered and how diverse they are.

- **Simplified candidate generation vs. full multi-model/guided scheme (§3, pipeline step 1)**  
  - **Paper / repo behavior**: Candidate prefixes are generated using both guided decoding (DualLLM with victim + uncensored models) and uncensored-only generation, across several uncensored models and meta-prefix/sample configurations (pipeline.py:142–263, default_config.py:32–47).  
  - **Code behavior**: `_generate_candidate_prefixes` (advprefix_gen.py:194–247) uses only a single uncensored model, no guided decoding with the victim model, and evenly splits `n_candidates` across meta-prefixes from a single string parameter.  
  - **Impact**: This reduces the diversity and coverage of the search over prefixes and omits the guided decoding path the paper highlights as part of the AdvPrefix objective, leading to potentially weaker or different prefixes than those intended.

- **Heuristic PASR fallback with no victim model or judges (§3.3)**  
  - **Paper / repo behavior**: PASR is always computed via actual model completions and judge evaluations; there is no heuristic PASR defined purely on the prefix text.  
  - **Code behavior**: When `target_llm` is not provided, `_calculate_pasr` returns `_heuristic_pasr(prefix)` (advprefix_gen.py:373–381,408–439), which scores prefixes based solely on the presence of certain affirmative/refusal words.  
  - **Impact**: In any integration path where `target_llm` is not plumbed through, prefix scoring is driven entirely by ad-hoc heuristics, which can diverge arbitrarily from the paper's PASR definition and severely affect fidelity.

- **Search-control and evaluation hyperparameters not aligned or not exposed (§3, §4)**  
  - **Paper / repo behavior**: Key search and evaluation hyperparameters such as `n_samples=25`, `max_new_tokens_completion=512`, `n_prefixes_per_goal`, `selection_judges`, and `n_candidates_per_goal` are explicitly configurable and documented (default_config.py:44–88).  
  - **Code behavior**: The attack uses `n_pasr_samples` default 5, fixes completion length for PASR at 100 tokens, always returns a single prefix, and does not expose knobs corresponding to `selection_judges` or `n_candidates_per_goal`.  
  - **Impact**: Users cannot reproduce the paper's experimental settings or adjust search control in the same way, and default behavior deviates from the reported configuration, which is a blocking issue for 100% fidelity.

- **Attack prompt construction differs from surrogate attack prompt mechanism (§4)**  
  - **Paper / repo behavior**: The surrogate attack prompt is controlled via discrete options (`SURROGATE_ATTACK_PROMPTS`, pipeline.py:47–51) and is used both in NLL/PASR estimation and final jailbreak execution (e.g., adding explicit suffix patterns like repeated `"!"`).  
  - **Code behavior**: `generate_attack` (advprefix_gen.py:128–163) constructs the final attack string as `goal + " " + best_prefix` without modeling the surrogate-attack-prompt choices or explicit suffix patterns.  
  - **Impact**: While the idea of prefilled prefixes is preserved, the exact prompt format and suffix behavior may differ from those used in the paper's experiments, potentially affecting jailbreak behavior and comparability.

## Extra Behaviors Not in Paper
- **Synthetic candidate prefixes fallback**: `_generate_synthetic_candidates` (advprefix_gen.py:165–192) injects a fixed list of affirmative templates when no candidates survive generation/filtering; the paper and official repository do not describe such a synthetic fallback.  
- **Heuristic PASR estimator without a target model**: `_heuristic_pasr` (advprefix_gen.py:408–439) estimates PASR from lexical patterns alone; this is not part of the published AdvPrefix objective.  
- **Custom lexical augmentations in preprocessing**: `_preprocess_candidates` adds variations like swapping `"Here is"` and `"Here's"` and removing leading `"To "` (advprefix_gen.py:285–293); the reference preprocessor instead uses token-level ablations and does not perform these particular string-level augmentations.  
- **Simplified single-judge classification prompt**: `_is_harmful_response` uses a shorter prompt and binary output labels `"VIOLATION"` / `"COMPLIANT"` (advprefix_gen.py:441–468), which differs from the more detailed, labeled nuanced judge prompt in the reference implementation (scorer_pasr.py:97–121).

## Required Changes to Reach 100%
- **Replace heuristic NLL with model-based cross-entropy**  
  - Implement `_calculate_nll` to query the victim model and compute cross-entropy over the prefix tokens, following `PrefixCECalculator.calculate_ce` (scorer_nll.py:72–141), and expose any necessary configuration (e.g., surrogate_attack_prompt) as attack parameters.  
  - Ensure the resulting NLL values are on the same scale as the paper (or explicitly documented) and use them consistently in the combined score and any CE-based filtering.

- **Align PASR estimation and judges with the paper**  
  - Modify `_calculate_pasr` to always sample `n_pasr_samples` completions from the target model with a default of 25, using a surrogate-attack prompt consistent with the paper, and route those completions through a nuanced-style judge that mirrors `NuancedEvaluator` (and, optionally, other judges).  
  - Remove or clearly gate the `_heuristic_pasr` fallback so that it is not used in standard AdvPrefix runs, and align the judge prompt and output labels with the paper's definition.

- **Implement full preprocessing and ablation pipeline (or a faithful equivalent)**  
  - Extend `_preprocess_candidates` to apply token-length filters, start/contain pattern filters, linebreak requirements, and duplicate merging similar to `PrefixPreprocessor.filter_phase1`, and add a separate ablation step that mirrors `PrefixPreprocessor.ablate`.  
  - After NLL computation, add CE-based filtering and per-goal top-k selection analogous to `filter_phase2`, controlled by attack parameters that correspond to `max_ce` and `n_candidates_per_goal`.

- **Expand candidate generation to support multi-model and guided decoding**  
  - Add parameters and logic to iterate over a list of uncensored models and, where possible, perform guided decoding using both the victim and uncensored models as in `PrefixGenerationPipeline.step1_generate_prefixes` (pipeline.py:142–263).  
  - Expose per-meta-prefix sample counts (or an equivalent control) so users can reproduce the `(50,50,50,150)` sampling distribution from the paper.

- **Expose and align search-control parameters and attack prompt formatting**  
  - Expose parameters corresponding to `n_prefixes_per_goal`, `selection_judges`, and completion/judge token limits, and set their defaults to match the paper's configuration.  
  - Update `generate_attack` to construct the final prompt using a surrogate-attack-prompt scheme equivalent to `SURROGATE_ATTACK_PROMPTS` (including the `"! ! !"`-style suffix where applicable), ensuring that the same format is used during both PASR estimation and final attack execution.

## Final Verdict
Given the heuristic NLL, simplified and partially heuristic PASR, missing preprocessing/ablation and CE-based selection, and several search-control and formatting discrepancies, the current implementation does **not** achieve exact fidelity to the AdvPrefix objective as defined in arXiv:2412.10321 and its reference repository. The overall verdict is **Not 100% Fidelity**.


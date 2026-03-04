## Audit Iteration 5 - 2025-12-26

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Default model and judge configuration diverge from reference PAIR defaults | ❌ Still Broken | ❌ Still Broken | Framework still defaults to `gpt-4o-mini` attacker/judge and `gpt-3.5-turbo` target via `LLMLiteLLM`, rather than Vicuna‑style attacker/target and GCG/JBB/Llama‑Guard judges used in the gold-standard repo; this iteration did not change those defaults (`pair_gen.py:57–69`, `pair_gen.py:134–147`, `pair_gen.py:171–231`). |
| Best‑prompt selection as API‑level extension beyond reference script | ⚠️ Still Equivalent | ⚠️ Still Equivalent | `generate_attack` continues to track and return the highest‑scoring prompt across all streams/iterations, whereas `JailbreakingLLMs/main.py` only logs prompts/responses and stops on score 10; this remains an intentional framework extension (`pair_gen.py:533–579`, `pair_gen.py:607–608`). |
| Judge score clamping deviates from reference behavior | ✅ Fixed | ✅ Fixed | `_score_response` still mirrors `JudgeBase.process_output` by extracting only the `[[X]]` pattern and returning the parsed integer directly, defaulting to 1 when parsing fails; no additional clamping or alternative formats have been introduced (`pair_gen.py:466–499`, `JailbreakingLLMs/judges.py:39–46`). |
| Early-stopping semantics differ from reference implementation (`>= success_threshold` vs `== 10`) | ⚠️ New Issue (Not 100% Fidelity) | ✅ Fixed | Early-stopping now uses strict equality `any(score == success_threshold for score in scores)` with `success_threshold` default 10, matching the reference behavior (which stops on `any(score == 10)`) even for out-of-range judge scores (`pair_gen.py:517`, `pair_gen.py:581–585`, `JailbreakingLLMs/main.py:69–71`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Attacker/target/judge role separation | ✅ | ✅ | Three distinct `LLMLiteLLM` instances for attacker, target, and judge are still constructed and used with clear roles, matching the reference repo’s separation of `attackLM`, `targetLM`, and `judgeLM` (`pair_gen.py:192–231`, `JailbreakingLLMs/main.py:22–25`). |
| System prompts and initial message | ✅ | ✅ | Attacker system prompts and `_get_init_message` remain effectively verbatim to `get_attacker_system_prompts`, `get_judge_system_prompt`, and `get_init_msg` in the gold repo (`pair_gen.py:235–383`, `pair_gen.py:384–392`, `JailbreakingLLMs/system_prompts.py:7–157`, `JailbreakingLLMs/common.py:43–47`). |
| Multi‑stream iterative loop and conversation truncation | ✅ | ✅ | The nested loop over `n_iterations` and `n_streams`, early stopping on a high judge score, and truncation via `keep_last_n` still align with `JailbreakingLLMs/main.py:33–71` (`pair_gen.py:539–605`). |
| JSON extraction for attacker output | ✅ | ✅ | `_extract_json` continues to slice from first `{` to first `}`, strip newlines, and parse with `ast.literal_eval`, matching `common.extract_json` up to logging differences (`pair_gen.py:400–438`, `JailbreakingLLMs/common.py:20–38`). |

**NEW Issues Found This Iteration:**
- None. No additional deviations were identified beyond the previously-known default model/judge configuration and best‑prompt API extension.

**Summary:**
- Fixed: 1 issue (early-stopping semantics)
- Partially Fixed: 0 issues
- Still Broken: 1 issue (default model/judge defaults)
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2310.08419
- Attack: pair_gen (PAIR - Prompt Automatic Iterative Refinement)
- Verdict: Not 100% Fidelity
- Coverage: 11/12 components (92%)
- Iteration: 5

## Executive Summary
The Iteration 5 audit confirms that the `PAIRAttack` implementation in `pair_gen.py` now matches the PAIR algorithm from *Jailbreaking Black Box Large Language Models in Twenty Queries* and the official `JailbreakingLLMs` repository in all algorithmic respects, including judge scoring and early-stopping semantics, which now use strict equality rather than a `>=` threshold. Core PAIR behavior—multi‑stream iterative refinement, attacker/target/judge role separation, system prompts, conversation history management with `keep_last_n`, and reproducibility via `pair_seed`—remains in one‑to‑one correspondence with the gold-standard code. The remaining discrepancies are confined to framework-specific default model/judge choices that differ from the reference defaults and the API-level decision to return the best‑scoring prompt, which changes how a single prompt is surfaced to downstream components but not the underlying search trajectory. Because these differences can still affect default configurations and surfaced outputs, the implementation remains **Not 100% Fidelity**, though it is now extremely close with only a small, well-characterized set of deviations.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 (Algorithm description), Plan §3–4 | Separate attacker, target, and judge LLM roles | `src/jbfoundry/attacks/generated/pair_gen.py:192–231` | ✅ | Three distinct `LLMLiteLLM` instances for attacker, target, and judge mirror the roles and separation in `JailbreakingLLMs/main.py:22–25`. |
| §3, Plan §4 | Inputs K (iterations), N (streams), O (objective), target string; conversation history C | `pair_gen.py:35–61`, `pair_gen.py:501–535` | ✅ | `n_iterations`, `n_streams`, `keep_last_n`, and the `goal`/`target` arguments with per-stream `conversation_histories` implement the blueprint’s inputs and conversation history, analogous to `initialize_conversations` and the main PAIR loop. |
| §3, Plan §4–5 | Attacker system prompts: roleplaying, logical appeal, authority endorsement | `pair_gen.py:235–383` | ✅ | The three system prompts closely match `roleplaying_prompt`, `logical_appeal_prompt`, and `authority_endorsement_prompt` in `JailbreakingLLMs/system_prompts.py:7–150`. |
| §3, Plan §4–5 | Initial attacker message summarizing objective and target prefix | `pair_gen.py:390–392` | ✅ | `_get_init_message` matches `common.get_init_msg` (`JailbreakingLLMs/common.py:43–44`), using the same bolded objective and “Begin.” phrasing. |
| §3, Plan §4 | Conversation history update with target response and score | `pair_gen.py:394–398`, `pair_gen.py:587–598` | ✅ | `_process_target_response` and the per-stream feedback updates align with `process_target_response` and the main loop’s use of processed responses, appending formatted LANGUAGE MODEL OUTPUT / OBJECTIVE / SCORE strings. |
| §3, Plan §4 | Multi-stream, multi-iteration search with breadth/depth trade-off (N streams, K iterations) | `pair_gen.py:539–605` | ✅ | The outer loop over `n_iterations` and inner loop over `n_streams`, plus early stopping when any stream’s score equals the success threshold and history truncation via `keep_last_n`, faithfully reproduce the PAIR search pattern from `JailbreakingLLMs/main.py:33–71`. |
| §3, Plan §6 | JUDGE function scoring 1–10 and success threshold \(t\) | `pair_gen.py:384–388`, `pair_gen.py:466–499`, `pair_gen.py:514–518`, `pair_gen.py:581–585` | ✅ | Judge system prompt and `[[X]]` parsing now exactly match `get_judge_system_prompt` and `JudgeBase.process_output`, and success is controlled by a parameterized `success_threshold` defaulting to 10 while using strict equality for early stopping, matching the reference semantics. |
| §3, Plan §4–5 | Attacker JSON output (`improvement`, `prompt`) and retry on malformed outputs | `pair_gen.py:400–438`, `pair_gen.py:440–464` | ✅ | `_extract_json` and `_generate_attack_prompt` parallel `common.extract_json` and the retry loop in the reference attacker, including up to `max_attack_attempts` retries and requiring both `improvement` and `prompt` keys. |
| §3, Plan §7 | Attacker decoding: temperature \(T = 1\), top-p \(p = 0.9\), max tokens | `pair_gen.py:71–90`, `pair_gen.py:192–205` | ✅ | `attack_temperature`, `attack_max_tokens`, and `attack_top_p` (default 0.9) are passed into the attacker LLM config, consistent with PAIR’s decoding settings and the reference repo’s `ATTACK_TEMP`/`ATTACK_TOP_P`. |
| §3, Plan §7 | Target decoding: temperature \(T = 0\), response length \(L = 150\) | `pair_gen.py:127–133`, `pair_gen.py:207–218` | ✅ | `target_temperature=0.0` and `target_max_tokens=150` are used for the target model, matching the blueprint and `JailbreakingLLMs/main.py:110–113`. |
| §3, Plan §4 | Using best-scoring prompt as final attack output | `pair_gen.py:533–579`, `pair_gen.py:607–608` | ⚠️ | Tracking `best_prompt` and returning it at the end is a reasonable extension of the algorithmic intent but differs from the reference script, which only logs prompts/responses rather than surfacing a single “best” prompt programmatically. |
| Plan §9 (Additional Considerations) | Determinism via fixed seeds for reproducibility | `pair_gen.py:155–161`, `pair_gen.py:192–231` | ✅ | A `pair_seed` parameter with default 0 is propagated into all three `LLMLiteLLM` instances as `seed`, preserving deterministic behavior across runs when models and parameters are held fixed. |

## Parameter Mapping
| Paper / Repo Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| \(K\) – max iterations (§3, Plan §4) | `n_iterations` (`PAIRAttack.PARAMETERS`) | int | 3 | ✅ | Matches `--n-iterations` default in `JailbreakingLLMs/main.py:165–169`. |
| \(N\) – number of streams (§3, Plan §4, README) | `n_streams` | int | 3 | ✅ | Same default as `--n-streams` in the reference script (though experiments often use more streams). |
| \(O\) – objective / behavior (§3, Plan §3–4) | `goal` argument to `generate_attack` | str | (required) | ✅ | Passed into attacker and judge prompts exactly as in `get_init_msg` and `get_attacker_system_prompts`. |
| Target prefix string (§3, Plan §3–4) | `target` argument to `generate_attack` | str | (required) | ✅ | Used as `target_str` in attacker and judge templates, matching `main.py:171–180` and `system_prompts.py`. |
| Threshold \(t\) for success (§3, Plan §4) | `success_threshold` | int | 10 | ✅ | Exposed as an `AttackParameter` with default equal to the reference’s implicit threshold and used with strict equality in the stopping condition, matching the gold-standard semantics while allowing configurable thresholds as an extension. |
| Attacker temperature \(T\) (§3, Plan §7; `config.ATTACK_TEMP`) | `attack_temperature` | float | 1.0 | ✅ | Forwarded to the attacker LLM, matching `ATTACK_TEMP = 1`. |
| Attacker top-p \(p\) (§3, Plan §7; `config.ATTACK_TOP_P`) | `attack_top_p` | float | 0.9 | ✅ | Forwarded as `top_p` to the attacker LLM, implementing PAIR’s top-p sampling setting. |
| Attacker max tokens \(L_\text{attack}\) (§3, Plan §7; `--attack-max-n-tokens`) | `attack_max_tokens` | int | 500 | ✅ | Used for attacker generation length, consistent with the reference default. |
| Max attack attempts (`--max-n-attack-attempts`) | `max_attack_attempts` | int | 5 | ✅ | Controls the retry loop in `_generate_attack_prompt`, analogous to `max-n-attack-attempts` in the original script. |
| Target model name (`--target-model`) | `target_model` | str | `"gpt-3.5-turbo"` | ❌ | Semantic role matches the paper and repo, but the default differs from `"vicuna-13b-v1.5"` used in `JailbreakingLLMs/main.py:104–108`. |
| Target max tokens \(L\) (§3, Plan §7; `--target-max-n-tokens`) | `target_max_tokens` | int | 150 | ✅ | Used as the target generation length, matching the reference default and blueprint. |
| Target temperature \(T_\text{target}\) (`config.TARGET_TEMP`) | `target_temperature` | float | 0.0 | ✅ | Passed into the target LLM config, consistent with `TARGET_TEMP = 0`. |
| Judge model choice (`--judge-model`) | `judge_model` | str | `"gpt-4o-mini"` | ❌ | Role corresponds to the paper’s judge, but the default and implementation (always an LLM judge via `LLMLiteLLM`) differ from the `gcg` / JailbreakBench / Llama-Guard options in the reference repo. |
| Judge max tokens (`--judge-max-n-tokens`) | `judge_max_tokens` | int | 10 | ✅ | Used as the judge generation length, as in `JailbreakingLLMs/main.py:137–140`. |
| Judge temperature (`--judge-temperature`) | `judge_temperature` | float | 0.0 | ✅ | Matches the reference default for temperature. |
| Conversation history length (`--keep-last-n`) | `keep_last_n` | int | 4 | ✅ | Used to truncate per-stream histories at `2 * keep_last_n` messages, matching `main.py:64–66`. |
| Random seed for reproducibility (Plan §9) | `pair_seed` | int | 0 | ✅ | Propagated as `seed` into all three `LLMLiteLLM` instances, aligning with the paper’s reproducibility recommendation and the reference repo’s deterministic configuration. |

## Misalignments / Missing Items
1. **Framework default model and judge configuration still diverge from the reference PAIR setup.**  
   - **Paper / Repo expectation:** The gold-standard repository defaults to Vicuna/Llama-family models and uses GCG/JailbreakBench/Llama-Guard-style judges (`JailbreakingLLMs/config.py`, `main.py:80–88`, `main.py:103–108`, `judges.load_judge`).  
   - **Observed behavior:** `PAIRAttack` defaults to `"gpt-4o-mini"` for attacker and judge and `"gpt-3.5-turbo"` for the target from provider `"wenwen"`, always using an LLM-based judge via `LLMLiteLLM` instead of `judges.py` abstractions (`pair_gen.py:57–69`, `pair_gen.py:134–147`, `pair_gen.py:221–231`).  
   - **Impact:** Algorithmic structure and parameterization are preserved, but out-of-the-box runs do not replicate the exact model/judge combinations used in the paper and its reference implementation; reproducing reported results still requires explicit reconfiguration.

2. **Best-prompt selection remains an API-level extension relative to the reference script.**  
   - **Paper / Repo expectation:** The PAIR script performs a search and stops when a jailbreak is found, logging prompts/responses/scores but not returning a designated “best” prompt (`JailbreakingLLMs/main.py:33–71`).  
   - **Observed behavior:** `generate_attack` tracks `best_prompt` and `best_score` across all streams and iterations and always returns the highest-scoring prompt even if no perfect (score 10) jailbreak is found (`pair_gen.py:533–579`, `pair_gen.py:607–608`).  
   - **Impact:** This is a reasonable design for the jbfoundry framework and aligns with the algorithm’s intent, but it remains an observable behavioral difference relative to the original script and may change which prompt is surfaced downstream in borderline cases.

## Extra Behaviors Not in Paper
- **Framework integration via `ModernBaseAttack` and `LLMLiteLLM`.**  
  The attack is embedded into the jbfoundry framework with configuration via `AttackParameter` objects and `LLMLiteLLM.from_config`, rather than using the original `APILiteLLM`/FastChat/JailbreakBench stack. This structural adaptation is necessary for this codebase but goes beyond the paper’s presentation.

- **Richer logging and explicit reporting of best scores.**  
  The implementation logs model choices, iteration progress, and discovery of new best prompts (`pair_gen.py:233`, `pair_gen.py:537–579`), providing additional debugging information not described in the paper.

## Required Changes to Reach 100%
1. **Align default model and judge choices with the reference PAIR configuration or continue to emphasize divergences.**  
   - **File / Lines:** `src/jbfoundry/attacks/generated/pair_gen.py:57–69`, `pair_gen.py:134–147`, `pair_gen.py:221–231`.  
   - **Change:** Either (a) change the default `attack_model`, `target_model`, and `judge_model` to match the reference repo’s defaults (e.g., Vicuna-13b-v1.5 attacker/target and `gcg`/JBB/Llama-Guard judges), or (b) accept that runs using framework defaults are not meant to reproduce the paper’s default configuration and treat this as an intentional but documented deviation.  
   - **Justification:** Ensures that typical, unmodified runs align more closely with the models and judges used in the original experiments, or that the divergence is clearly framed as a deliberate choice.

2. **Optionally, align or parameterize the “best-prompt” API with the reference script.**  
   - **File / Lines:** `src/jbfoundry/attacks/generated/pair_gen.py:533–579`, `pair_gen.py:607–608`.  
   - **Change:** Either (a) document clearly that returning `best_prompt` is a framework extension and leave behavior as-is, or (b) add an option to return the last or any successful prompt in a way that can exactly reproduce the logging-only behavior of `JailbreakingLLMs/main.py`.  
   - **Justification:** While not strictly required for algorithmic fidelity, making this difference explicit or configurable would remove the remaining substantive behavioral discrepancy besides model/judge defaults.

## Final Verdict
The Iteration 5 audit verifies that PAIR’s algorithmic core in this framework is now fully aligned with the paper and the `JailbreakingLLMs` codebase, including judge-scoring and early-stopping behavior. The remaining gaps concern framework-specific default model/judge choices and an API-level decision to return the best-scoring prompt, which can influence default runs and surfaced outputs but do not alter the underlying search procedure. Because these differences can still affect behavior in practical use, the implementation remains **Not 100% Fidelity**, albeit with only two well-understood deviations separating it from full fidelity.

---

## Audit Iteration 4 - 2025-12-26

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Default model and judge configuration diverge from reference PAIR defaults | ❌ Still Broken | ❌ Still Broken | Framework still defaults to `gpt-4o-mini` attacker/judge and `gpt-3.5-turbo` target via `LLMLiteLLM`, rather than Vicuna‑style attacker/target and GCG/JBB/Llama‑Guard judges used in the gold-standard repo; the new docstring in `__init__` clarifies how to reproduce the paper setup but does not change out‑of‑the‑box behavior (`pair_gen.py:57–69`, `pair_gen.py:134–147`, `pair_gen.py:171–186`). |
| Best‑prompt selection as API‑level extension beyond reference script | ⚠️ Still Equivalent | ⚠️ Still Equivalent | `generate_attack` continues to track and return the highest‑scoring prompt across all streams/iterations, whereas `JailbreakingLLMs/main.py` only logs prompts/responses and stops on score 10; this remains an intentional framework extension (`pair_gen.py:533–579`, `pair_gen.py:605–607`). |
| Judge score clamping deviates from reference behavior | ❌ Noted as New Issue | ✅ Fixed | `_score_response` now mirrors `JudgeBase.process_output` by extracting only the `[[X]]` pattern and returning the parsed integer directly, defaulting to 1 when parsing fails; previous clamping into \[1,10\] has been removed (`pair_gen.py:466–499`, `JailbreakingLLMs/judges.py:39–46`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Attacker/target/judge role separation | ✅ | ✅ | Three distinct `LLMLiteLLM` instances for attacker, target, and judge are still constructed and used with clear roles, matching the reference repo’s separation of `attackLM`, `targetLM`, and `judgeLM` (`pair_gen.py:193–231`, `JailbreakingLLMs/main.py:22–25`). |
| System prompts and initial message | ✅ | ✅ | Attacker system prompts and `_get_init_message` remain effectively verbatim to `get_attacker_system_prompts`, `get_judge_system_prompt`, and `get_init_msg` in the gold repo (`pair_gen.py:235–383`, `pair_gen.py:384–392`, `JailbreakingLLMs/system_prompts.py:7–157`, `JailbreakingLLMs/common.py:43–47`). |
| Multi‑stream iterative loop and conversation truncation | ✅ | ✅ | The nested loop over `n_iterations` and `n_streams`, early stopping on a high judge score, and truncation via `keep_last_n` still align with `JailbreakingLLMs/main.py:33–71` (`pair_gen.py:538–604`). |
| JSON extraction for attacker output | ✅ | ✅ | `_extract_json` continues to slice from first `{` to first `}`, strip newlines, and parse with `ast.literal_eval`, matching `common.extract_json` up to logging differences (`pair_gen.py:400–438`, `JailbreakingLLMs/common.py:20–38`). |
| Reproducibility via fixed random seeds | ✅ | ✅ | `pair_seed` is still propagated as `seed` into attacker, target, and judge `LLMLiteLLM` instances, preserving deterministic behavior across runs when configured identically (`pair_gen.py:155–161`, `pair_gen.py:193–231`). |

**NEW Issues Found This Iteration:**
- **Early-stopping condition uses `>= success_threshold` instead of strict equality.** The reference script terminates when any judge score is exactly 10 (`any(score == 10)` in `JailbreakingLLMs/main.py:69–71`), while this implementation stops when any score is greater than or equal to the configurable `success_threshold` (default 10) (`pair_gen.py:516–517`, `pair_gen.py:580–583`). For well‑formed judge outputs in \[1,10\], behavior is identical; however, if a judge ever emits a rating above 10 (e.g., `[[15]]`), the original code would **not** stop early whereas this implementation would, creating a subtle difference in search dynamics for malformed but parseable judge outputs.

**Summary:**
- Fixed: 1 issue (judge score clamping)
- Partially Fixed: 0 issues
- Still Broken: 1 issue (default model/judge defaults)
- Regressions: 0 issues
- New Issues: 1 issue (early‑stopping `>=` vs `==` threshold behavior)

# Implementation Fidelity Verdict
- Paper ID: 2310.08419
- Attack: pair_gen (PAIR - Prompt Automatic Iterative Refinement)
- Verdict: Not 100% Fidelity
- Coverage: 10/12 components (83%)
- Iteration: 4

## Executive Summary
The Iteration 4 audit confirms that the `PAIRAttack` implementation in `pair_gen.py` remains extremely close to both the PAIR algorithm from *Jailbreaking Black Box Large Language Models in Twenty Queries* and the official `JailbreakingLLMs` repository, preserving all previously verified fixes and now resolving the judge-score clamping deviation so that `_score_response` matches `JudgeBase.process_output`. Core PAIR behavior—including multi‑stream iterative refinement, attacker/target/judge role separation, system prompts, conversation history management with `keep_last_n`, and reproducibility via `pair_seed`—continues to align one‑to‑one with the gold-standard code. The remaining discrepancies are: (a) framework-specific default model/judge choices that differ from the reference defaults, (b) the decision to return the best‑scoring prompt as an API extension, and (c) a very minor deviation in the early‑stopping condition, which uses `>= success_threshold` rather than `== 10` and only diverges in the presence of out‑of‑range judge scores. These issues are narrow and largely confined to defaults and edge cases, but they still preclude a 100% fidelity verdict.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 (Algorithm description), Plan §3–4 | Separate attacker, target, and judge LLM roles | `src/jbfoundry/attacks/generated/pair_gen.py:193–231` | ✅ | Three distinct `LLMLiteLLM` instances for attacker, target, and judge mirror the roles and separation in `JailbreakingLLMs/main.py:22–25`. |
| §3, Plan §4 | Inputs K (iterations), N (streams), O (objective), target string; conversation history C | `pair_gen.py:35–61`, `pair_gen.py:500–535` | ✅ | `n_iterations`, `n_streams`, `keep_last_n`, and the `goal`/`target` arguments with per-stream `conversation_histories` implement the blueprint’s inputs and conversation history, analogous to `initialize_conversations` and the main PAIR loop. |
| §3, Plan §4–5 | Attacker system prompts: roleplaying, logical appeal, authority endorsement | `pair_gen.py:235–383` | ✅ | The three system prompts closely match `roleplaying_prompt`, `logical_appeal_prompt`, and `authority_endorsement_prompt` in `JailbreakingLLMs/system_prompts.py:7–150`. |
| §3, Plan §4–5 | Initial attacker message summarizing objective and target prefix | `pair_gen.py:390–392` | ✅ | `_get_init_message` matches `common.get_init_msg` (`JailbreakingLLMs/common.py:43–44`), using the same bolded objective and “Begin.” phrasing. |
| §3, Plan §4 | Conversation history update with target response and score | `pair_gen.py:394–398`, `pair_gen.py:585–596` | ✅ | `_process_target_response` and the per-stream feedback updates align with `process_target_response` and the main loop’s use of processed responses, appending formatted LANGUAGE MODEL OUTPUT / OBJECTIVE / SCORE strings. |
| §3, Plan §4 | Multi-stream, multi-iteration search with breadth/depth trade-off (N streams, K iterations) | `pair_gen.py:538–604` | ✅ | The outer loop over `n_iterations` and inner loop over `n_streams`, plus early stopping when any stream’s score crosses the success threshold and history truncation via `keep_last_n`, faithfully reproduce the PAIR search pattern from `JailbreakingLLMs/main.py:33–71`. |
| §3, Plan §6 | JUDGE function scoring 1–10 and success threshold \(t\) | `pair_gen.py:384–388`, `pair_gen.py:466–499`, `pair_gen.py:516–517`, `pair_gen.py:580–583` | ⚠️ | Judge system prompt and `[[X]]` parsing now exactly match `get_judge_system_prompt` and `JudgeBase.process_output`, and success is controlled by a parameterized `success_threshold` defaulting to 10 (the reference’s effective threshold). However, this implementation stops when any `score >= success_threshold`, while the original code uses `score == 10`, leading to slightly different behavior only if the judge outputs out-of-range ratings above 10. |
| §3, Plan §4–5 | Attacker JSON output (`improvement`, `prompt`) and retry on malformed outputs | `pair_gen.py:400–438`, `pair_gen.py:440–464` | ✅ | `_extract_json` and `_generate_attack_prompt` parallel `common.extract_json` and the retry loop in the reference attacker, including up to `max_attack_attempts` retries and requiring both `improvement` and `prompt` keys. |
| §3, Plan §7 | Attacker decoding: temperature \(T = 1\), top-p \(p = 0.9\), max tokens | `pair_gen.py:71–90`, `pair_gen.py:193–205` | ✅ | `attack_temperature`, `attack_max_tokens`, and `attack_top_p` (default 0.9) are passed into the attacker LLM config, consistent with PAIR’s decoding settings and the reference repo’s `ATTACK_TEMP`/`ATTACK_TOP_P`. |
| §3, Plan §7 | Target decoding: temperature \(T = 0\), response length \(L = 150\) | `pair_gen.py:127–133`, `pair_gen.py:207–218` | ✅ | `target_temperature=0.0` and `target_max_tokens=150` are used for the target model, matching the blueprint and `JailbreakingLLMs/main.py:110–113`. |
| §3, Plan §4 | Using best-scoring prompt as final attack output | `pair_gen.py:533–579`, `pair_gen.py:605–607` | ⚠️ | Tracking `best_prompt` and returning it at the end is a reasonable extension of the algorithmic intent but differs from the reference script, which only logs prompts/responses rather than surfacing a single “best” prompt programmatically. |
| Plan §9 (Additional Considerations) | Determinism via fixed seeds for reproducibility | `pair_gen.py:155–161`, `pair_gen.py:193–231` | ✅ | A `pair_seed` parameter with default 0 is propagated into all three `LLMLiteLLM` instances as `seed`, matching the paper’s reproducibility recommendation and the reference repository’s deterministic design. |

## Parameter Mapping
| Paper / Repo Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| \(K\) – max iterations (§3, Plan §4) | `n_iterations` (`PAIRAttack.PARAMETERS`) | int | 3 | ✅ | Matches `--n-iterations` default in `JailbreakingLLMs/main.py:165–169`. |
| \(N\) – number of streams (§3, Plan §4, README) | `n_streams` | int | 3 | ✅ | Same default as `--n-streams` in the reference script (though experiments often use 20–30 streams). |
| \(O\) – objective / behavior (§3, Plan §3–4) | `goal` argument to `generate_attack` | str | (required) | ✅ | Passed into attacker and judge prompts exactly as in `get_init_msg` and `get_attacker_system_prompts`. |
| Target prefix string (§3, Plan §3–4) | `target` argument to `generate_attack` | str | (required) | ✅ | Used as `target_str` in attacker and judge templates, matching `main.py:171–180` and `system_prompts.py`. |
| Threshold \(t\) for success (§3, Plan §4) | `success_threshold` | int | 10 | ⚠️ | Exposed as an `AttackParameter` with default equal to the reference’s implicit threshold (`score == 10`) and used in the stopping condition; behavior is identical for scores in \[1,10\], but using `>= success_threshold` instead of `== 10` changes behavior if a judge ever outputs ratings above 10. |
| Attacker temperature \(T\) (§3, Plan §7; `config.ATTACK_TEMP`) | `attack_temperature` | float | 1.0 | ✅ | Forwarded to the attacker LLM, matching `ATTACK_TEMP = 1`. |
| Attacker top-p \(p\) (§3, Plan §7; `config.ATTACK_TOP_P`) | `attack_top_p` | float | 0.9 | ✅ | Forwarded as `top_p` to the attacker LLM, implementing PAIR’s top-p sampling setting. |
| Attacker max tokens \(L_\text{attack}\) (§3, Plan §7; `--attack-max-n-tokens`) | `attack_max_tokens` | int | 500 | ✅ | Used for attacker generation length, consistent with the reference default. |
| Max attack attempts (`--max-n-attack-attempts`) | `max_attack_attempts` | int | 5 | ✅ | Controls the retry loop in `_generate_attack_prompt`, analogous to `max-n-attack-attempts` in the original script. |
| Target model name (`--target-model`) | `target_model` | str | `"gpt-3.5-turbo"` | ❌ | Semantic role matches the paper and repo, but the default differs from `"vicuna-13b-v1.5"` used in `JailbreakingLLMs/main.py:104–108`. |
| Target max tokens \(L\) (§3, Plan §7; `--target-max-n-tokens`) | `target_max_tokens` | int | 150 | ✅ | Used as the target generation length, matching the reference default and blueprint. |
| Target temperature \(T_\text{target}\) (`config.TARGET_TEMP`) | `target_temperature` | float | 0.0 | ✅ | Passed into the target LLM config, consistent with `TARGET_TEMP = 0`. |
| Judge model choice (`--judge-model`) | `judge_model` | str | `"gpt-4o-mini"` | ❌ | Role corresponds to the paper’s judge, but the default and implementation (always an LLM judge via `LLMLiteLLM`) differ from the `gcg` / JailbreakBench / Llama-Guard options in the reference repo. |
| Judge max tokens (`--judge-max-n-tokens`) | `judge_max_tokens` | int | 10 | ✅ | Used as the judge generation length, as in `JailbreakingLLMs/main.py:137–140`. |
| Judge temperature (`--judge-temperature`) | `judge_temperature` | float | 0.0 | ✅ | Matches the reference default for temperature. |
| Conversation history length (`--keep-last-n`) | `keep_last_n` | int | 4 | ✅ | Used to truncate per-stream histories at `2 * keep_last_n` messages, matching `main.py:64–66`. |
| Random seed for reproducibility (Plan §9) | `pair_seed` | int | 0 | ✅ | Propagated as `seed` into all three `LLMLiteLLM` instances, aligning with the paper’s reproducibility recommendation and the reference repo’s deterministic configuration. |

## Misalignments / Missing Items
1. **Framework default model and judge configuration still diverge from the reference PAIR setup.**  
   - **Paper / Repo expectation:** The gold-standard repository defaults to Vicuna/Llama-family models and uses GCG/JailbreakBench/Llama-Guard-style judges (`JailbreakingLLMs/config.py`, `main.py:80–88`, `main.py:103–108`, `judges.load_judge`).  
   - **Observed behavior:** `PAIRAttack` defaults to `"gpt-4o-mini"` for attacker and judge and `"gpt-3.5-turbo"` for the target from provider `"wenwen"`, always using an LLM-based judge via `LLMLiteLLM` instead of `judges.py` abstractions (`pair_gen.py:57–69`, `pair_gen.py:134–147`, `pair_gen.py:221–231`). The new `__init__` docstring documents how to configure Vicuna and Llama‑Guard‑style setups but leaves the defaults unchanged.  
   - **Impact:** Algorithmic structure and parameterization are preserved, but out-of-the-box runs do not replicate the exact model/judge combinations used in the paper and its reference implementation; reproducing reported results still requires explicit reconfiguration.

2. **Early-stopping semantics differ slightly from the reference implementation.**  
   - **Paper / Repo expectation:** The judge is instructed to output ratings between 1 and 10, and the reference script stops when any score equals 10 (`any(score == 10)`), after `JudgeBase.process_output` has extracted the integer from `[[X]]` without further modification (`JailbreakingLLMs/judges.py:39–46`, `JailbreakingLLMs/main.py:69–71`).  
   - **Observed behavior:** `_score_response` now matches `process_output` exactly, but `generate_attack` treats any score greater than or equal to `success_threshold` (default 10) as sufficient for early stopping (`pair_gen.py:516–517`, `pair_gen.py:580–583`). Thus, if a judge ever emits a rating above 10 (e.g., `[[15]]`), this implementation will regard it as a successful jailbreak while the reference code would not.  
   - **Impact:** For all intended judge outputs in the range 1–10, behavior is identical; deviations only arise for malformed but parseable scores above 10, making this a rare but real semantic difference in edge-case search dynamics.

3. **Best-prompt selection remains an API-level extension relative to the reference script.**  
   - **Paper / Repo expectation:** The PAIR script performs a search and stops when a jailbreak is found, logging prompts/responses/scores but not returning a designated “best” prompt (`JailbreakingLLMs/main.py:33–71`).  
   - **Observed behavior:** `generate_attack` tracks `best_prompt` and `best_score` across all streams and iterations and always returns the highest-scoring prompt even if no perfect (score 10) jailbreak is found (`pair_gen.py:533–579`, `pair_gen.py:605–607`).  
   - **Impact:** This is a reasonable design for the jbfoundry framework and aligns with the algorithm’s intent, but it remains an observable behavioral difference relative to the original script and may change which prompt is surfaced downstream in borderline cases.

## Extra Behaviors Not in Paper
- **Framework integration via `ModernBaseAttack` and `LLMLiteLLM`.**  
  The attack is embedded into the jbfoundry framework with configuration via `AttackParameter` objects and `LLMLiteLLM.from_config`, rather than using the original `APILiteLLM`/FastChat/JailbreakBench stack. This structural adaptation is necessary for this codebase but goes beyond the paper’s presentation.

- **Richer logging and explicit reporting of best scores.**  
  The implementation logs model choices, iteration progress, and discovery of new best prompts (`pair_gen.py:233–233`, `pair_gen.py:536–579`), providing additional debugging information not described in the paper.

## Required Changes to Reach 100%
1. **Align default model and judge choices with the reference PAIR configuration or continue to emphasize divergences.**  
   - **File / Lines:** `src/jbfoundry/attacks/generated/pair_gen.py:57–69`, `pair_gen.py:134–147`, `pair_gen.py:221–231`.  
   - **Change:** Either (a) change the default `attack_model`, `target_model`, and `judge_model` to match the reference repo’s defaults (e.g., Vicuna-13b-v1.5 attacker/target and `gcg`/JBB/Llama-Guard judges), or (b) accept that runs using framework defaults are not meant to reproduce the paper’s default configuration and treat this as an intentional but documented deviation.  
   - **Justification:** Ensures that typical, unmodified runs align more closely with the models and judges used in the original experiments, or that the divergence is clearly framed as a deliberate choice.

2. **Match early-stopping semantics to the reference script, or gate the difference behind a configuration flag.**  
   - **File / Lines:** `src/jbfoundry/attacks/generated/pair_gen.py:516–517`, `pair_gen.py:580–583`.  
   - **Change:** To achieve exact behavioral parity, change the stopping condition from `any(score >= success_threshold for score in scores)` to `any(score == success_threshold for score in scores)` when `success_threshold` retains its default of 10, or introduce a configuration option that allows switching between equality-based and threshold-based stopping while defaulting to the reference semantics.  
   - **Justification:** Restores strict equivalence with the gold-standard early-stopping behavior, including edge cases where the judge accidentally emits ratings outside the intended 1–10 range.

3. **Optionally, align or parameterize the “best-prompt” API with the reference script.**  
   - **File / Lines:** `src/jbfoundry/attacks/generated/pair_gen.py:533–579`, `pair_gen.py:605–607`.  
   - **Change:** Either (a) document clearly that returning `best_prompt` is a framework extension and leave behavior as-is, or (b) add an option to return the last or any successful prompt in a way that can exactly reproduce the logging-only behavior of `JailbreakingLLMs/main.py`.  
   - **Justification:** While not strictly required for algorithmic fidelity, making this difference explicit or configurable would remove the last substantive behavioral discrepancy besides model/judge defaults.

## Final Verdict
The Iteration 4 audit verifies that PAIR’s algorithmic core in this framework is effectively identical to the paper and the `JailbreakingLLMs` codebase, and that the previously identified judge-score clamping deviation has been fully resolved. The remaining gaps concern framework-specific default model/judge choices, a slightly more permissive early-stopping condition for out-of-range judge scores, and an API-level decision to return the best-scoring prompt. Because these differences can still affect behavior—especially in default configurations and rare edge cases—the implementation remains **Not 100% Fidelity**, though it is now extremely close with a small, well-characterized set of deviations.

---

## Audit Iteration 3 - 2025-12-26

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Attacker top-p parameter defined but not used | ✅ Fixed | ✅ Fixed | `attack_top_p` is still retrieved and passed as `top_p` into the attacker `LLMLiteLLM.from_config`, keeping decoding aligned with `ATTACK_TOP_P = 0.9` in the reference repo (`pair_gen.py:71–90`, `pair_gen.py:195–205`). |
| JSON extraction semantics differ and are stricter than reference | ✅ Fixed | ✅ Fixed | `_extract_json` continues to mirror `common.extract_json` (first `{` to first `}`, newline stripping, `ast.literal_eval`, key checks) with only benign robustness differences when no closing brace exists (`pair_gen.py:400–438`, `JailbreakingLLMs/common.py:20–38`). |
| Judge scoring regex more permissive than `judges.py` | ✅ Fixed | ✅ Fixed | `_score_response` still only accepts the `[[X]]` pattern and defaults to 1 otherwise, matching `JudgeBase.process_output`; further behavior differences are now captured as a *new* clamping issue rather than regex permissiveness (`pair_gen.py:466–498`, `JailbreakingLLMs/judges.py:39–46`). |
| Reproducibility via fixed random seeds not implemented | ✅ Fixed | ✅ Fixed | `pair_seed` remains wired as `seed` into attacker, target, and judge `LLMLiteLLM` instances, preserving reproducibility in line with the paper and reference repo (`pair_gen.py:155–161`, `pair_gen.py:193–205`, `pair_gen.py:207–231`). |
| Threshold \(t\) for success not exposed as parameter | ⚠️ Still Equivalent | ✅ Fixed | A new `success_threshold` `AttackParameter` (default 10) is now read inside `generate_attack` and used in the stopping condition `score >= success_threshold`, exposing the search control while matching the reference default (`pair_gen.py:162–168`, `pair_gen.py:516–517`, `pair_gen.py:580–583`). |
| Default model choices differ from reference implementation | ❌ Still Broken | ❌ Still Broken | Defaults remain framework-specific (`gpt-4o-mini` attacker/judge, `gpt-3.5-turbo` target, provider `wenwen`) rather than Vicuna-style and GCG/JBB/Llama-Guard judges used in `JailbreakingLLMs/main.py` and `config.py` (`pair_gen.py:57–69`, `pair_gen.py:134–147`). |
| Best-prompt selection as extension beyond reference script | ⚠️ Still Equivalent | ⚠️ Still Equivalent | `generate_attack` still tracks and returns the best-scoring prompt instead of just logging, which is an API-level extension consistent with the algorithm but not present in `JailbreakingLLMs/main.py` (`pair_gen.py:533–578`, `JailbreakingLLMs/main.py:33–71`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Attacker/target/judge role separation | ✅ | ✅ | Three distinct `LLMLiteLLM` instances for attacker, target, and judge are still constructed and used with clear roles, mirroring the gold-standard repo’s separation (`pair_gen.py:193–231`, `JailbreakingLLMs/main.py:22–25`). |
| System prompts and initial message | ✅ | ✅ | Attacker system prompts and `_get_init_message` remain verbatim matches to `system_prompts.get_attacker_system_prompts`, `get_judge_system_prompt`, and `common.get_init_msg` (`pair_gen.py:235–383`, `pair_gen.py:384–392`, `JailbreakingLLMs/system_prompts.py:7–157`, `JailbreakingLLMs/common.py:43–47`). |
| Multi-stream iterative loop and conversation truncation | ✅ | ✅ | The nested loop over `n_iterations` and `n_streams`, early stopping on a high judge score, and truncation via `keep_last_n` continue to match the structure and intent of `JailbreakingLLMs/main.py:33–71` (`pair_gen.py:538–604`). |

**NEW Issues Found This Iteration:**
- **Judge score clamping deviates from reference behavior.** While `_score_response` now uses the same `[[X]]` extraction regex as `JudgeBase.process_output`, it additionally clamps scores into \[1, 10\] (`max(1, min(10, score))`), whereas the reference implementation leaves out-of-range numeric ratings unchanged (`JailbreakingLLMs/judges.py:39–46`). In rare cases where the judge outputs `[[0]]` or `[[15]]`, this implementation would treat them as 1 or 10 (potentially triggering early success) rather than preserving the raw value; this is a subtle but real semantic divergence from the gold-standard code.

**Summary:**
- Fixed: 5 issues
- Partially Fixed: 1 issue (still-intentional best-prompt extension)
- Still Broken: 1 issue (default model/judge configuration)
- Regressions: 0 issues
- New Issues: 1 issue (judge score clamping)

# Implementation Fidelity Verdict
- Paper ID: 2310.08419
- Attack: pair_gen (PAIR - Prompt Automatic Iterative Refinement)
- Verdict: Not 100% Fidelity
- Coverage: 10/12 components (83%)
- Iteration: 3

## Executive Summary
The current `PAIRAttack` implementation in `pair_gen.py` continues to closely mirror both the PAIR algorithm from *Jailbreaking Black Box Large Language Models in Twenty Queries* and the official `JailbreakingLLMs` repository, preserving all fixes introduced in Iterations 1–2 and further improving fidelity by exposing the success threshold \(t\) as a configurable `success_threshold` parameter (default 10). The core PAIR control flow—multi-stream, multi-iteration search, attacker/target/judge role separation, conversation history management with `keep_last_n`, and system prompts—remains in near one-to-one correspondence with `JailbreakingLLMs/main.py`, `common.py`, and `system_prompts.py`. The primary remaining divergences are (a) framework-specific default choices for attacker/target/judge models and judge type, and (b) a subtle but behavior-affecting change in judge scoring that clamps outputs into \[1, 10\] rather than preserving out-of-range ratings, along with the framework-oriented decision to return the best-scoring prompt. These differences are relatively minor but still alter semantics in edge cases and default configurations, so the implementation cannot yet be considered 100% faithful to the paper and gold-standard code.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 (Algorithm description), Plan §3–4 | Separate attacker, target, and judge LLM roles | `src/jbfoundry/attacks/generated/pair_gen.py:193–231` | ✅ | Three distinct `LLMLiteLLM` instances for attacker, target, and judge mirror the roles and separation in `JailbreakingLLMs/main.py:22–25`. |
| §3, Plan §4 | Inputs K (iterations), N (streams), O (objective), target string; conversation history C | `pair_gen.py:35–61`, `pair_gen.py:500–535` | ✅ | `n_iterations`, `n_streams`, `keep_last_n`, and the `goal`/`target` arguments with per-stream `conversation_histories` implement the blueprint’s inputs and conversation history design, analogous to `JailbreakingLLMs/common.initialize_conversations` and `main.py:33–37`. |
| §3, Plan §4–5 | Attacker system prompts: roleplaying, logical appeal, authority endorsement | `pair_gen.py:235–383` | ✅ | The three system prompts are effectively verbatim copies of `system_prompts.roleplaying_prompt`, `logical_appeal_prompt`, and `authority_endorsement_prompt` (`JailbreakingLLMs/system_prompts.py:7–150`). |
| §3, Plan §4–5 | Initial attacker message summarizing objective and target prefix | `pair_gen.py:390–392` | ✅ | `_get_init_message` matches `common.get_init_msg` (`JailbreakingLLMs/common.py:43–44`), using the same bolded objective and “Begin.” phrasing. |
| §3, Plan §4 | Conversation history update with target response and score | `pair_gen.py:394–398`, `pair_gen.py:585–596` | ✅ | `_process_target_response` and the per-stream feedback updates align with `common.process_target_response` and `main.py:35–37`, appending formatted LANGUAGE MODEL OUTPUT / OBJECTIVE / SCORE strings as new user turns. |
| §3, Plan §4 | Multi-stream, multi-iteration search with breadth/depth trade-off (N streams, K iterations) | `pair_gen.py:538–604` | ✅ | The outer loop over `n_iterations` and inner loop over `n_streams`, plus early stopping when any stream’s score crosses the success threshold and history truncation via `keep_last_n`, faithfully reproduce the PAIR search pattern from `JailbreakingLLMs/main.py:33–71`. |
| §3, Plan §6 | JUDGE function scoring 1–10 and success threshold \(t\) | `pair_gen.py:384–388`, `pair_gen.py:466–498`, `pair_gen.py:516–517`, `pair_gen.py:580–583` | ⚠️ | The judge system prompt and `[[X]]` parsing semantics match `system_prompts.get_judge_system_prompt` and `JudgeBase.process_output`, and success is controlled by a parameterized `success_threshold` defaulting to 10 (matching the reference). However, scores are additionally clamped into \[1,10\], whereas the reference leaves out-of-range values unchanged, leading to slight behavioral differences for malformed judge outputs. |
| §3, Plan §4–5 | Attacker JSON output (`improvement`, `prompt`) and retry on malformed outputs | `pair_gen.py:400–438`, `pair_gen.py:440–464` | ✅ | `_extract_json` and `_generate_attack_prompt` now parallel `common.extract_json` and the retry loop in the reference attacker, including up to `max_attack_attempts` retries and requiring both `improvement` and `prompt` keys. |
| §3, Plan §7 | Attacker decoding: temperature \(T = 1\), top-p \(p = 0.9\), max tokens | `pair_gen.py:71–90`, `pair_gen.py:193–205` | ✅ | `attack_temperature`, `attack_max_tokens`, and `attack_top_p` (default 0.9) are passed into the attacker LLM config, consistent with PAIR’s decoding settings and `ATTACK_TEMP`/`ATTACK_TOP_P` in `JailbreakingLLMs/config.py:5–8`. |
| §3, Plan §7 | Target decoding: temperature \(T = 0\), response length \(L = 150\) | `pair_gen.py:127–133`, `pair_gen.py:207–218` | ✅ | `target_temperature=0.0` and `target_max_tokens=150` are used for the target model, matching the blueprint and `JailbreakingLLMs/main.py:110–113`. |
| §3, Plan §4 | Using best-scoring prompt as final attack output | `pair_gen.py:533–578`, `pair_gen.py:605–606` | ⚠️ | Tracking `best_prompt` and returning it at the end is a reasonable extension of the algorithmic intent but differs from the reference script, which only logs prompts and responses rather than surfacing a single “best” prompt programmatically. |
| Plan §9 (Additional Considerations) | Determinism via fixed seeds for reproducibility | `pair_gen.py:155–161`, `pair_gen.py:193–231` | ✅ | A `pair_seed` parameter with default 0 is propagated into all three `LLMLiteLLM` instances as `seed`, matching the paper’s reproducibility recommendation and the reference repository’s fixed-seed design. |

## Parameter Mapping
| Paper / Repo Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| \(K\) – max iterations (§3, Plan §4) | `n_iterations` (`PAIRAttack.PARAMETERS`) | int | 3 | ✅ | Matches `--n-iterations` default in `JailbreakingLLMs/main.py:165–169`. |
| \(N\) – number of streams (§3, Plan §4, README) | `n_streams` | int | 3 | ✅ | Same default as `--n-streams` in the reference script (though experiments often use 20–30 streams). |
| \(O\) – objective / behavior (§3, Plan §3–4) | `goal` argument to `generate_attack` | str | (required) | ✅ | Passed into attacker and judge prompts exactly as in `common.get_init_msg` and `system_prompts.get_attacker_system_prompts`. |
| Target prefix string (§3, Plan §3–4) | `target` argument to `generate_attack` | str | (required) | ✅ | Used as `target_str` in attacker and judge templates, matching `main.py:171–180` and `system_prompts.py`. |
| Threshold \(t\) for success (§3, Plan §4) | `success_threshold` | int | 10 | ✅ | Newly exposed as an `AttackParameter`, with default equal to the reference’s implicit threshold (`score == 10`) and used in the same early-stopping condition. |
| Attacker temperature \(T\) (§3, Plan §7; `config.ATTACK_TEMP`) | `attack_temperature` | float | 1.0 | ✅ | Forwarded to the attacker LLM, matching `ATTACK_TEMP = 1`. |
| Attacker top-p \(p\) (§3, Plan §7; `config.ATTACK_TOP_P`) | `attack_top_p` | float | 0.9 | ✅ | Forwarded as `top_p` to the attacker LLM, implementing the PAIR top-p sampling setting. |
| Attacker max tokens \(L_\text{attack}\) (§3, Plan §7; `--attack-max-n-tokens`) | `attack_max_tokens` | int | 500 | ✅ | Used for attacker generation length, consistent with the reference default. |
| Max attack attempts (`--max-n-attack-attempts`) | `max_attack_attempts` | int | 5 | ✅ | Controls the retry loop in `_generate_attack_prompt`, analogous to `max-n-attack-attempts` in the original script. |
| Target model name (`--target-model`) | `target_model` | str | `"gpt-3.5-turbo"` | ❌ | Semantic role matches the paper and repo, but the default differs from `"vicuna-13b-v1.5"` used in `JailbreakingLLMs/main.py:104–108`. |
| Target max tokens \(L\) (§3, Plan §7; `--target-max-n-tokens`) | `target_max_tokens` | int | 150 | ✅ | Matches the reference default and blueprint token budget. |
| Target temperature \(T_\text{target}\) (`config.TARGET_TEMP`) | `target_temperature` | float | 0.0 | ✅ | Passed into the target LLM config, consistent with `TARGET_TEMP = 0`. |
| Judge model choice (`--judge-model`) | `judge_model` | str | `"gpt-4o-mini"` | ❌ | Role corresponds to the paper’s judge, but the default and implementation (always an LLM judge via `LLMLiteLLM`) differ from the `gcg` / JailbreakBench / Llama-Guard options in the reference repo. |
| Judge max tokens (`--judge-max-n-tokens`) | `judge_max_tokens` | int | 10 | ✅ | Used as the judge generation length, as in `JailbreakingLLMs/main.py:137–140`. |
| Judge temperature (`--judge-temperature`) | `judge_temperature` | float | 0.0 | ✅ | Matches the reference default for temperature. |
| Conversation history length (`--keep-last-n`) | `keep_last_n` | int | 4 | ✅ | Used to truncate per-stream histories at `2 * keep_last_n` messages, matching `main.py:64–66`. |
| Random seed for reproducibility (Plan §9) | `pair_seed` | int | 0 | ✅ | Introduced to provide deterministic behavior and passed as `seed` into all three LLMs. |

## Misalignments / Missing Items
1. **Framework default model and judge configuration still diverge from the reference PAIR setup.**  
   - **Paper / Repo expectation:** The gold-standard repository defaults to Vicuna/Llama-family models and uses GCG/JailbreakBench/Llama-Guard-style judges (`JailbreakingLLMs/config.py:11–21`, `main.py:80–88`, `main.py:103–108`, `judges.load_judge`).  
   - **Observed behavior:** `PAIRAttack` defaults to `"gpt-4o-mini"` for attacker and judge and `"gpt-3.5-turbo"` for the target from provider `"wenwen"`, always using an LLM-based judge via `LLMLiteLLM` instead of `judges.py` abstractions (`pair_gen.py:57–69`, `pair_gen.py:134–147`, `pair_gen.py:221–231`).  
   - **Impact:** Algorithmic structure and parameterization are preserved, but out-of-the-box runs do not replicate the exact model/judge combinations used in the paper and its reference implementation; reproducing reported results requires explicit reconfiguration.

2. **Judge score clamping introduces a subtle semantic deviation from the reference implementation.**  
   - **Paper / Repo expectation:** The judge is instructed to output ratings between 1 and 10, and `JudgeBase.process_output` simply extracts the integer inside `[[X]]`, defaulting to 1 only when parsing fails (`JailbreakingLLMs/judges.py:39–46`); numbers outside \[1,10\] are not modified.  
   - **Observed behavior:** `_score_response` uses the same `[[X]]` regex but then clamps the parsed integer into \[1,10\] (`pair_gen.py:491–495`). This means e.g. `[[0]]` becomes 1 and `[[15]]` becomes 10, potentially turning malformed but parseable ratings into successful jailbreaks when `success_threshold` is 10.  
   - **Impact:** For well-formed judge outputs in the intended range, behavior matches the reference exactly; for rare out-of-range ratings, however, this clamping can modify scores and early-stopping behavior, so the attack’s search dynamics are not strictly identical to the gold-standard code.

3. **Best-prompt selection remains an API-level extension relative to the reference script.**  
   - **Paper / Repo expectation:** The PAIR script performs a search and stops when a jailbreak is found, logging prompts/responses/scores but not returning a designated “best” prompt (`JailbreakingLLMs/main.py:33–71`).  
   - **Observed behavior:** `generate_attack` tracks `best_prompt` and `best_score` across all streams and iterations and always returns the highest-scoring prompt even if no perfect (score 10) jailbreak is found (`pair_gen.py:533–578`, `pair_gen.py:605–606`).  
   - **Impact:** This is a reasonable design for the jbfoundry framework and aligns with the algorithm’s intent, but it is still an observable behavioral difference relative to the original script and may change which prompt is surfaced downstream in borderline cases.

## Extra Behaviors Not in Paper
- **Framework integration via `ModernBaseAttack` and `LLMLiteLLM`.**  
  The attack is embedded into the jbfoundry framework with configuration via `AttackParameter` objects and `LLMLiteLLM.from_config`, rather than using the original `APILiteLLM`/FastChat/JailbreakBench stack. This structural adaptation is necessary for this codebase but goes beyond the paper’s presentation.

- **Richer logging and explicit reporting of best scores.**  
  The implementation logs model choices, iteration progress, and discovery of new best prompts (`pair_gen.py:233–233`, `pair_gen.py:536–579`), providing additional debugging information not described in the paper.

## Required Changes to Reach 100%
1. **Align default model and judge choices with the reference PAIR configuration or document divergences more strongly.**  
   - **File / Lines:** `src/jbfoundry/attacks/generated/pair_gen.py:57–69`, `pair_gen.py:134–147`, `pair_gen.py:221–231`.  
   - **Change:** Either (a) change the default `attack_model`, `target_model`, and `judge_model` to match the reference repo’s defaults (e.g., Vicuna-13b-v1.5 attacker/target and `gcg`/JBB/Llama-Guard judges), or (b) add prominent comments and/or docstrings stating that current defaults are framework-specific and provide explicit example configurations that exactly reproduce the paper’s setup.  
   - **Justification:** Ensures that typical, unmodified runs align more closely with the models and judges used in the original experiments, reducing the gap between this framework and the published results.

2. **Remove or gate judge score clamping to exactly mirror `JudgeBase.process_output`.**  
   - **File / Lines:** `src/jbfoundry/attacks/generated/pair_gen.py:491–495`.  
   - **Change:** Drop the `max(1, min(10, score))` clamping and instead return the parsed integer directly (falling back to 1 only when parsing fails), or make clamping an opt-in behavior guarded by a configuration flag that defaults to the reference semantics.  
   - **Justification:** Restores strict behavioral equivalence with the gold-standard judge handling, including in edge cases where the judge emits ratings outside \[1, 10\].

3. **Optionally, align or parameterize the “best-prompt” API with the reference script.**  
   - **File / Lines:** `src/jbfoundry/attacks/generated/pair_gen.py:533–578`, `pair_gen.py:605–606`.  
   - **Change:** Either (a) document clearly that returning `best_prompt` is a framework extension and leave behavior as-is, or (b) add an option to return the last or any successful prompt in a way that can exactly reproduce the logging-only behavior of `JailbreakingLLMs/main.py`.  
   - **Justification:** While not strictly required for algorithmic fidelity, making this difference explicit or configurable would remove the last substantive behavioral discrepancy besides model/judge defaults.

## Final Verdict
The Iteration 3 audit confirms that all prior semantic issues around top‑p handling, JSON extraction, judge regexes, and reproducibility seeding remain fixed, and that the success threshold \(t\) is now cleanly exposed as a configurable parameter while preserving the reference default. The implementation’s control flow and core PAIR logic are essentially identical to the paper and the `JailbreakingLLMs` repository, with remaining deviations confined to default model/judge choices, judge-score clamping, and an API-level best-prompt return design. Because these differences can still affect behavior—especially in edge cases and default runs—the attack cannot yet be labeled **100% Fidelity**, but it is now extremely close, with a small and well-delineated set of changes needed to reach full fidelity.

---

## Audit Iteration 2 - 2025-12-26

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Attacker top-p parameter defined but not used | ❌ | ✅ Fixed | `attack_top_p` is now retrieved and passed as `top_p` into `LLMLiteLLM.from_config` for the attacker (`pair_gen.py:171–182`), matching `ATTACK_TOP_P` usage in the reference repo. |
| JSON extraction semantics differ and are stricter than reference | ⚠️ | ✅ Fixed | `_extract_json` now mirrors `common.extract_json` by slicing from the first `{` to the first `}`, stripping newlines, and using `ast.literal_eval` with key checks (`pair_gen.py:373–411`). |
| Judge scoring regex more permissive than `judges.py` | ⚠️ | ✅ Fixed | `_score_response` now only accepts the `[[X]]` pattern and defaults to 1 otherwise, exactly matching `judges.py:39–46` (`pair_gen.py:439–471`). |
| Reproducibility via fixed random seeds not implemented | ❌ | ✅ Fixed | New `pair_seed` parameter is introduced and propagated as `seed` into attacker, target, and judge `LLMLiteLLM` instances (`pair_gen.py:155–161`, `pair_gen.py:168–204`). |
| Threshold \(t\) for success not exposed as parameter | ⚠️ | ⚠️ Still Equivalent | Success is still hard-coded as `score == 10`, which matches the reference script’s behavior but remains non-configurable (`pair_gen.py:552–555`). |
| Default model choices differ from reference implementation | ❌ | ❌ Still Broken | Defaults remain framework-specific (`gpt-4o-mini` / `gpt-3.5-turbo` / `gpt-4o-mini`) rather than Vicuna/GPT/Llama-Guard as in the `JailbreakingLLMs` repo (`pair_gen.py:57–69`, `pair_gen.py:134–147`). |
| Best-prompt selection as extension beyond reference script | ⚠️ | ⚠️ Still Equivalent | `generate_attack` still returns the best-scoring prompt instead of mirroring the logging-only behavior of `main.py`, an acceptable but non-identical extension (`pair_gen.py:504–507`, `pair_gen.py:541–551`, `pair_gen.py:577–578`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Attacker/target/judge role separation | ✅ | ✅ | Still uses three distinct `LLMLiteLLM` instances with clear roles as in the reference repo. |
| System prompts and initial message | ✅ | ✅ | PAIR system prompts and init message remain verbatim matches to `system_prompts.py` and `common.get_init_msg`. |
| Multi-stream iterative loop and conversation truncation | ✅ | ✅ | Loop over `n_iterations` and `n_streams` plus `keep_last_n`-based history truncation still align with `JailbreakingLLMs/main.py:33–71`. |

**NEW Issues Found This Iteration:**
- None. No new deviations were found beyond the remaining differences in default model choices and the best-prompt-return behavior already identified.

**Summary:**
- Fixed: 4 issues
- Partially Fixed: 2 issues
- Still Broken: 1 issue
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2310.08419
- Attack: pair_gen (PAIR - Prompt Automatic Iterative Refinement)
- Verdict: Not 100% Fidelity
- Coverage: 10/12 components (83%)
- Iteration: 2

## Executive Summary
The updated `PAIRAttack` implementation in `pair_gen.py` now closely matches both the PAIR algorithm described in *Jailbreaking Black Box Large Language Models in Twenty Queries* and the official `JailbreakingLLMs` reference code. All previously flagged semantic deviations in attacker top‑p sampling, JSON extraction, judge scoring, and reproducibility seeding have been addressed, bringing the control flow, scoring, and parsing behavior into near one‑to‑one alignment with the gold-standard repository. The remaining differences are limited to framework-specific defaults (attacker/target/judge model names) and the choice to return the best-scoring prompt rather than only logging results; these are minor but still constitute deviations from the exact reference configuration. As a result, the implementation is substantially higher fidelity than in Iteration 1 but cannot be declared fully 100% faithful due to these residual mismatches.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 (Algorithm description), Plan §3–4 | Separate attacker, target, and judge LLM roles | `src/jbfoundry/attacks/generated/pair_gen.py:164–205` | ✅ | Three distinct `LLMLiteLLM` instances for attacker, target, and judge mirror the roles and separation in `JailbreakingLLMs/main.py:22–25`. |
| §3, Plan §4 | Inputs K (iterations), N (streams), O (objective), target string; conversation history C | `pair_gen.py:35–61`, `pair_gen.py:486–503` | ✅ | `n_iterations`, `n_streams`, and `keep_last_n` plus `goal`/`target` arguments and `conversation_histories` structure match the blueprint and `common.py:68–77`. |
| §3, Plan §4–5 | Attacker system prompts: roleplaying, logical appeal, authority endorsement | `pair_gen.py:208–355` | ✅ | Prompts are copied almost verbatim from `JailbreakingLLMs/system_prompts.py:1–151`, including strategy descriptions and JSON-output instructions. |
| §3, Plan §4–5 | Initial attacker message summarizing objective and target prefix | `pair_gen.py:363–365` | ✅ | `_get_init_message` matches `common.get_init_msg` (`common.py:43–47`), with the same bolded objective and “Begin.” text. |
| §3, Plan §4 | Conversation history update with target response and score | `pair_gen.py:367–371`, `pair_gen.py:557–575` | ✅ | `_process_target_response` format and per-stream history updates correspond to `common.process_target_response` and `main.py:35–37`. |
| §3, Plan §4 | Multi-stream, multi-iteration search with breadth/depth trade-off (N streams, K iterations) | `pair_gen.py:486–576` | ✅ | Outer loop over `n_iterations` and inner loop over `n_streams` replicate `JailbreakingLLMs/main.py:33–71`, including early stopping when any score is 10 and truncation controlled by `keep_last_n`. |
| §3, Plan §6 | JUDGE function scoring 1–10 and success threshold t (score==10) | `pair_gen.py:357–361`, `pair_gen.py:439–471`, `pair_gen.py:552–555` | ✅ | Judge system prompt and `[[X]]` parsing match `system_prompts.get_judge_system_prompt` and `judges.GPTJudge.process_output`, with success defined as any score equal to 10. |
| §3, Plan §4–5 | Attacker JSON output (`improvement`, `prompt`) and retry on malformed outputs | `pair_gen.py:373–437` | ✅ | `_extract_json` and `_generate_attack_prompt` mirror `common.extract_json` and the retry behavior of `AttackLM._generate_attack`, including up to `max_attack_attempts` retries and key validation. |
| §3, Plan §7 | Attacker decoding: temperature \(T = 1\), top-p \(p = 0.9\), max tokens | `pair_gen.py:71–90`, `pair_gen.py:171–182` | ✅ | `attack_temperature`, `attack_max_tokens`, and `attack_top_p` (default 0.9) are all passed to `LLMLiteLLM`, aligning with `ATTACK_TEMP`/`ATTACK_TOP_P` and PAIR’s decoding settings. |
| §3, Plan §7 | Target decoding: temperature \(T = 0\), response length \(L = 150\) | `pair_gen.py:127–133`, `pair_gen.py:185–193` | ✅ | `target_temperature=0.0` and `target_max_tokens=150` match the blueprint and `JailbreakingLLMs/main.py:110–113`. |
| §3, Plan §4 | Using best-scoring prompt as final attack output | `pair_gen.py:504–507`, `pair_gen.py:541–551`, `pair_gen.py:577–578` | ⚠️ | Tracking `best_prompt` by maximum judge score is consistent with the algorithm’s intent but goes beyond `main.py`, which does not return a single “best” prompt. |
| Plan §9 (Additional Considerations) | Determinism via fixed seeds for reproducibility | `pair_gen.py:155–161`, `pair_gen.py:168–204` | ✅ | `pair_seed` default 0 is propagated as `seed` into all three `LLMLiteLLM` instances, matching the paper’s reproducibility recommendation and the reference repo’s fixed-seed behavior. |

## Parameter Mapping
| Paper / Repo Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| \(K\) – max iterations (§3, Plan §4) | `n_iterations` (`PAIRAttack.PARAMETERS`) | int | 3 | ✅ | Matches `--n-iterations` default in `JailbreakingLLMs/main.py:165–169`. |
| \(N\) – number of streams (§3, Plan §4, README) | `n_streams` | int | 3 | ✅ | Same default as `--n-streams` in `main.py:151–156` (though the paper recommends up to 20–30 in experiments). |
| \(O\) – objective / behavior (§3, Plan §3–4) | `goal` argument to `generate_attack` | str | (required) | ✅ | Passed through to attacker and judge prompts exactly as in `common.py:43–47` and `system_prompts.py`. |
| Target prefix string (§3, Plan §3–4) | `target` argument to `generate_attack` | str | (required) | ✅ | Used as `target_str` in attacker and judge prompts, matching `main.py:176–180` and the reference templates. |
| Threshold \(t\) for success (§3, Plan §4) | hard-coded `score == 10` | int | 10 | ⚠️ | Same effective threshold as `main.py:69–71` but not exposed as a configurable parameter in this framework. |
| Attacker temperature \(T\) (§3, Plan §7; `config.ATTACK_TEMP`) | `attack_temperature` | float | 1.0 | ✅ | Passed into `LLMLiteLLM.from_config` for the attacker, matching `config.ATTACK_TEMP`. |
| Attacker top-p \(p\) (§3, Plan §7; `config.ATTACK_TOP_P`) | `attack_top_p` | float | 0.9 | ✅ | Now retrieved and passed as `top_p` into the attacker LLM, aligning with PAIR’s specified top-p sampling. |
| Attacker max tokens \(L_\text{attack}\) (§3, Plan §7; `--attack-max-n-tokens`) | `attack_max_tokens` | int | 500 | ✅ | Used in attacker LLM config (`pair_gen.py:171–182`), matching the reference’s default. |
| Max attack attempts (`--max-n-attack-attempts`) | `max_attack_attempts` | int | 5 | ✅ | Used in `_generate_attack_prompt` retry loop (`pair_gen.py:420–437`), consistent with `AttackLM._generate_attack`. |
| Target model name (`--target-model`) | `target_model` | str | `"gpt-3.5-turbo"` | ❌ | Semantic role matches `--target-model`, but the default differs from `"vicuna-13b-v1.5"` in `main.py:104–108`, affecting direct replication of reference runs. |
| Target max tokens \(L\) (§3, Plan §7; `--target-max-n-tokens`) | `target_max_tokens` | int | 150 | ✅ | Plumbed into `self.target_llm` (`pair_gen.py:185–193`), matching the reference settings. |
| Target temperature \(T_\text{target}\) (`config.TARGET_TEMP`) | `target_temperature` | float | 0.0 | ✅ | Used in target LLM config, consistent with `TARGET_TEMP = 0`. |
| Judge model choice (`--judge-model`) | `judge_model` | str | `"gpt-4o-mini"` | ❌ | Role matches `--judge-model`, but the default and implementation (always an LLM judge rather than `GCG`/`JBBJudge`) differ from the gold-standard repo. |
| Judge max tokens (`--judge-max-n-tokens`) | `judge_max_tokens` | int | 10 | ✅ | Used in judge LLM config (`pair_gen.py:196–203`), as in `main.py:137–140`. |
| Judge temperature (`--judge-temperature`) | `judge_temperature` | float | 0.0 | ✅ | Passed to the judge LLM and matches reference defaults. |
| Conversation history length (`--keep-last-n`) | `keep_last_n` | int | 4 | ✅ | Used to truncate per-stream histories at `2 * keep_last_n` messages (`pair_gen.py:570–575`), matching `main.py:64–66`. |
| Random seed for reproducibility (Plan §9) | `pair_seed` | int | 0 | ✅ | New parameter wired into all three LLMs as `seed`, aligning with the paper’s reproducibility recommendation. |

## Misalignments / Missing Items
1. **Framework default model choices still diverge from the reference PAIR configuration.**  
   - **Paper / Repo expectation:** The reference implementation defaults to Vicuna/Llama-style models for attacker and target and `gcg`/Llama-Guard/JailbreakBench as judges (`config.py:11–21`, `main.py:80–88`, `main.py:103–108`, `main.py:129–135`).  
   - **Observed behavior:** `PAIRAttack` defaults to `"gpt-4o-mini"` for attacker and judge and `"gpt-3.5-turbo"` for the target (`pair_gen.py:57–69`, `pair_gen.py:134–147`), and always implements the judge as a generic chat model, not via `judges.py`.  
   - **Impact:** Algorithmic behavior is preserved and parameters allow overriding to match the paper, but out-of-the-box runs do not match the exact model/judge setup used in the paper and official repository.

2. **Success threshold \(t\) remains hard-coded rather than parameterized.**  
   - **Paper / Plan expectation:** PAIR defines a success condition via a threshold on the judge score; the reference script implicitly uses `score == 10` as this threshold (`main.py:69–71`).  
   - **Observed behavior:** `PAIRAttack` also hard-codes success as `score == 10` (`pair_gen.py:552–555`) and does not expose this threshold as an `AttackParameter`.  
   - **Impact:** Semantics are identical to the reference repo, but users cannot easily experiment with different thresholds within this framework; this is a minor configurability deviation rather than a logic error.

## Extra Behaviors Not in Paper
- **Best-prompt selection and return value.**  
  `generate_attack` tracks the highest judge score observed and returns the corresponding prompt (`pair_gen.py:504–507`, `pair_gen.py:541–551`, `pair_gen.py:577–578`), whereas the reference `main.py` only logs prompts/responses. This is a reasonable framework extension but not described in the paper.

- **Framework-specific integration via `ModernBaseAttack` and `LLMLiteLLM`.**  
  The attack is embedded in the jbfoundry framework and uses `LLMLiteLLM` instead of the paper’s `APILiteLLM`/JailbreakBench helpers; this is necessary for integration but differs structurally from the original codebase.

## Required Changes to Reach 100%
1. **Align default model and judge choices with the reference PAIR setup (or document divergences explicitly).**  
   - **File / Lines:** `src/jbfoundry/attacks/generated/pair_gen.py:57–69`, `pair_gen.py:134–147`, `pair_gen.py:92–105`.  
   - **Change:** Either (a) change the default `attack_model`, `target_model`, and `judge_model` to the reference defaults (e.g., Vicuna-style attacker/target and `gcg`/Llama-Guard/JailbreakBench judge), or (b) add clear comments explaining that the current defaults are framework-specific while providing example configurations that exactly reproduce the paper’s setup.  
   - **Justification:** Ensures that, without additional configuration, the implementation more faithfully mirrors the experimental setup used in the paper and repository.

2. **Optionally expose the success threshold \(t\) as a configurable parameter.**  
   - **File / Lines:** `src/jbfoundry/attacks/generated/pair_gen.py:35–49`, `pair_gen.py:552–555`.  
   - **Change:** Add an `AttackParameter` (e.g., `success_score`) with default 10 and use it instead of the hard-coded constant in the early-stopping condition; keep the default at 10 to maintain behavioral parity with the reference script.  
   - **Justification:** While the current hard-coded threshold matches the repo, making it configurable would eliminate the remaining minor configurability deviation without altering default behavior.

## Final Verdict
With the corrections to attacker top‑p handling, JSON extraction, judge scoring, and reproducibility seeding, the `PAIRAttack` implementation now matches the PAIR algorithm and the `JailbreakingLLMs` reference behavior in all key algorithmic respects. The only remaining differences are framework-specific defaults for model/judge selection and the choice to return the best-scoring prompt plus a non-parameterized success threshold, which are minor but still technically deviations from the exact reference configuration. Therefore, the current implementation remains **Not 100% Fidelity**, but the remaining gaps are small and primarily concern default configuration and API design rather than core algorithm semantics.

---

# Implementation Fidelity Verdict
- Paper ID: 2310.08419
- Attack: pair_gen (PAIR - Prompt Automatic Iterative Refinement)
- Verdict: Not 100% Fidelity
- Coverage: 8/12 components (67%)
- Iteration: 1

## Executive Summary
The `PAIRAttack` implementation in `pair_gen.py` captures the high-level structure of the PAIR algorithm from *Jailbreaking Black Box Large Language Models in Twenty Queries* and closely follows the official `JailbreakingLLMs` reference implementation. It correctly models multi-stream iterative refinement, attacker/target/judge roles, conversation history updates, early stopping when a fully jailbroken response is found, and the three persuasion strategies. However, there are several semantic deviations from the reference code and paper: the attacker top-p parameter is defined but never applied, JSON extraction behavior differs and is stricter than the original, judge scoring uses more permissive regexes than the reference implementation, and randomness is not seeded for reproducibility. These gaps mean the behavior—especially in edge cases and sampling—can differ from the paper and gold-standard repository, so the implementation cannot be considered 100% faithful without further changes.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 (Algorithm description), Plan §3–4 | Separate attacker, target, and judge LLM roles | `src/jbfoundry/attacks/generated/pair_gen.py:156–188` | ✅ | Three distinct `LLMLiteLLM` instances for attacker, target, and judge mirror paper and `JailbreakingLLMs/main.py:22–25`. |
| §3, Plan §4 | Inputs K (iterations), N (streams), O (objective), target string; conversation history C | `pair_gen.py:34–55`, `pair_gen.py:460–489` | ✅ | `n_iterations`, `n_streams`, and `keep_last_n` parameters plus `goal`/`target` arguments and `conversation_histories` match blueprint and `common.py:68–77`. |
| §3, Plan §4–5 | Attacker system prompts: roleplaying, logical appeal, authority endorsement | `pair_gen.py:192–339` | ✅ | Prompts are copied almost verbatim from `JailbreakingLLMs/system_prompts.py:1–151`, including strategy descriptions and JSON-output instructions. |
| §3, Plan §4–5 | Initial attacker message summarizing objective and target prefix | `pair_gen.py:347–349` | ✅ | `_get_init_message` matches `common.py:get_init_msg` at `common.py:43–47`, setting the same bolded objective and “Begin.” text. |
| §3, Plan §4 | Conversation history update with target response and score | `pair_gen.py:351–355`, `pair_gen.py:544–555` | ✅ | `_process_target_response` string format and per-stream history updates correspond to `common.py:46–47` and `main.py:35–37`. |
| §3, Plan §4 | Multi-stream, multi-iteration search with breadth/depth trade-off (N streams, K iterations) | `pair_gen.py:460–565` | ✅ | Outer loop over `n_iterations` and inner loop over `n_streams` replicate `JailbreakingLLMs/main.py:33–71`, including early stopping when any score is 10 and truncation controlled by `keep_last_n`. |
| §3, Plan §6 | JUDGE function scoring 1–10 and success threshold t (score==10) | `pair_gen.py:341–345`, `pair_gen.py:409–458` | ⚠️ | Uses the same judge system prompt as `system_prompts.py:154–157` and the same success criterion `score == 10`, but regex parsing is more permissive than `judges.py:39–46`, changing behavior when the judge output format deviates from `[[rating]]`. |
| §3, Plan §4–5 | Attacker JSON output (`improvement`, `prompt`) and retry on malformed outputs | `pair_gen.py:357–381`, `pair_gen.py:383–407` | ⚠️ | Logic mirrors `common.py:8–41` and `conversers.py:87–125` (retry loop and required keys), but uses `json.loads` and `rfind("}")` instead of `ast.literal_eval` and first `}`; this makes JSON parsing stricter and behavior on malformed outputs diverges from the reference. |
| §3, Plan §7 | Attacker decoding: temperature \(T=1\), top-p \(p=0.9\), max tokens | `pair_gen.py:77–90`, `pair_gen.py:156–168` | ❌ | `attack_temperature` and `attack_max_tokens` are respected (matching `config.py:5–8`), but `attack_top_p` is never passed into `LLMLiteLLM`, so top-p defaults are uncontrolled and can differ from the paper’s \(p=0.9\) and `config.ATTACK_TOP_P`. |
| §3, Plan §7 | Target decoding: temperature \(T=0\), response length \(L=150\) | `pair_gen.py:119–153`, `pair_gen.py:170–178` | ✅ | `target_temperature=0.0` and `target_max_tokens=150` match both blueprint and `JailbreakingLLMs/main.py:109–113` and `config.py:5–8`. |
| §3, Plan §4 | Using best-scoring prompt as final attack output | `pair_gen.py:491–537`, `pair_gen.py:564–565` | ⚠️ | Tracking `best_prompt` by maximum judge score is consistent with algorithmic intent but goes beyond `main.py`, which only early-stops and logs; reference script does not define a single “best prompt” return value. |
| Plan §9 (Additional Considerations) | Determinism via fixed seeds for reproducibility | `pair_gen.py:156–188`, `src/jbfoundry/llm/litellm.py:277–456` | ❌ | Unlike `JailbreakingLLMs/language_models.py:63–86` which sets a fixed `seed=0` in `batch_completion`, the PAIRAttack path does not configure any seed for `LLMLiteLLM`, so runs are not reproducible as recommended. |

## Parameter Mapping
| Paper / Repo Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| \(K\) – max iterations (§3, Plan §4) | `n_iterations` (`PAIRAttack.PARAMETERS`) | int | 3 | ✅ | Matches `--n-iterations` default in `JailbreakingLLMs/main.py:165–169`. |
| \(N\) – number of streams (§3, Plan §4, README) | `n_streams` | int | 3 | ✅ | Same default as `--n-streams` in `main.py:151–156` (though paper recommends up to 20–30 for experiments). |
| \(O\) – objective / behavior (§3, Plan §3–4) | `goal` argument to `generate_attack` | str | (required) | ✅ | Passed through to system prompts and judge prompt exactly as in `common.py:43–47` and `system_prompts.py:7–15`. |
| Target prefix string (§3, Plan §3–4) | `target` argument to `generate_attack` | str | (required) | ✅ | Used as `target_str` in attacker and judge prompts, matching `main.py:176–180` and `system_prompts.py`. |
| Threshold \(t\) for success (§3, Plan §4) | hard-coded `score == 10` | int | 10 | ⚠️ | Same effective threshold as reference (`main.py:69–71`) but not exposed as a configurable parameter. |
| Attacker temperature \(T\) (§3, Plan §7; `config.ATTACK_TEMP`) | `attack_temperature` | float | 1.0 | ✅ | Passed into `LLMLiteLLM.from_config` at `pair_gen.py:163–167`, matching `config.py:5`. |
| Attacker top-p \(p\) (§3, Plan §7; `config.ATTACK_TOP_P`) | `attack_top_p` | float | 0.9 | ❌ | Parameter exists with correct default but is never used when constructing `self.attacker_llm`, so the true top-p is whatever default LiteLLM uses, not 0.9. |
| Attacker max tokens \(L_\text{attack}\) (§3, Plan §7; `--attack-max-n-tokens`) | `attack_max_tokens` | int | 500 | ✅ | Used in attacker LLM config at `pair_gen.py:167–168`, matching `main.py:89–93`. |
| Max attack attempts (`--max-n-attack-attempts`) | `max_attack_attempts` | int | 5 | ✅ | Used in `_generate_attack_prompt` loop (`pair_gen.py:390–405`), consistent with `conversers.py:94–124`. |
| Target model name (`--target-model`) | `target_model` | str | `"gpt-3.5-turbo"` | ❌ | Semantic role matches, but default differs from reference’s `"vicuna-13b-v1.5"` (`main.py:104–108`); this affects replication of paper results unless overridden. |
| Target max tokens \(L\) (§3, Plan §7; `--target-max-n-tokens`) | `target_max_tokens` | int | 150 | ✅ | Plumbed into `self.target_llm` (`pair_gen.py:173–178`), matching `main.py:110–113` and blueprint. |
| Target temperature \(T_\text{target}\) (`config.TARGET_TEMP`) | `target_temperature` | float | 0.0 | ✅ | Used at `pair_gen.py:176–177`, consistent with `config.py:6`. |
| Judge model choice (`--judge-model`) | `judge_model` | str | `"gpt-4o-mini"` | ❌ | Role matches, but default differs from reference’s `"gcg"` / Llama-Guard/JBB (`main.py:131–135`); also uses LLMLiteLLM instead of `judges.py` classes. |
| Judge max tokens (`--judge-max-n-tokens`) | `judge_max_tokens` | int | 10 | ✅ | Plumbed into `self.judge_llm` at `pair_gen.py:186–187`, same as `main.py:137–140`. |
| Judge temperature (`--judge-temperature`) | `judge_temperature` | float | 0.0 | ✅ | Used in judge LLM config at `pair_gen.py:186–187`, matching `main.py:143–147`. |
| Conversation history length (`--keep-last-n`) | `keep_last_n` | int | 4 | ✅ | Used to truncate histories at `2 * keep_last_n` messages per stream (`pair_gen.py:557–562`), matching `main.py:64–66`. |

## Misalignments / Missing Items
1. **Attacker top-p parameter defined but not used (semantic deviation).**  
   - **Paper / Repo expectation:** Attacker decoding uses top-p sampling with \(p = 0.9\) (Plan §7; `JailbreakingLLMs/config.py:5–8`, `conversers.py:57–60`).  
   - **Observed behavior:** `PAIRAttack.PARAMETERS` defines `attack_top_p` with default `0.9` (`pair_gen.py:84–90`), but this value is never passed to `LLMLiteLLM.from_config` in `__init__` (`pair_gen.py:156–168`). As a result, the actual top-p is governed by LiteLLM defaults rather than the paper-specified 0.9, and user overrides to `attack_top_p` have no effect.  
   - **Impact:** Changes the attacker’s sampling distribution relative to both the paper and the reference implementation, potentially altering exploration behavior and jailbreak success rates.

2. **JSON extraction semantics differ and are stricter than the reference implementation.**  
   - **Paper / Repo expectation:** The attacker returns a JSON-like structure with `improvement` and `prompt` fields; the reference code uses `extract_json` (`common.py:8–41`) which (a) slices from the first `{` to the first `}`, (b) strips newlines, and (c) parses with `ast.literal_eval`, tolerating some non-strict JSON formatting.  
   - **Observed behavior:** `_extract_json` in `pair_gen.py:357–381` slices from the first `{` to the last `}` and parses with `json.loads`. This rejects outputs that would be accepted by `ast.literal_eval` (e.g., single quotes, some Python-style literals) and behaves differently when multiple braces appear in the output.  
   - **Impact:** For edge cases where the attacker’s output is not perfectly valid JSON, the PAIRAttack implementation may fail to parse where the reference would succeed (or vice versa), changing how often the retry loop succeeds and potentially raising a `ValueError` earlier or more often than in the gold-standard code.

3. **Judge scoring regex is more permissive than the gold-standard `judges.py` implementation.**  
   - **Paper / Repo expectation:** The judge is instructed to output `Rating: [[rating]]`, and `GPTJudge.process_output` (`judges.py:39–46`) only recognizes the `[[X]]` pattern; any other format triggers a warning and defaults the score to 1.  
   - **Observed behavior:** `_score_response` (`pair_gen.py:409–458`) first looks for `[[X]]`, but then falls back to `Rating: X` and finally to any bare integer between 1 and 10 in the judge output. These fallbacks can assign non-1 scores in cases where the reference implementation would consider the output malformed and treat it as score 1.  
   - **Impact:** For misformatted judge responses, the attack’s notion of “best prompt” and the early-stopping condition (`score == 10`) can diverge from the reference, leading to different stopping behavior and selected prompts.

4. **Reproducibility via fixed random seeds is not implemented.**  
   - **Paper / Plan expectation:** Plan §9 recommends using fixed seeds for random number generation to ensure reproducibility; the reference APILiteLLM sets `seed=0` in `language_models.py:76–85`.  
   - **Observed behavior:** `LLMLiteLLM.query` (`src/jbfoundry/llm/litellm.py:277–456`) is invoked from PAIRAttack without any explicit seed configuration; it relies on LiteLLM defaults.  
   - **Impact:** PAIRAttack runs are not deterministic even when other parameters are held fixed, deviating from the recommended reproducibility settings used in the original repository.

5. **Default model choices differ from the reference implementation and paper experiments.**  
   - **Paper / Repo expectation:** The reference uses Vicuna/Llama as default attacker and target models (`config.py:11–21`, `main.py:80–88`, `main.py:103–108`), and the paper describes experiments with GPT‑3.5/4, Vicuna, and Gemini. Judge models include GCG and Llama-Guard/JailbreakBench (`main.py:129–135`, `judges.py:76–84`).  
   - **Observed behavior:** `PAIRAttack` defaults the attacker, target, and judge models to `"gpt-4o-mini"` / `"gpt-3.5-turbo"` from provider `"wenwen"` (`pair_gen.py:56–69`, `pair_gen.py:91–104`, `pair_gen.py:133–146`). The judge is always implemented as a generic chat model using the judge system prompt, rather than reusing `judges.py`.  
   - **Impact:** While the algorithmic structure is preserved and parameters allow overriding model names, out-of-the-box behavior does not mirror the models used in the paper or the official repository, so direct replication of reported results requires additional configuration.

6. **Best-prompt selection is an extension beyond the reference script.**  
   - **Paper / Plan expectation:** The algorithm conceptually searches for a successful jailbreak and can stop once a jailbreak is found; the reference script stops early when any judge score reaches 10 and logs all prompts/responses (`main.py:58–71`) but does not return a single “best” prompt programmatically.  
   - **Observed behavior:** `generate_attack` tracks `best_prompt` and `best_score` over all streams and iterations (`pair_gen.py:491–537`) and returns `best_prompt` at the end (`pair_gen.py:564–565`).  
   - **Impact:** This is a reasonable design for the jbfoundry framework API and does not contradict the paper, but it is an additional behavior not present in the gold-standard script and slightly changes which prompt is surfaced to downstream evaluation when no perfect (score 10) jailbreak is found.

## Extra Behaviors Not in Paper
- **Robust judge parsing with multiple regex fallbacks.**  
  `_score_response` (`pair_gen.py:409–458`) adds additional parsing patterns and clamping behavior beyond what is documented in the paper or implemented in `judges.py`, affecting how non-standard judge outputs are treated.

- **Richer logging and explicit “best score” reporting.**  
  The implementation logs model configurations and iteration progress (`pair_gen.py:190`, `pair_gen.py:495–537`, `pair_gen.py:564–565`), which aids debugging but is not part of the paper’s algorithm.

- **Framework-specific integration via `ModernBaseAttack` and `LLMLiteLLM`.**  
  The attack is wrapped in the jbfoundry framework (`src/jbfoundry/attacks/base.py:99–187`) and uses `LLMLiteLLM` (`src/jbfoundry/llm/litellm.py:99–457`) instead of the paper’s `APILiteLLM` and JailbreakBench integration. These are structural adaptations required to fit this codebase but go beyond what is described in the paper.

## Required Changes to Reach 100%
1. **Wire the attacker top-p parameter into the attacker LLM configuration.**  
   - **File / Lines:** `src/jbfoundry/attacks/generated/pair_gen.py:77–90`, `pair_gen.py:156–168`.  
   - **Change:** Retrieve `attack_top_p = self.get_parameter_value("attack_top_p")` in `__init__` and pass it through to `LLMLiteLLM.from_config` (e.g., via a `top_p` keyword argument or equivalent), ensuring the attacker uses \(p=0.9\) by default as in `config.ATTACK_TOP_P`.  
   - **Justification:** Aligns sampling behavior with Plan §7 and `JailbreakingLLMs/config.py:5–8` and makes the `attack_top_p` parameter effective.

2. **Align JSON extraction semantics with `common.extract_json` or clearly justify deviations.**  
   - **File / Lines:** `src/jbfoundry/attacks/generated/pair_gen.py:357–381`.  
   - **Change:** Either (a) reimplement `_extract_json` to match `common.py:20–38` (first `}`, newline stripping, `ast.literal_eval`, same error conditions), or (b) document and adjust behavior to accept all outputs accepted by the reference while still using `json.loads` (e.g., by normalizing single to double quotes and limiting the slice to the first matching brace pair).  
   - **Justification:** Ensures that the success/failure profile of attacker JSON parsing matches the gold-standard implementation, especially for borderline-formatted outputs.

3. **Restrict judge scoring to the reference format or make the fallback logic optional and clearly documented.**  
   - **File / Lines:** `src/jbfoundry/attacks/generated/pair_gen.py:409–458`.  
   - **Change:** To match `judges.py:39–46`, consider only accepting the `[[X]]` pattern and defaulting to score 1 otherwise, or gate the more permissive regexes behind an explicit configuration flag that defaults to the reference behavior.  
   - **Justification:** Restores identical semantics for how misformatted judge outputs influence scores and early stopping.

4. **Introduce explicit seeding for reproducibility consistent with the paper and reference repo.**  
   - **File / Lines:** `src/jbfoundry/attacks/generated/pair_gen.py:156–188`, `src/jbfoundry/llm/litellm.py:277–456`.  
   - **Change:** Add an optional `seed` parameter (with default 0) for the PAIR attack and propagate it into `LLMLiteLLM` (e.g., via stored kwargs passed to LiteLLM’s `completion`), mirroring how `APILiteLLM` passes `seed=0` in `language_models.py:76–85`.  
   - **Justification:** Matches Plan §9 and the reference repository’s deterministic configuration.

5. **Optionally, align default model choices with the reference PAIR setup.**  
   - **File / Lines:** `src/jbfoundry/attacks/generated/pair_gen.py:56–69`, `pair_gen.py:91–104`, `pair_gen.py:133–146`.  
   - **Change:** Change default `attack_model`, `target_model`, and `judge_model` to values consistent with the paper/repo (e.g., Vicuna/GPT‑3.5/4 and Llama‑Guard/JBB), or clearly document in comments that defaults are framework-specific while still demonstrating how to configure the original paper settings.  
   - **Justification:** Not strictly algorithmic, but improves out-of-the-box fidelity to the experiments described in the paper and the official repository.

## Final Verdict
Given the unused attacker top-p parameter, stricter and behavior-changing JSON parsing compared to `common.extract_json`, more permissive judge scoring regexes than `judges.py`, and the absence of reproducibility seeding, the current `PAIRAttack` implementation is **Not 100% Fidelity** relative to the PAIR paper and its gold-standard `JailbreakingLLMs` repository. The overall control flow, roles, and key parameters are well aligned, so addressing the highlighted issues should be sufficient to bring the implementation up to full fidelity.


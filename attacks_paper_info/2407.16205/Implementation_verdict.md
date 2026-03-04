## Audit Iteration 5 - 2025-12-26

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| No visual / text-to-image pathway for ABJ | ⚠️ | ⚠️ Partially Fixed | Visual/text-to-image path remains unimplemented; parameters `text_to_image_model` and `enable_visual_path` are still present but unused (`abj_gen.py:88–101,319–457`). |
| Default model choices differ from reference repository (assist/judge/target) | ⚠️ | ⚠️ Partially Fixed | Assist model default (`gpt-4o-mini`), target fallback (`deepseek-chat`), and judge provider remain different from the repo defaults (`glm4`, `deepseek_v3`, `gpt4o`) (`abj_gen.py:38–102,174–199,353–371`; `ABJ.py:8–16`). |
| Target model defaults differ from repo gold standard | ⚠️ | ⚠️ Partially Fixed | `generate_attack` still falls back to `deepseek-chat` instead of `deepseek_v3` when `target_llm` is not provided (`abj_gen.py:353–361`; `ABJ.py:8–16`). |
| Multi-sample success condition and gating differ from reference pipeline | ❌ | ❌ Still Broken | Success gating now uses `any(judgements)` across all samples instead of matching the repo’s `all('1' in judgement_results[0] ...)` first-sample check, so it remains semantically different from `pipeline_execution.py:9–21,46–60` (`abj_gen.py:382–408,425–448`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Query-to-neutral-data transformation | ✅ | ✅ | `_transform_query_to_neutral_data` is unchanged and still mirrors `get_data` in `data_preparation.py:13–38`, including regex-based JSON extraction and `<data>` fallback on parse failure (`abj_gen.py:201–235`). |
| Chain-of-thought attack prompt construction | ✅ | ✅ | `ABJ_ATTACK_PROMPT` and `_get_attack_prompt` are unchanged and still match `ABJ_attack_prompt` in `pipeline_prompt.py:1–3` (`abj_gen.py:118–120,267–277`). |
| Toxicity adjustment logic (enhance vs reduce via refusal judge) | ✅ | ✅ | `_toxicity_adjustment` still follows `toxicity_adjustment` semantics: refusal → reduction, otherwise → enhancement, using the assistant model and JSON-to-`<data>` reformatting (`abj_gen.py:296–317`; `toxicity_adjustment.py:7–18`). |
| Refusal detection prompt and usage | ✅ | ✅ | `DETAILED_JUDGE_PROMPT` and `_is_refusal` still align with `detailed_judge_prompt` in `pipeline_prompt.py:83–98`, treating any judgment containing `1` as refusal (`abj_gen.py:152–166,279–295`). |

**NEW Issues Found This Iteration:**
- No new semantic deviations beyond the previously-known issues were identified; the main change is that multi-sample success gating was modified to `any(judgements)`, which remains within the scope of the existing gating misalignment rather than a distinct new issue.

**Summary:**
- Fixed: 0 issues
- Partially Fixed: 3 issues
- Still Broken: 1 issue
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2407.16205
- Attack: abj_gen
- Verdict: Not 100% Fidelity
- Coverage: 7/12 components (58%)
- Iteration: 5

## Executive Summary
The Iteration 5 `ABJAttack` implementation in `abj_gen.py` continues to faithfully reproduce the core **textual** ABJ loop from the paper and `ABJ-Attack` repo—query-to-`<data>` transformation, chain-of-thought attack prompt construction, refusal-based toxicity adjustment, and robust JSON fallback—while maintaining exposed parameters for search control and visual models. However, the implementation still omits the actual visual/text-to-image pathway, keeps default model choices only partially aligned with the reference repository, and now explicitly uses an `any(judgements)` multi-sample success condition that deviates from the repo’s first-sample gating in `pipeline_execution.py`. As a result, even though no new discrepancies were introduced in this iteration and previously-correct components remain stable, the attack cannot yet be considered a fully faithful reproduction of the full ABJ algorithm and official code.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §ABJ, Attack Initiation | Transform harmful query into structured neutral textual data via assistant model and JSON parsing | `src/jbfoundry/attacks/generated/abj_gen.py:201–235`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/data_preparation.py:13–38` | ✅ | Still mirrors official `get_data`: same `query_transform` prompt, regex extraction of JSON, and `<data>`-formatted fallback when parsing fails. |
| §ABJ, Attack Initiation | Use assistant model for query transformation | `src/jbfoundry/attacks/generated/abj_gen.py:174–193,201–212`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/pipeline_prompt.py:15–27` | ✅ | `self.assist_model` is configured and used analogously to the repo assistant model (assistant generates JSON which is parsed into `<data>`). |
| §ABJ, Attack Initiation | Generate neutral visual (image) data via text-to-image model from attributes | — | ❌ | Implementation remains text-only: it never calls any image/visual or text-to-image model, whereas the plan and repo (`utils/text2img.py`, `ABJ_visual.py`, `pipeline/pipeline_prompt.py:6–13`) define a visual path. |
| §ABJ, Attack Execution | Chain-of-thought reasoning over textual personal data to infer task and steps | `src/jbfoundry/attacks/generated/abj_gen.py:118–120,267–277`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/data_analysis.py:5–8`; `pipeline/pipeline_prompt.py:1–3` | ✅ | `ABJ_ATTACK_PROMPT` and `_get_attack_prompt` still match the repo’s `ABJ_attack_prompt` template and usage. |
| §ABJ, Visual Path | Visual chain-of-thought reasoning prompt and visual attack path | — | ❌ | The implementation does not expose or use `ABJ_visual_attack_prompt` or any visual reasoning path present in the repo (`pipeline/pipeline_prompt.py:6–8`, `ABJ_visual.py`). |
| §ABJ, Attack Control | Iterative attack-execute–adjust loop with maximum toxicity adjustment rounds | `src/jbfoundry/attacks/generated/abj_gen.py:296–317,413–451`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/pipeline_execution.py:34–69`; `pipeline/toxicity_adjustment.py:7–18` | ✅ | For each failed stage, the implementation detects refusals using the last response, adjusts toxicity accordingly, regenerates an attack prompt, and repeats up to `max_adjustment_rounds`, matching the reference loop structure. |
| §ABJ, Search Control | Multiple response samples per prompt controlled by `max_attack_rounds` | `src/jbfoundry/attacks/generated/abj_gen.py:38–45,179–180,381–448`; `attacks_paper_info/2407.16205/ABJ-Attack/ABJ.py:8–19`; `pipeline/pipeline_execution.py:9–21,34–60` | ❌ | `max_attack_rounds` is parameterized and used to sample multiple responses per attack prompt, but success now triggers when **any** sample is judged jailbroken, instead of matching the repo’s `all('1' in judgement_results[0] ...)` first-sample gating semantics. |
| §ABJ, Toxicity Adjustment | Benign vs refusal classification and toxicity enhancement/reduction | `src/jbfoundry/attacks/generated/abj_gen.py:279–317`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/toxicity_adjustment.py:7–18`; `pipeline/pipeline_prompt.py:30–44,47–61,83–98` | ✅ | Uses a dedicated refusal judge (`DETAILED_JUDGE_PROMPT`) and two prompts (`TOXICITY_ENHANCEMENT_PROMPT` / `TOXICITY_REDUCTION_PROMPT`) exactly as in the repo: refusal → reduction, otherwise → enhancement. |
| §ABJ, Refusal Detection | Separate judge model and prompt for refusal detection | `src/jbfoundry/attacks/generated/abj_gen.py:152–166,279–295`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/pipeline_prompt.py:83–98`; `pipeline/toxicity_adjustment.py:7–18` | ✅ | Implements the same detailed refusal-judging prompt and uses a dedicated judge model to decide between enhancement and reduction. |
| §ABJ, Visual & Dual-Modality Design | Joint textual and visual reasoning pathway for ABJ | — | ❌ | Attack remains purely textual and does not cover the visual/dual-modality aspects described in the blueprint and supported in the repo (e.g., `ABJ_visual.py`, `utils/text2img.py`). |
| §ABJ, Parameterization | Model parameters and defaults (assist, judge, target, temps, text-to-image) | `src/jbfoundry/attacks/generated/abj_gen.py:38–102,174–199,353–371`; `attacks_paper_info/2407.16205/ABJ-Attack/ABJ.py:8–19`; `ABJ-Attack/readme.md:31–47` | ⚠️ | Parameters exist and are wired; judge defaults now match (`gpt-4o`), and text-to-image parameters are exposed, but assist model default (`gpt-4o-mini`) and target default (`deepseek-chat` vs `deepseek_v3`) still diverge from the repo’s documented choices. |
| §ABJ, Robustness | Fallback behavior on malformed JSON from assistant | `src/jbfoundry/attacks/generated/abj_gen.py:201–235,237–265`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/data_preparation.py:21–38` | ✅ | Continues to use the same pattern-based JSON extraction and default `<data>` backup to handle parse failures, consistent with the official code’s robustness behavior. |

## Parameter Mapping
| Paper / Repo Parameter | Code Parameter | Type | Default (Paper/Repo) | Default (Code) | Match (✅/⚠️/❌) | Notes |
|---|---|---|---|---|---|---|
| Harmful query `HB` / task | `goal` (in `generate_attack`) | str | None (required input) | None (required input) | ✅ | Harmful query is consistently passed as `goal` and used as the question in evaluator input. |
| `max_adjustment_rounds` | `max_adjustment_rounds` (AttackParameter) | int | 5 (`ABJ.py:16`, README) | 5 | ✅ | Matches reference default and semantics; controls number of toxicity adjustment loops. |
| `max_attack_rounds` | `max_attack_rounds` (AttackParameter) | int | 1 in `ABJ.py:15` (README suggests 3) | 1 | ❌ | Parameter is exposed and controls samples per prompt, but the success criterion (`any(judgements)`) does not replicate the repo’s `all('1' in judgement_results[0])` first-sample gating semantics. |
| Assist model name `assist_model` | `assist_model` (AttackParameter) | str | `glm4` (`ABJ.py:11`) | `gpt-4o-mini` | ❌ | Same role but different default model name than the reference repo; description notes this as a functionally equivalent alternative. |
| Assist model provider | `assist_provider` (AttackParameter) | str | Local `LLMModel` backend | `wenwen` | ⚠️ | Different provider layer due to framework integration; role is equivalent but not one-to-one with repo’s implementation. |
| Judge model name `judge_model` | `judge_model` (AttackParameter) | str | `gpt4o` (`ABJ.py:12`) | `gpt-4o` | ✅ | Matches the reference default (notation difference only). |
| Judge model provider | `judge_provider` (AttackParameter) | str | Local `LLMModel` backend | `wenwen` | ⚠️ | As above, provider differs but role (refusal detection) is equivalent. |
| Text-to-image model | `text_to_image_model` (AttackParameter) | str | `gpt-image-1` (blueprint / repo utilities) | `gpt-image-1` | ⚠️ | Parameter name, type, and default align with the blueprint, but it is not used anywhere in the current implementation. |
| Visual path enable flag | `enable_visual_path` (AttackParameter) | bool | (not explicitly parameterized in paper) | `False` | ⚠️ | Extra flag introduced for API compatibility; currently has no effect because the visual path is unimplemented. |
| Assist model temperature | `temperature` (AttackParameter) | float | 1.0 (from `LLMModel(..., temperature=1)`) | 1.0 | ✅ | Matches the intended behavior for the assistant model. |
| Target model name `target_model` | `args.target_model` in repo; `args.model` → internal `target_llm` here | str | `deepseek_v3` (`ABJ.py:10`) | `deepseek-chat` (via `getattr(self.args, 'model', 'deepseek-chat')`) | ⚠️ | Closer to the repo’s DeepSeek default than the original framework default, but still not the exact documented default. |
| Judge for harmfulness | `judge_model` + `judge_prompt` (repo) vs `evaluator` (`WenwenOpenAIChatEvaluator`) | object / callable | Custom `judge_model` + `judge_prompt` | Framework evaluator | ⚠️ | Semantics (detects harmfulness) align, but implementation uses the framework’s evaluation module rather than the repo’s explicit prompt. |
| Refusal judge | `judge_model` + `detailed_judge_prompt` | object / prompt | Present (repo) | Present | ✅ | Same prompt content and role for refusal detection. |

## Misalignments / Missing Items

1. **Multi-sample success condition and gating still diverge from the reference pipeline**
   - **Paper/Repo citation**: `ABJ-Attack/ABJ.py:8–19` and `pipeline/pipeline_execution.py:9–21,34–60` define `max_attack_rounds` and use it inside `generate_responses_and_judgements`, with downstream control flow driven by `all('1' in judgement_results[0] for judgement_results in judgement_results_list)`, which for a single target model effectively checks only the **first** judgment per batch.  
   - **Expected behavior**: For each attack prompt, the attack should sample multiple responses (controlled by `max_attack_rounds`) and decide whether to proceed to toxicity adjustment using a gating condition consistent with the reference implementation.  
   - **Observed behavior**: `ABJAttack.generate_attack` samples `max_attack_rounds` responses but treats the attack as successful if **any** sample is judged jailbroken (`any(judgements)`), rather than matching the reference’s first-sample gating semantics (`abj_gen.py:381–408,425–448`).  
   - **Impact**: Changes the effective search/control dynamics and stopping condition relative to the cloned repo; harmful outputs that appear only in later samples are now sufficient for success, which may improve attack strength but is not a faithful reproduction of the gold-standard pipeline.

2. **Visual/text-to-image pathway remains unimplemented**
   - **Paper/Plan citation**: The blueprint in `2407.16205_plan.md:23–33` describes `transform_query_to_neutral_data(harmful_query) -> Tuple[str, Image]`, explicitly including both textual and visual data; model roles also include a text-to-image model (`gpt-image-1`) at `plan:30–31,89–90`. The repo defines visual prompts and utilities in `ABJ-Attack/pipeline/pipeline_prompt.py:6–13`, `ABJ_visual.py`, and `utils/text2img.py`.  
   - **Expected behavior**: The ABJ implementation should be able to generate and use visual data as part of the reasoning-based jailbreak (at least as an optional, parameterized path).  
   - **Observed behavior**: `ABJAttack` only handles a textual `<data>` string; the module docstring and parameters (`text_to_image_model`, `enable_visual_path`) clearly state that the visual path is not implemented, and no image generation or visual reasoning path is wired into `generate_attack` (`abj_gen.py:88–101,319–457`).  
   - **Impact**: Omits a modality that the plan and repo consider part of the ABJ design, reducing fidelity for multi-modal attack scenarios despite the clearer documentation and parameter surface.

3. **Default model choices remain partially misaligned with the reference repository**
   - **Paper/Repo citation**: `ABJ-Attack/ABJ.py:10–12` sets `target_model='deepseek_v3'`, `assist_model='glm4'`, `judge_model='gpt4o'` by default; `ABJ-Attack/readme.md:31–47` documents these roles and parameters.  
   - **Expected behavior**: Within this framework, model types/providers can change, but default model names should align with the reference when feasible, or clear justification should be given.  
   - **Observed behavior**: `ABJAttack.PARAMETERS` now match the judge model default (`gpt-4o`) and move the target default toward DeepSeek (`deepseek-chat`), but the assist model default remains `gpt-4o-mini`, and the target name still does not match `deepseek_v3`; text-to-image parameters are present but unused (`abj_gen.py:38–102,174–199,353–371`; `ABJ.py:8–19`).  
   - **Impact**: These differences reduce strict reproducibility relative to the gold-standard repo and can affect empirical performance, though they do not change the core textual algorithm.

## Extra Behaviors Not in Paper
- **Framework evaluator integration for harmfulness judgment**:  
  The implementation uses `WenwenOpenAIChatEvaluator` from `src/jbfoundry/evaluation/base.py` (`abj_gen.py:363–371`) instead of the repo’s custom `judge_model` + `judge_prompt` pair (`pipeline_execution.py:9–21`, `pipeline/pipeline_prompt.py:64–80`). This is consistent with the framework’s requirements and explicitly documented, but it is not described in the paper or ABJ-only repo.

- **Prompt-only fallback mode**:  
  If no target model or evaluator is passed, `generate_attack` returns a single attack prompt without running the adjustment loop (`abj_gen.py:379–457`). This “prompt-only” mode is not present in the official ABJ pipeline but can be useful in this framework and does not contradict the paper.

- **Non-functional visual parameters for API compatibility**:  
  `text_to_image_model` and `enable_visual_path` are exposed as parameters and documented as non-functional in this framework (`abj_gen.py:88–101`), providing an API surface that mirrors the paper/repo but without behavior.

## Required Changes to Reach 100%

1. **Align multi-sample success condition and gating with the reference pipeline (or clearly document a deliberate deviation)**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:38–45,381–408,425–448`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/pipeline_execution.py:9–21,46–60`.  
   - **Change**:
     - Update the success condition after sampling `max_attack_rounds` responses so that, for a single target model, it emulates the repo’s logic (e.g., basing success on the first judgment only, or providing a configuration flag to choose between “repo-compatible” and “any-sample” gating with a clearly documented default).  
   - **Justification**: Restores fidelity to the cloned repo’s search-control behavior and stopping condition while still allowing a more aggressive “any-sample” mode as an explicit, opt-in deviation if desired.

2. **Implement (or robustly emulate) the visual/text-to-image pathway**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:38–102,201–235,296–451`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/pipeline_prompt.py:6–13`; `ABJ-Attack/utils/text2img.py`, `ABJ_visual.py`.  
   - **Change**:
     - Wire `text_to_image_model` and `enable_visual_path` into the attack logic so that, when enabled, the attack generates a visual representation from the `<data>` attributes (following `generate_visual_descriptions` and visual prompts) and uses it in an ABJ-style visual reasoning prompt.  
     - If the framework fundamentally cannot support images, clearly separate this implementation as a “text-only ABJ variant” and document that it does not cover the visual branch of the algorithm required for full fidelity.  
   - **Justification**: Restores the dual-modality behavior described by the paper and gold-standard repo, or explicitly scopes the implementation to a subset of the algorithm.

3. **Further align or explicitly justify default model choices**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:38–102,174–199,353–371`; `attacks_paper_info/2407.16205/ABJ-Attack/ABJ.py:8–19`.  
   - **Change**:
     - Adjust `assist_model` and target model defaults to mirror the reference repo (`glm4`, `deepseek_v3`) where these models are available in the deployment environment, or expand parameter descriptions to explicitly justify the deviations (e.g., unavailability of `glm4`/`deepseek_v3` in this framework).  
   - **Justification**: Improves strict reproducibility relative to the gold-standard repo and clarifies any unavoidable divergences.

## Final Verdict
**Not 100% Fidelity** — The Iteration 5 implementation maintains strong fidelity for the core textual ABJ loop (query transformation, chain-of-thought prompting, refusal-based toxicity adjustment, and robustness to malformed JSON) and correctly exposes search and visual-related parameters, but it still diverges from the reference `ABJ-Attack` repository in two material ways: the **multi-sample success gating** does not match the repo’s `max_attack_rounds` semantics, and the **visual/text-to-image pathway** remains unimplemented, with default model choices only partially aligned. Until these discrepancies are resolved or explicitly scoped as out-of-algorithm, the implementation cannot be considered a fully faithful reproduction of the paper and official code.

## Audit Iteration 4 - 2025-12-26

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| No visual / text-to-image pathway for ABJ | ⚠️ | ⚠️ Partially Fixed | Attack remains text-only; `text_to_image_model` and `enable_visual_path` are exposed and documented as non-functional, but no visual pipeline or image model invocation exists (`abj_gen.py:87–100,200–233,318–453`). |
| Default model choices differ from reference repository (assist/judge/target) | ⚠️ | ⚠️ Partially Fixed | Defaults are unchanged this iteration (`assist_model='gpt-4o-mini'`, target fallback `deepseek-chat`, judge `gpt-4o`) and remain only partially aligned with the repo defaults (`glm4`, `deepseek_v3`, `gpt4o`). |
| Target model defaults differ from repo gold standard | ⚠️ | ⚠️ Partially Fixed | Fallback target model is still `deepseek-chat` rather than `deepseek_v3` (`abj_gen.py:352–360`; `ABJ-Attack/ABJ.py:8–16`); behavior is closer than in Iteration 1 but not identical. |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Query-to-neutral-data transformation | ✅ | ✅ | `_transform_query_to_neutral_data` still mirrors `get_data` in `data_preparation.py:13–38`, including regex-based JSON extraction and `<data>` fallback on parse failure (`abj_gen.py:200–233`; `data_preparation.py:13–38`). |
| Chain-of-thought attack prompt construction | ✅ | ✅ | `ABJ_ATTACK_PROMPT` and `_get_attack_prompt` are unchanged and still match `ABJ_attack_prompt` in `pipeline_prompt.py:1–3` (`abj_gen.py:117–120,266–276`). |
| Toxicity adjustment logic (enhance vs reduce via refusal judge) | ✅ | ✅ | `_toxicity_adjustment` continues to follow `toxicity_adjustment` semantics: refusal → reduction, otherwise → enhancement, using the assistant model and JSON-to-`<data>` reformatting (`abj_gen.py:295–317`; `toxicity_adjustment.py:7–18`). |
| Refusal detection prompt and usage | ✅ | ✅ | `DETAILED_JUDGE_PROMPT` and `_is_refusal` still align with `detailed_judge_prompt` in `pipeline_prompt.py:83–98`, treating any judgment containing `1` as a refusal (`abj_gen.py:151–165,278–293`). |
| Search-control gating semantics (`max_attack_rounds`) | ✅ | ❌ | Closer inspection of `pipeline_execution.py:9–21,43–60` shows the repo gates success on `'1' in judgement_results[0]` across all rounds for each target model, whereas `abj_gen.py:385–406,422–445` only inspects `judgements[0]` from the first round and ignores later samples, so the multi-sample success condition still deviates from the gold-standard pipeline. |

**NEW Issues Found This Iteration:**
- No brand-new code paths were added or broken in Iteration 4; the main change is a more precise analysis of the **multi-sample success gating semantics**, which reveals that they still diverge from `pipeline_execution.generate_responses_and_judgements` despite the presence of `max_attack_rounds`.

**Summary:**
- Fixed: 0 issues
- Partially Fixed: 3 issues
- Still Broken: 1 issue
- Regressions: 1 issue
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2407.16205
- Attack: abj_gen
- Verdict: Not 100% Fidelity
- Coverage: 7/12 components (58%)
- Iteration: 4

## Executive Summary
The Iteration 4 `ABJAttack` implementation in `abj_gen.py` continues to faithfully capture the **textual** ABJ loop from the paper and reference `ABJ-Attack` repository: transforming harmful queries into neutral `<data>` text, constructing a chain-of-thought attack prompt, detecting refusals with a dedicated judge, and iteratively adjusting toxicity via enhancement/reduction prompts with robust JSON fallback behavior. However, a closer comparison to `pipeline_execution.py` shows that while `max_attack_rounds` is now exposed and used to sample multiple responses, the **success gating** still inspects only the first judgment and ignores later samples, which does not match the repo’s multi-sample OR-over-rounds behavior. In addition, the **visual/text-to-image pathway** remains unimplemented (parameters only) and the default model choices (especially assist and target defaults) are still only partially aligned with the gold-standard repo. Because of these remaining semantic and coverage gaps, the implementation cannot yet be considered a fully faithful reproduction of the complete ABJ algorithm.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §ABJ, Attack Initiation | Transform harmful query into structured neutral textual data via assistant model and JSON parsing | `src/jbfoundry/attacks/generated/abj_gen.py:200–233`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/data_preparation.py:13–38` | ✅ | Still closely mirrors official `get_data`: same `query_transform` prompt, regex extraction of JSON, and `<data>`-formatted fallback when parsing fails. |
| §ABJ, Attack Initiation | Use assistant model for query transformation | `src/jbfoundry/attacks/generated/abj_gen.py:173–192,200–212`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/pipeline_prompt.py:15–27` | ✅ | `self.assist_model` is configured and used analogously to the repo assistant model (assistant generates JSON which is parsed into `<data>`). |
| §ABJ, Attack Initiation | Generate neutral visual (image) data via text-to-image model from attributes | — | ❌ | Implementation is still text-only: it never calls any image/visual or text-to-image model, whereas the plan and repo (`utils/text2img.py`, `ABJ_visual.py`, `pipeline/pipeline_prompt.py:6–13`) define a visual path. |
| §ABJ, Attack Execution | Chain-of-thought reasoning over textual personal data to infer task and steps | `src/jbfoundry/attacks/generated/abj_gen.py:117–120,266–276`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/data_analysis.py:5–8`; `pipeline/pipeline_prompt.py:1–3` | ✅ | `ABJ_ATTACK_PROMPT` and `_get_attack_prompt` still match the repo’s `ABJ_attack_prompt` template and usage. |
| §ABJ, Visual Path | Visual chain-of-thought reasoning prompt and visual attack path | — | ❌ | The implementation does not expose or use `ABJ_visual_attack_prompt` or any visual reasoning path present in the repo (`pipeline/pipeline_prompt.py:6–8`, `ABJ_visual.py`). |
| §ABJ, Attack Control | Iterative attack-execute–adjust loop with maximum toxicity adjustment rounds | `src/jbfoundry/attacks/generated/abj_gen.py:295–317,410–448`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/pipeline_execution.py:34–69`; `pipeline/toxicity_adjustment.py:7–18` | ✅ | For each failed stage, the implementation detects refusals using the last response, adjusts toxicity accordingly, regenerates an attack prompt, and repeats up to `max_adjustment_rounds`, matching the reference loop structure. |
| §ABJ, Search Control | Multiple response samples per prompt controlled by `max_attack_rounds` | `src/jbfoundry/attacks/generated/abj_gen.py:37–44,177–179,385–446`; `attacks_paper_info/2407.16205/ABJ-Attack/ABJ.py:8–19`; `pipeline/pipeline_execution.py:9–21,34–60` | ❌ | `max_attack_rounds` is parameterized and used to sample multiple responses per attack prompt, but success checks only `judgements[0]` (first round) instead of mirroring the repo’s condition `all('1' in judgement_results[0] for judgement_results in judgement_results_list)`, which effectively requires at least one harmful sample across **all rounds** for each target model. |
| §ABJ, Toxicity Adjustment | Benign vs refusal classification and toxicity enhancement/reduction | `src/jbfoundry/attacks/generated/abj_gen.py:278–317`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/toxicity_adjustment.py:7–18`; `pipeline/pipeline_prompt.py:30–44,47–61,83–98` | ✅ | Uses a dedicated refusal judge (`DETAILED_JUDGE_PROMPT`) and two prompts (`TOXICITY_ENHANCEMENT_PROMPT` / `TOXICITY_REDUCTION_PROMPT`) exactly as in the repo: refusal → reduction, otherwise → enhancement. |
| §ABJ, Refusal Detection | Separate judge model and prompt for refusal detection | `src/jbfoundry/attacks/generated/abj_gen.py:151–165,278–293`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/pipeline_prompt.py:83–98`; `pipeline/toxicity_adjustment.py:7–18` | ✅ | Implements the same detailed refusal-judging prompt and uses a dedicated judge model to decide between enhancement and reduction. |
| §ABJ, Visual & Dual-Modality Design | Joint textual and visual reasoning pathway for ABJ | — | ❌ | Attack remains purely textual and does not cover the visual/dual-modality aspects described in the blueprint and supported in the repo (e.g., `ABJ_visual.py`, `utils/text2img.py`). |
| §ABJ, Parameterization | Model parameters and defaults (assist, judge, target, temps, text-to-image) | `src/jbfoundry/attacks/generated/abj_gen.py:37–101,173–199,352–370`; `attacks_paper_info/2407.16205/ABJ-Attack/ABJ.py:8–19`; `ABJ-Attack/readme.md:31–47` | ⚠️ | Parameters exist and are wired; judge defaults now match (`gpt-4o`), and text-to-image parameters are exposed, but assist model default (`gpt-4o-mini`) and target default (`deepseek-chat` vs `deepseek_v3`) still diverge from the repo’s documented choices. |
| §ABJ, Robustness | Fallback behavior on malformed JSON from assistant | `src/jbfoundry/attacks/generated/abj_gen.py:200–233,235–264`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/data_preparation.py:21–38` | ✅ | Continues to use the same pattern-based JSON extraction and default `<data>` backup to handle parse failures, consistent with the official code’s robustness behavior. |

## Parameter Mapping
| Paper / Repo Parameter | Code Parameter | Type | Default (Paper/Repo) | Default (Code) | Match (✅/⚠️/❌) | Notes |
|---|---|---|---|---|---|---|
| Harmful query `HB` / task | `goal` (in `generate_attack`) | str | None (required input) | None (required input) | ✅ | Harmful query is consistently passed as `goal` and used as the question in evaluator input. |
| `max_adjustment_rounds` | `max_adjustment_rounds` (AttackParameter) | int | 5 (`ABJ.py:16`, README) | 5 | ✅ | Matches reference default and semantics; controls number of toxicity adjustment loops. |
| `max_attack_rounds` | `max_attack_rounds` (AttackParameter) | int | 1 in `ABJ.py:15` (README suggests 3) | 1 | ⚠️ | Parameter is exposed and controls samples per prompt, but the success criterion (checking only `judgements[0]`) does not replicate the repo’s `'1' in judgement_results[0]` gating over all rounds. |
| Assist model name `assist_model` | `assist_model` (AttackParameter) | str | `glm4` (`ABJ.py:11`) | `gpt-4o-mini` | ❌ | Same role but different default model name than the reference repo; description notes this as a functionally equivalent alternative. |
| Assist model provider | `assist_provider` (AttackParameter) | str | Local `LLMModel` backend | `wenwen` | ⚠️ | Different provider layer due to framework integration; role is equivalent but not one-to-one with repo’s implementation. |
| Judge model name `judge_model` | `judge_model` (AttackParameter) | str | `gpt4o` (`ABJ.py:12`) | `gpt-4o` | ✅ | Matches the reference default (notation difference only). |
| Judge model provider | `judge_provider` (AttackParameter) | str | Local `LLMModel` backend | `wenwen` | ⚠️ | As above, provider differs but role (refusal detection) is equivalent. |
| Text-to-image model | `text_to_image_model` (AttackParameter) | str | `gpt-image-1` (blueprint / repo utilities) | `gpt-image-1` | ⚠️ | Parameter name, type, and default align with the blueprint, but it is not used anywhere in the current implementation. |
| Visual path enable flag | `enable_visual_path` (AttackParameter) | bool | (not explicitly parameterized in paper) | `False` | ⚠️ | Extra flag introduced for API compatibility; currently has no effect because the visual path is unimplemented. |
| Assist model temperature | `temperature` (AttackParameter) | float | 1.0 (from `LLMModel(..., temperature=1)`) | 1.0 | ✅ | Matches the intended behavior for the assistant model. |
| Target model name `target_model` | `args.target_model` in repo; `args.model` → internal `target_llm` here | str | `deepseek_v3` (`ABJ.py:10`) | `deepseek-chat` (via `getattr(self.args, 'model', 'deepseek-chat')`) | ⚠️ | Closer to the repo’s DeepSeek default than Iteration 1, but still not the exact documented default. |
| Judge for harmfulness | `judge_model` + `judge_prompt` (repo) vs `evaluator` (`WenwenOpenAIChatEvaluator`) | object / callable | Custom `judge_model` + `judge_prompt` | Framework evaluator | ⚠️ | Semantics (detects harmfulness) align, but implementation uses the framework’s evaluation module rather than the repo’s explicit prompt; this deviation is explicitly documented. |
| Refusal judge | `judge_model` + `detailed_judge_prompt` | object / prompt | Present (repo) | Present | ✅ | Same prompt content and role for refusal detection. |

## Misalignments / Missing Items

1. **Multi-sample success condition and gating still differ from reference pipeline**
   - **Paper/Repo citation**: `ABJ-Attack/ABJ.py:8–19` and `pipeline/pipeline_execution.py:9–21,34–60` define `max_attack_rounds` and use it inside `generate_responses_and_judgements`, with downstream control flow driven by `all('1' in judgement_results[0] for judgement_results in judgement_results_list)`. For a single target model, this effectively requires that **at least one sample across all rounds** be judged harmful for that model.  
   - **Expected behavior**: For each attack prompt, the attack should sample multiple responses (controlled by `max_attack_rounds`) and decide whether to proceed to toxicity adjustment based on a gating condition consistent with the reference implementation.  
   - **Observed behavior**: `ABJAttack.generate_attack` samples `max_attack_rounds` responses but then only inspects `judgements[0]` (the first round’s judgment) to decide success (`abj_gen.py:385–406,422–445`), ignoring later samples that could be harmful.  
   - **Impact**: Changes the effective search/control dynamics and stopping condition relative to the cloned repo: harmful outputs that appear only in later samples are treated as failures, altering attack success rates and search behavior.

2. **Visual/text-to-image pathway still not implemented**
   - **Paper/Plan citation**: The blueprint in `2407.16205_plan.md:23–33` describes `transform_query_to_neutral_data(harmful_query) -> Tuple[str, Image]`, explicitly including both textual and visual data; model roles also include a text-to-image model (`gpt-image-1`) at `plan:30–31,89–90`. The repo defines visual prompts and utilities in `ABJ-Attack/pipeline/pipeline_prompt.py:6–13`, `ABJ_visual.py`, and `utils/text2img.py`.  
   - **Expected behavior**: The ABJ implementation should be able to generate and use visual data as part of the reasoning-based jailbreak (at least as an optional, parameterized path).  
   - **Observed behavior**: `ABJAttack` only handles a textual `<data>` string; the module docstring and parameters (`text_to_image_model`, `enable_visual_path`) clearly state that the visual path is not implemented, and no image generation or visual reasoning path is wired into `generate_attack`.  
   - **Impact**: Omits a modality that the plan and repo consider part of the ABJ design, reducing fidelity for multi-modal attack scenarios despite the clearer documentation and parameter surface.

3. **Default model choices remain partially misaligned with the reference repository**
   - **Paper/Repo citation**: `ABJ-Attack/ABJ.py:10–12` sets `target_model='deepseek_v3'`, `assist_model='glm4'`, `judge_model='gpt4o'` by default; `ABJ-Attack/readme.md:31–47` documents these roles and parameters.  
   - **Expected behavior**: Within this framework, model types/providers can change, but default model names should align with the reference when feasible, or clear justification should be given.  
   - **Observed behavior**: `ABJAttack.PARAMETERS` now match the judge model default (`gpt-4o`) and move the target default toward DeepSeek (`deepseek-chat`), but the assist model default remains `gpt-4o-mini`, and the target name still does not match `deepseek_v3`; text-to-image parameters are present but unused.  
   - **Impact**: These differences reduce strict reproducibility relative to the gold-standard repo and can affect empirical performance, though they do not change the core textual algorithm.

## Extra Behaviors Not in Paper
- **Framework evaluator integration for harmfulness judgment**:  
  The implementation uses `WenwenOpenAIChatEvaluator` from `src/jbfoundry/evaluation/base.py` (`abj_gen.py:362–370`) instead of the repo’s custom `judge_prompt` + `judge_model` pair (`pipeline_execution.py:9–21`, `pipeline/pipeline_prompt.py:64–80`). This is consistent with the framework’s requirements and explicitly documented, but it is not described in the paper or ABJ-only repo.

- **Prompt-only fallback mode**:  
  If no target model or evaluator is passed, `generate_attack` returns a single attack prompt without running the adjustment loop (`abj_gen.py:378–453`). This “prompt-only” mode is not present in the official ABJ pipeline but can be useful in this framework and does not contradict the paper.

- **Non-functional visual parameters for API compatibility**:  
  `text_to_image_model` and `enable_visual_path` are exposed as parameters and documented as non-functional in this framework (`abj_gen.py:87–100`), providing an API surface that mirrors the paper/repo but without behavior.

## Required Changes to Reach 100%

1. **Align multi-sample success condition and gating with the reference pipeline**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:37–44,385–406,422–446`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/pipeline_execution.py:9–21,43–60`.  
   - **Change**:
     - Update the success condition after sampling `max_attack_rounds` responses so that, for a single target model, it emulates the repo’s logic (e.g., treating the attack as successful if `any(judgements)` rather than checking only `judgements[0]`, or by explicitly mirroring `'1' in judgement_results[0]` semantics).  
   - **Justification**: Restores fidelity to the cloned repo’s search-control behavior and stopping condition while still using the framework’s evaluator abstraction.

2. **Implement (or robustly emulate) the visual/text-to-image pathway**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:37–101,200–233,295–448`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/pipeline_prompt.py:6–13`; `ABJ-Attack/utils/text2img.py`, `ABJ_visual.py`.  
   - **Change**:
     - Wire `text_to_image_model` and `enable_visual_path` into the attack logic so that, when enabled, the attack generates a visual representation from the `<data>` attributes (following `visual_description_generation` and `generate_visual_descriptions`) and uses it in an ABJ-style visual reasoning prompt (`ABJ_visual_attack_prompt`).  
     - If the framework fundamentally cannot support images, clearly separate this implementation as a “text-only ABJ variant” and document that it does not cover the visual branch of the algorithm required for full fidelity.  
   - **Justification**: Restores the dual-modality behavior described by the paper and gold-standard repo, or explicitly scopes the implementation to a subset of the algorithm.

3. **Further align or explicitly justify default model choices**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:37–101,173–199,352–370`.  
   - **Change**:
     - Adjust `assist_model` and target model defaults to mirror the reference repo (`glm4`, `deepseek_v3`) where these models are available in the deployment environment, or expand parameter descriptions to explicitly justify the deviations (e.g., unavailability of `glm4`/`deepseek_v3` in this framework).  
   - **Justification**: Improves strict reproducibility relative to the gold-standard repo and clarifies any unavoidable divergences.

## Final Verdict
**Not 100% Fidelity** — The Iteration 4 implementation maintains strong fidelity for the core textual ABJ loop (query transformation, chain-of-thought prompting, refusal-based toxicity adjustment, and robustness to malformed JSON) and correctly exposes search and visual-related parameters, but it still diverges from the reference `ABJ-Attack` repository in two material ways: the **multi-sample success gating** does not match the repo’s `max_attack_rounds` semantics, and the **visual/text-to-image pathway** remains unimplemented, with default model choices only partially aligned. Until these discrepancies are resolved or explicitly scoped as out-of-algorithm, the implementation cannot be considered a fully faithful reproduction of the paper and official code.

## Audit Iteration 3 - 2025-12-26

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Missing `max_attack_rounds` search control | ✅ | ✅ Fixed | Parameter remains exposed and drives multi-sample querying in `src/jbfoundry/attacks/generated/abj_gen.py:37–44,177–179,385–446`; no regression observed. |
| No visual / text-to-image pathway for ABJ | ⚠️ | ⚠️ Partially Fixed | Attack remains text-only; docstring and parameters (`text_to_image_model`, `enable_visual_path`) clearly document that the visual path is unsupported, but no actual visual pipeline is implemented. |
| Default model choices differ from reference repository (assist/judge/target) | ⚠️ | ⚠️ Partially Fixed | Defaults are unchanged from Iteration 2 (`assist_model='gpt-4o-mini'`, target fallback `deepseek-chat`, judge `gpt-4o`); still only partially aligned with repo defaults (`glm4`, `deepseek_v3`, `gpt4o`). |
| Visual reasoning and image model parameterization missing | ❌ | ✅ Fixed | New `AttackParameter`s `text_to_image_model` and `enable_visual_path` were added and documented in `abj_gen.py:87–100`, so the text-to-image and visual-path parameters now exist even though they are non-functional. |
| Target model defaults differ from repo gold standard | ⚠️ | ⚠️ Partially Fixed | Target fallback continues to use `deepseek-chat` instead of `deepseek_v3`; no change this iteration. |
| Evaluation differences vs repo’s judge model not documented | ✅ | ✅ Fixed | Comment explaining the use of `WenwenOpenAIChatEvaluator` instead of the repo’s `judge_model + judge_prompt` remains in place (`abj_gen.py:362–370`). |
| Multi-sample success condition deviates from reference pipeline | ❌ | ✅ Fixed | Success gating now checks only the first judgment (`judgements[0]`) after multi-sampling (`abj_gen.py:402–406,443–445`), matching `pipeline_execution.py:43–60` for the single-target-model case. |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Query-to-neutral-data transformation | ✅ | ✅ | `_transform_query_to_neutral_data` still mirrors `get_data` in `data_preparation.py:13–38`, including regex-based JSON extraction and `<data>` fallback on parse failure. |
| Chain-of-thought attack prompt construction | ✅ | ✅ | `ABJ_ATTACK_PROMPT` and `_get_attack_prompt` remain unchanged and still match `ABJ_attack_prompt` in `pipeline_prompt.py:1–3`. |
| Toxicity adjustment logic (enhance vs reduce via refusal judge) | ✅ | ✅ | `_toxicity_adjustment` continues to follow `toxicity_adjustment` semantics: refusal → reduction, otherwise → enhancement, using the assistant model and JSON re-formatting. |
| Refusal detection prompt and usage | ✅ | ✅ | `DETAILED_JUDGE_PROMPT` and `_is_refusal` still align with `detailed_judge_prompt` in `pipeline_prompt.py:83–98`, returning refusal if the judge output contains `1`. |

**NEW Issues Found This Iteration:**
- No new semantic deviations were identified; remaining gaps are the missing visual/text-to-image attack path and partial misalignment of default model choices relative to the reference repo.

**Summary:**
- Fixed: 2 issues
- Partially Fixed: 3 issues
- Still Broken: 0 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2407.16205
- Attack: abj_gen
- Verdict: Not 100% Fidelity
- Coverage: 8/12 components (67%)
- Iteration: 3

## Executive Summary
The Iteration 3 `ABJAttack` implementation in `abj_gen.py` now exposes both textual and visual-related parameters and fully aligns its multi-sample search control with the official `ABJ-Attack` repository: `max_attack_rounds` governs repeated sampling, and success gating checks only the first judgment after each batch, matching `pipeline_execution.py`. The core textual ABJ loop (query transformation into `<data>`, chain-of-thought attack prompting, refusal-based toxicity adjustment, and robust JSON fallback) remains faithful to the paper and cloned repo. However, the visual/text-to-image attack pathway is still not implemented (despite parameters and documentation), and default model choices (especially assist and target defaults) remain only partially aligned with the repo’s gold-standard configuration. Consequently, while fidelity has improved relative to Iteration 2, the implementation still cannot be considered a fully faithful reproduction of the complete algorithm.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §ABJ, Attack Initiation | Transform harmful query into structured neutral textual data via assistant model and JSON parsing | `src/jbfoundry/attacks/generated/abj_gen.py:200–233`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/data_preparation.py:13–38` | ✅ | Still closely mirrors official `get_data`: same `query_transform` prompt, regex extraction of JSON, and `<data>`-formatted fallback when parsing fails. |
| §ABJ, Attack Initiation | Use assistant model for query transformation | `src/jbfoundry/attacks/generated/abj_gen.py:173–192,200–212`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/pipeline_prompt.py:15–27` | ✅ | `self.assist_model` is configured and used analogously to the repo assistant model (assistant generates JSON which is parsed into `<data>`). |
| §ABJ, Attack Initiation | Generate neutral visual (image) data via text-to-image model from attributes | — | ❌ | Implementation is still text-only: it never calls any image/visual or text-to-image model, whereas the plan and repo (`utils/text2img.py`, `ABJ_visual.py`, `pipeline/pipeline_prompt.py:6–13`) define a visual path. |
| §ABJ, Attack Execution | Chain-of-thought reasoning over textual personal data to infer task and steps | `src/jbfoundry/attacks/generated/abj_gen.py:117–120,266–276`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/data_analysis.py:5–8`; `pipeline/pipeline_prompt.py:1–3` | ✅ | `ABJ_ATTACK_PROMPT` and `_get_attack_prompt` still match the repo’s `ABJ_attack_prompt` template and usage. |
| §ABJ, Visual Path | Visual chain-of-thought reasoning prompt and visual attack path | — | ❌ | The implementation does not expose or use `ABJ_visual_attack_prompt` or any visual reasoning path present in the repo (`pipeline/pipeline_prompt.py:6–8`, `data_analysis.get_visual_attack_prompt`). |
| §ABJ, Attack Control | Iterative attack-execute–adjust loop with maximum toxicity adjustment rounds | `src/jbfoundry/attacks/generated/abj_gen.py:295–317,410–448`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/pipeline_execution.py:34–69`; `pipeline/toxicity_adjustment.py` | ✅ | For each failed stage, the implementation detects refusals using the last response, adjusts toxicity accordingly, regenerates an attack prompt, and repeats up to `max_adjustment_rounds`, matching the reference loop structure. |
| §ABJ, Search Control | Multiple response samples per prompt controlled by `max_attack_rounds` | `src/jbfoundry/attacks/generated/abj_gen.py:37–44,177–179,385–446`; `attacks_paper_info/2407.16205/ABJ-Attack/ABJ.py:8–19`; `pipeline/pipeline_execution.py:9–21,34–60` | ✅ | `max_attack_rounds` is parameterized and used to sample multiple responses per attack prompt; success is gated on the first judgment only, matching `generate_responses_and_judgements` + `pipeline_execution` for a single target model. |
| §ABJ, Toxicity Adjustment | Benign vs refusal classification and toxicity enhancement/reduction | `src/jbfoundry/attacks/generated/abj_gen.py:278–317`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/toxicity_adjustment.py`; `pipeline/pipeline_prompt.py:30–44,47–61,83–98` | ✅ | Uses a dedicated refusal judge (`DETAILED_JUDGE_PROMPT`) and two prompts (`TOXICITY_ENHANCEMENT_PROMPT` / `TOXICITY_REDUCTION_PROMPT`) exactly as in the repo: refusal → reduction, otherwise → enhancement. |
| §ABJ, Refusal Detection | Separate judge model and prompt for refusal detection | `src/jbfoundry/attacks/generated/abj_gen.py:151–165,278–293`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/pipeline_prompt.py:83–98`; `pipeline/toxicity_adjustment.py` | ✅ | Implements the same detailed refusal-judging prompt and uses a dedicated judge model to decide between enhancement and reduction. |
| §ABJ, Visual & Dual-Modality Design | Joint textual and visual reasoning pathway for ABJ | — | ❌ | Attack remains purely textual and does not cover the visual/dual-modality aspects described in the blueprint and supported in the repo (e.g., `ABJ_visual.py`, `utils/text2img.py`). |
| §ABJ, Parameterization | Model parameters and defaults (assist, judge, target, temps, text-to-image) | `src/jbfoundry/attacks/generated/abj_gen.py:37–101,173–199,352–370`; `attacks_paper_info/2407.16205/ABJ-Attack/ABJ.py:8–19`; `ABJ-Attack/readme.md:31–47` | ⚠️ | Parameters exist and are wired; judge defaults now match (`gpt-4o`), and text-to-image parameters are exposed, but assist model default (`gpt-4o-mini`) and target default (`deepseek-chat` vs `deepseek_v3`) still diverge from the repo’s documented choices. |
| §ABJ, Robustness | Fallback behavior on malformed JSON from assistant | `src/jbfoundry/attacks/generated/abj_gen.py:200–233,235–264`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/data_preparation.py:21–38` | ✅ | Continues to use the same pattern-based JSON extraction and default `<data>` backup to handle parse failures, consistent with the official code’s robustness behavior. |

## Parameter Mapping
| Paper / Repo Parameter | Code Parameter | Type | Default (Paper/Repo) | Default (Code) | Match (✅/⚠️/❌) | Notes |
|---|---|---|---|---|---|---|
| Harmful query `HB` / task | `goal` (in `generate_attack`) | str | None (required input) | None (required input) | ✅ | Harmful query is consistently passed as `goal` and used as the question in evaluator input. |
| `max_adjustment_rounds` | `max_adjustment_rounds` (AttackParameter) | int | 5 (`ABJ.py:16`, README) | 5 | ✅ | Matches reference default and semantics; controls number of toxicity adjustment loops. |
| `max_attack_rounds` | `max_attack_rounds` (AttackParameter) | int | 1 in `ABJ.py:15` (README suggests 3) | 1 | ✅ | Parameter is exposed and controls samples per prompt; success gating now matches the repo’s use of the first judgment only. |
| Assist model name `assist_model` | `assist_model` (AttackParameter) | str | `glm4` (`ABJ.py:11`) | `gpt-4o-mini` | ❌ | Same role but different default model name than the reference repo; description notes this as a functionally-equivalent alternative. |
| Assist model provider | `assist_provider` (AttackParameter) | str | Local `LLMModel` backend | `wenwen` | ⚠️ | Different provider layer due to framework integration; role is equivalent but not one-to-one with repo’s implementation. |
| Judge model name `judge_model` | `judge_model` (AttackParameter) | str | `gpt4o` (`ABJ.py:12`) | `gpt-4o` | ✅ | Matches the reference default (notation difference only). |
| Judge model provider | `judge_provider` (AttackParameter) | str | Local `LLMModel` backend | `wenwen` | ⚠️ | As above, provider differs but role (refusal detection) is equivalent. |
| Text-to-image model | `text_to_image_model` (AttackParameter) | str | `gpt-image-1` (blueprint / repo utilities) | `gpt-image-1` | ⚠️ | Parameter name, type, and default align with the blueprint, but it is not used anywhere in the current implementation. |
| Visual path enable flag | `enable_visual_path` (AttackParameter) | bool | (not explicitly parameterized in paper) | `False` | ⚠️ | Extra flag introduced for API compatibility; currently has no effect because the visual path is unimplemented. |
| Assist model temperature | `temperature` (AttackParameter) | float | 1.0 (from `LLMModel(..., temperature=1)`) | 1.0 | ✅ | Matches the intended behavior for the assistant model. |
| Target model name `target_model` | `args.target_model` in repo; `args.model` → internal `target_llm` here | str | `deepseek_v3` (`ABJ.py:10`) | `deepseek-chat` (via `getattr(self.args, 'model', 'deepseek-chat')`) | ⚠️ | Closer to the repo’s DeepSeek default than Iteration 1, but still not the exact documented default. |
| Judge for harmfulness | `judge_model` + `judge_prompt` (repo) vs `evaluator` (`WenwenOpenAIChatEvaluator`) | object / callable | Custom `judge_model` + `judge_prompt` | Framework evaluator | ⚠️ | Semantics (detects harmfulness) align, but implementation uses the framework’s evaluation module rather than the repo’s explicit prompt; this deviation is now explicitly documented. |
| Refusal judge | `judge_model` + `detailed_judge_prompt` | object / prompt | Present (repo) | Present | ✅ | Same prompt content and role for refusal detection. |

## Misalignments / Missing Items

1. **Visual/text-to-image pathway still not implemented**
   - **Paper/Plan citation**: The blueprint in `2407.16205_plan.md:23–33` describes `transform_query_to_neutral_data(harmful_query) -> Tuple[str, Image]`, explicitly including both textual and visual data; model roles also include a text-to-image model (`gpt-image-1`) at `plan:30–31,89–90`. The repo defines visual prompts and utilities in `ABJ-Attack/pipeline/pipeline_prompt.py:6–13`, `ABJ_visual.py`, and `utils/text2img.py`.  
   - **Expected behavior**: The ABJ implementation should be able to generate and use visual data as part of the reasoning-based jailbreak (at least as an optional, parameterized path).  
   - **Observed behavior**: `ABJAttack` only handles a textual `<data>` string; the module docstring now explicitly states that the visual path is not implemented, and text-to-image parameters exist, but there is still no code path that generates or consumes images.  
   - **Impact**: Omits a modality that the plan and repo consider part of the ABJ design, reducing fidelity for multi-modal attack scenarios despite the clearer documentation and parameter surface.

2. **Default model choices remain partially misaligned with the reference repository**
   - **Paper/Repo citation**: `ABJ-Attack/ABJ.py:10–12` sets `target_model='deepseek_v3'`, `assist_model='glm4'`, `judge_model='gpt4o'` by default; `readme.md:31–47` documents these roles and parameters.  
   - **Expected behavior**: Within this framework, model types/providers can change, but default model names should align with the reference when feasible, or clear justification should be given.  
   - **Observed behavior**: `ABJAttack.PARAMETERS` now match the judge model default (`gpt-4o`) and move the target default toward DeepSeek (`deepseek-chat`), but the assist model default remains `gpt-4o-mini`, and the target name still does not match `deepseek_v3`; text-to-image parameters are present but unused.  
   - **Impact**: These differences reduce strict reproducibility relative to the gold-standard repo and can affect empirical performance, though they do not change the core textual algorithm.

## Extra Behaviors Not in Paper
- **Framework evaluator integration for harmfulness judgment**:  
  The implementation uses `WenwenOpenAIChatEvaluator` from `src/jbfoundry/evaluation/base.py` (`abj_gen.py:362–370`) instead of the repo’s custom `judge_prompt` + `judge_model` pair (`pipeline_execution.py:9–21`, `pipeline/pipeline_prompt.py:64–80`). This is consistent with the framework’s requirements and explicitly documented, but it is not described in the paper or ABJ-only repo.

- **Prompt-only fallback mode**:  
  If no target model or evaluator is passed, `generate_attack` returns a single attack prompt without running the adjustment loop (`abj_gen.py:378–453`). This “prompt-only” mode is not present in the official ABJ pipeline but can be useful in this framework and does not contradict the paper.

- **Non-functional visual parameters for API compatibility**:  
  `text_to_image_model` and `enable_visual_path` are exposed as parameters and documented as non-functional in this framework (`abj_gen.py:87–100`), providing an API surface that mirrors the paper/repo but without behavior.

## Required Changes to Reach 100%

1. **Implement (or robustly emulate) the visual/text-to-image pathway**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:37–101,200–233,295–448`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/pipeline_prompt.py:6–13`; `ABJ-Attack/utils/text2img.py`, `ABJ_visual.py`.  
   - **Change**:
     - Wire `text_to_image_model` and `enable_visual_path` into the attack logic so that, when enabled, the attack generates a visual representation from the `<data>` attributes (following `visual_description_generation` and `generate_visual_descriptions`) and uses it in an ABJ-style visual reasoning prompt (`ABJ_visual_attack_prompt`).  
     - If the framework fundamentally cannot support images, clearly separate this implementation as a “text-only ABJ variant” and document that it does not cover the visual branch of the algorithm required for full fidelity.  
   - **Justification**: Restores the dual-modality behavior described by the paper and gold-standard repo, or explicitly scopes the implementation to a subset of the algorithm.

2. **Further align or explicitly justify default model choices**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:37–101,173–199,352–370`.  
   - **Change**:
     - Adjust `assist_model` and target model defaults to mirror the reference repo (`glm4`, `deepseek_v3`) where these models are available in the deployment environment, or expand parameter descriptions to explicitly justify the deviations (e.g., unavailability of `glm4`/`deepseek_v3` in this framework).  
   - **Justification**: Improves strict reproducibility relative to the gold-standard repo and clarifies any unavoidable divergences.

## Final Verdict
**Not 100% Fidelity** — The Iteration 3 implementation fully aligns its multi-sample search control with the reference `ABJ-Attack` repository and provides parameterization for visual models, while preserving strong fidelity for the textual ABJ loop (query transformation, chain-of-thought prompting, refusal-based toxicity adjustment, and robustness to malformed JSON). Nonetheless, it still omits the visual/text-to-image pathway and retains only partially aligned default model choices, so it cannot yet be considered a completely faithful reproduction of the full algorithm described by the paper and official code.

## Audit Iteration 2 - 2025-12-26

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Missing `max_attack_rounds` search control | ❌ | ✅ Fixed | Parameter `max_attack_rounds` added and used to control multi-sample querying in `src/jbfoundry/attacks/generated/abj_gen.py:33–40,159–161,364–383,403–422`. |
| No visual / text-to-image pathway for ABJ | ❌ | ⚠️ Partially Fixed | Limitation is now explicitly documented in the module docstring (`abj_gen.py:10–16`), but no visual or text-to-image pipeline is implemented. |
| Default model choices differ from reference repository (assist/judge/target) | ❌ | ⚠️ Partially Fixed | Judge model default now matches `gpt4o` and target fallback is closer to the repo (`deepseek-chat` vs `deepseek_v3`), but assist model and exact target model name still diverge. |
| Visual reasoning and image model parameterization missing | ❌ | ❌ Still Broken | No parameter is exposed for a text-to-image model or visual pathway in `ABJAttack.PARAMETERS`. |
| Target model defaults differ from repo gold standard | ❌ | ⚠️ Partially Fixed | Fallback target model now uses a DeepSeek-style model (`deepseek-chat`) instead of `gpt-3.5-turbo`, which is closer to `deepseek_v3` but not identical. |
| Evaluation differences vs repo’s judge model not documented | ⚠️ | ✅ Fixed | Added explicit comment explaining use of framework `WenwenOpenAIChatEvaluator` instead of the repo’s `judge_model + judge_prompt` (`abj_gen.py:341–349`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Query-to-neutral-data transformation | ✅ | ✅ | `_transform_query_to_neutral_data` remains aligned with `get_data` in `data_preparation.py`, including regex JSON extraction and `<data>` fallback. |
| Chain-of-thought attack prompt construction | ✅ | ✅ | `ABJ_ATTACK_PROMPT` and `_get_attack_prompt` unchanged and still match `ABJ_attack_prompt` in `pipeline_prompt.py`. |
| Toxicity adjustment logic (enhance vs reduce via refusal judge) | ✅ | ✅ | `_toxicity_adjustment` still mirrors `toxicity_adjustment.py`, using refusal detection (`detailed_judge_prompt`) to choose between enhancement and reduction. |
| Refusal detection prompt and usage | ✅ | ✅ | `DETAILED_JUDGE_PROMPT` and `_is_refusal` continue to match the repo’s logic (return 1 ⇒ refusal). |

**NEW Issues Found This Iteration:**
- Multi-sample success condition deviates from the reference pipeline: this implementation treats the attack as successful if **any** sampled response is jailbroken, while the repo’s `pipeline_execution.generate_responses_and_judgements` and subsequent control logic gate toxicity adjustment based on an `all('1' in judgement_results[0])` condition on the first judgment per target model (`pipeline_execution.py:9–21,43–60`). This behavior is more intuitive and closer to the paper’s description (success on any harmful response) but does not exactly match the cloned repo’s control flow.

**Summary:**
- Fixed: 2 issues
- Partially Fixed: 3 issues
- Still Broken: 1 issue
- Regressions: 0 issues
- New Issues: 1 issue

# Implementation Fidelity Verdict
- Paper ID: 2407.16205
- Attack: abj_gen
- Verdict: Not 100% Fidelity
- Coverage: 7/12 components (58%)
- Iteration: 2

## Executive Summary
The updated `ABJAttack` in `abj_gen.py` now exposes and uses the `max_attack_rounds` parameter to perform multi-sample querying per attack prompt, better matching the search-control behavior described in the paper and official `ABJ-Attack` repository. The core textual ABJ loop remains faithful: the implementation transforms harmful queries into neutral `<data>` text via an assistant model, constructs a chain-of-thought attack prompt, evaluates target responses for harmfulness using the framework evaluator, and iteratively adjusts toxicity via enhancement/reduction prompts conditioned on refusal detection. However, the visual/text-to-image pathway is still absent (despite being documented as unsupported), model defaults only partially align with the reference repo, and the multi-sample success condition now diverges from the cloned pipeline’s exact `all('1')` gating logic. As a result, while fidelity to the textual branch has improved, the implementation still falls short of 100% fidelity to the full algorithm described by the paper and gold-standard repo.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §ABJ, Attack Initiation | Transform harmful query into structured neutral textual data via assistant model and JSON parsing | `src/jbfoundry/attacks/generated/abj_gen.py:182–215`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/data_preparation.py:13–38` | ✅ | Still closely mirrors official `get_data`: same `query_transform` prompt, regex extraction of JSON, and `<data>`-formatted fallback when parsing fails. |
| §ABJ, Attack Initiation | Use assistant model for query transformation | `src/jbfoundry/attacks/generated/abj_gen.py:155–173,192–194`; `ABJ-Attack/pipeline/pipeline_prompt.py:15–27` | ✅ | `self.assist_model` is configured and used analogously to the repo assistant model (assistant generates JSON which is parsed into `<data>`). |
| §ABJ, Attack Initiation | Generate neutral visual (image) data via text-to-image model from attributes | — | ❌ | Implementation is text-only: it never calls any image/visual or text-to-image model, whereas the plan and repo (`utils/text2img.py`, `ABJ_visual.py`, `pipeline/pipeline_prompt.py:6–13`) define a visual path. |
| §ABJ, Attack Execution | Chain-of-thought reasoning over textual personal data to infer task and steps | `src/jbfoundry/attacks/generated/abj_gen.py:99–101,248–258`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/data_analysis.py:5–8`; `pipeline/pipeline_prompt.py:1–3` | ✅ | `ABJ_ATTACK_PROMPT` and `_get_attack_prompt` still match the repo’s `ABJ_attack_prompt` template and usage. |
| §ABJ, Visual Path | Visual chain-of-thought reasoning prompt and visual attack path | — | ❌ | The implementation does not expose or use `ABJ_visual_attack_prompt` or any visual reasoning path present in the repo (`pipeline/pipeline_prompt.py:6–8`, `data_analysis.get_visual_attack_prompt`). |
| §ABJ, Attack Control | Iterative attack-execute–adjust loop with maximum toxicity adjustment rounds | `src/jbfoundry/attacks/generated/abj_gen.py:277–298,351–356,385–425`; `pipeline/pipeline_execution.py:34–69`; `pipeline/toxicity_adjustment.py:7–18` | ✅ | For each failed stage, the implementation detects refusals, adjusts toxicity accordingly, regenerates an attack prompt, and repeats up to `max_adjustment_rounds`, matching the reference loop structure. |
| §ABJ, Search Control | Multiple response samples per prompt controlled by `max_attack_rounds` | `src/jbfoundry/attacks/generated/abj_gen.py:33–40,159–161,359–383,399–422`; `attacks_paper_info/2407.16205/ABJ-Attack/ABJ.py:8–19`; `pipeline/pipeline_execution.py:9–21,34–45` | ⚠️ | `max_attack_rounds` is now parameterized and used to sample multiple responses per attack prompt, but success is triggered on **any** jailbroken response rather than replicating the repo’s `all('1')`-based gating on the first judgment per target. |
| §ABJ, Toxicity Adjustment | Benign vs refusal classification and toxicity enhancement/reduction | `src/jbfoundry/attacks/generated/abj_gen.py:260–275,277–298`; `pipeline/toxicity_adjustment.py:7–18`; `pipeline/pipeline_prompt.py:30–44,47–61,83–98` | ✅ | Uses a dedicated refusal judge (`DETAILED_JUDGE_PROMPT`) and two prompts (`TOXICITY_ENHANCEMENT_PROMPT` / `TOXICITY_REDUCTION_PROMPT`) exactly as in the repo: refusal → reduction, otherwise → enhancement. |
| §ABJ, Refusal Detection | Separate judge model and prompt for refusal detection | `src/jbfoundry/attacks/generated/abj_gen.py:63–67,155–167,260–275`; `pipeline/pipeline_prompt.py:83–98`; `pipeline/toxicity_adjustment.py:7–18` | ✅ | Implements the same detailed refusal-judging prompt and uses a dedicated judge model to decide between enhancement and reduction. |
| §ABJ, Visual & Dual-Modality Design | Joint textual and visual reasoning pathway for ABJ | — | ❌ | Attack remains purely textual and does not cover the visual/dual-modality aspects described in the blueprint and supported in the repo (e.g., `ABJ_visual.py`, `utils/text2img.py`). |
| §ABJ, Parameterization | Model parameters and defaults (assist, judge, target, temps) | `src/jbfoundry/attacks/generated/abj_gen.py:33–83,155–167,333–339`; `ABJ-Attack/ABJ.py:8–19`; `ABJ-Attack/readme.md:31–47` | ⚠️ | Parameters exist and are wired; judge defaults now match (`gpt4o`), but assist model (`gpt-4o-mini`) and target default (`deepseek-chat` vs `deepseek_v3`) still diverge from the repo’s documented choices. |
| §ABJ, Robustness | Fallback behavior on malformed JSON from assistant | `src/jbfoundry/attacks/generated/abj_gen.py:192–215,217–246`; `pipeline/data_preparation.py:21–38` | ✅ | Continues to use the same pattern-based JSON extraction and default `<data>` backup to handle parse failures, consistent with the official code’s robustness behavior. |

## Parameter Mapping
| Paper / Repo Parameter | Code Parameter | Type | Default (Paper/Repo) | Default (Code) | Match (✅/⚠️/❌) | Notes |
|---|---|---|---|---|---|---|
| Harmful query `HB` / task | `goal` (in `generate_attack`) | str | None (required input) | None (required input) | ✅ | Harmful query is consistently passed as `goal` and used as the question in evaluator input. |
| `max_adjustment_rounds` | `max_adjustment_rounds` (AttackParameter) | int | 5 (`ABJ.py:16`, README) | 5 | ✅ | Matches reference default and semantics; controls number of toxicity adjustment loops. |
| `max_attack_rounds` | `max_attack_rounds` (AttackParameter) | int | 1 in `ABJ.py:15` (README suggests 3) | 1 | ⚠️ | Parameter is now exposed and controls samples per prompt, but the success criterion (`any` vs repo’s `all('1')` on first judgments) is not identical. |
| Assist model name `assist_model` | `assist_model` (AttackParameter) | str | `glm4` (`ABJ.py:11`) | `gpt-4o-mini` | ❌ | Same role but different default model name than the reference repo; description notes this as an “available alternative”. |
| Assist model provider | `assist_provider` (AttackParameter) | str | Local `LLMModel` backend | `wenwen` | ⚠️ | Different provider layer due to framework integration; role is equivalent but not one-to-one with repo’s implementation. |
| Judge model name `judge_model` | `judge_model` (AttackParameter) | str | `gpt4o` (`ABJ.py:12`) | `gpt-4o` | ✅ | Now matches the reference default (notation difference only). |
| Judge model provider | `judge_provider` (AttackParameter) | str | Local `LLMModel` backend | `wenwen` | ⚠️ | As above, provider differs but role (refusal detection) is equivalent. |
| Text-to-image model (e.g., `gpt-image-1`) | — | str | Specified in paper/plan for image generation | — | ❌ | No parameter or usage for a text-to-image model in this implementation. |
| Assist model temperature | `temperature` (AttackParameter) | float | 1.0 (from `LLMModel(..., temperature=1)`) | 1.0 | ✅ | Matches the intended behavior for the assistant model. |
| Target model name `target_model` | `args.target_model` in repo; `args.model` → internal `target_llm` here | str | `deepseek_v3` (`ABJ.py:10`) | `deepseek-chat` (via `getattr(self.args, 'model', 'deepseek-chat')`) | ⚠️ | Closer to the repo’s DeepSeek default than before, but still not the exact documented default. |
| Judge for harmfulness | `judge_model` + `judge_prompt` (repo) vs `evaluator` (`WenwenOpenAIChatEvaluator`) | object / callable | Custom `judge_model` + `judge_prompt` | Framework evaluator | ⚠️ | Semantics (detects harmfulness) align, but implementation uses the framework’s evaluation module rather than the repo’s explicit prompt; now explicitly documented. |
| Refusal judge | `judge_model` + `detailed_judge_prompt` | object / prompt | Present (repo) | Present | ✅ | Same prompt content and role for refusal detection. |

## Misalignments / Missing Items

1. **Multi-sample success condition and gating differ from reference pipeline**
   - **Paper/Repo citation**: `ABJ-Attack/ABJ.py:8–19` and `pipeline/pipeline_execution.py:9–21,34–60` define `max_attack_rounds` and use it inside `generate_responses_and_judgements`, with downstream control flow driven by `all('1' in judgement_results[0] for judgement_results in judgement_results_list)`.  
   - **Expected behavior**: For each attack prompt, the attack should sample multiple responses (controlled by `max_attack_rounds`) and decide whether to proceed to toxicity adjustment based on a gating condition consistent with the reference implementation.  
   - **Observed behavior**: `ABJAttack.generate_attack` samples `max_attack_rounds` responses but treats the attack as successful if **any** sample is judged jailbroken, returning immediately and never exploring the remaining samples for that round. This deviates from the repo’s `all('1')`-based gating on the first judgments, and also from its behavior of collecting all samples for logging before adjusting.  
   - **Impact**: Changes the effective search/control dynamics and stopping condition relative to the cloned repo. While arguably more intuitive and closer to “success on any harmful output,” it is not a faithful reproduction of the reference pipeline.

2. **No visual / text-to-image pathway implemented**
   - **Paper/Plan citation**: The blueprint in `2407.16205_plan.md:23–33` describes `transform_query_to_neutral_data(harmful_query) -> Tuple[str, Image]`, explicitly including both textual and visual data; model roles also include a text-to-image model (`gpt-image-1`) at `plan:30–31,89–90`. The repo defines visual prompts and utilities in `ABJ-Attack/pipeline/pipeline_prompt.py:6–13`, `ABJ_visual.py`, and `utils/text2img.py`.  
   - **Expected behavior**: The ABJ implementation should be able to generate and use visual data as part of the reasoning-based jailbreak (at least as an optional, parameterized path).  
   - **Observed behavior**: `ABJAttack` only handles a textual `<data>` string; the module docstring clarifies that the visual path is not implemented due to framework constraints, but there is no actual visual generation or usage.  
   - **Impact**: Omits a modality that the plan and repo consider part of the ABJ design, reducing fidelity for multi-modal attack scenarios despite the documented limitation.

3. **Visual reasoning and image model parameterization still missing**
   - **Paper/Plan citation**: Model roles in `2407.16205_plan.md:87–91` explicitly include a **Text-to-Image Model** used during attack initiation.  
   - **Expected behavior**: A configuration parameter (even if sometimes unused) should exist for the text-to-image model to match the algorithm specification and repo.  
   - **Observed behavior**: No parameter or placeholder exists in `ABJAttack.PARAMETERS` for a text-to-image model or visual pathway.  
   - **Impact**: The implementation cannot even be configured to use a visual path, further limiting fidelity to the paper’s dual-modality threat model.

4. **Default model choices only partially aligned with the reference repository**
   - **Paper/Repo citation**: `ABJ-Attack/ABJ.py:10–12` sets `target_model='deepseek_v3'`, `assist_model='glm4'`, `judge_model='gpt4o'` by default; `readme.md:31–47` documents these roles and parameters.  
   - **Expected behavior**: Within this framework, model types/providers can change, but default model names should align with the reference when feasible, or clear justification should be given.  
   - **Observed behavior**: `ABJAttack.PARAMETERS` now match the judge model default (`gpt-4o`) and move the target default toward DeepSeek (`deepseek-chat`), but the assist model default remains `gpt-4o-mini`, and the target name still does not match `deepseek_v3`.  
   - **Impact**: These differences reduce strict reproducibility relative to the gold-standard repo and can affect empirical performance, though they do not change the core algorithmic structure.

## Extra Behaviors Not in Paper
- **Framework evaluator integration for harmfulness judgment**:  
  The implementation uses `WenwenOpenAIChatEvaluator` from `src/jbfoundry/evaluation/base.py` (`abj_gen.py:341–349`) instead of the repo’s custom `judge_prompt` + `judge_model` pair (`pipeline_execution.py:9–21`, `pipeline/pipeline_prompt.py:64–80`). This is consistent with the framework’s requirements and now explicitly documented, but it is not described in the paper or ABJ-only repo.

- **Prompt-only fallback mode**:  
  If no target model or evaluator is passed, `generate_attack` returns a single attack prompt without running the adjustment loop (`abj_gen.py:357–356,427–430`). This “prompt-only” mode is not present in the official ABJ pipeline but can be useful in this framework and does not contradict the paper.

- **JSON parsing robustness mirrored but generalized**:  
  Both `_transform_query_to_neutral_data` and `_format_json_to_data` reuse the same robust regex+fallback pattern (`abj_gen.py:192–215,217–246`), covering both initial data generation and subsequent toxicity adjustments, whereas the original ABJ code separates parsing across `get_data` and `format_json_to_data`.

## Required Changes to Reach 100%

1. **Align multi-sample success condition and gating with reference pipeline (or clearly justify divergence)**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:33–40,359–383,399–422`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/pipeline_execution.py:9–21,43–60`.  
   - **Change**:
     - Either replicate the repo’s gating semantics (e.g., base adjustment on an `all()` condition over judgments from the samples, or at least over the first-round samples), or add a configuration flag to choose between “any-sample success” and “repo-compatible gating,” documenting the default choice.  
   - **Justification**: Restores fidelity to the cloned repo’s control flow while still allowing the more intuitive behavior as a documented deviation if desired.

2. **Add optional visual / text-to-image path (or stronger documentation of non-coverage)**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:33–83,99–101,182–215,300–425`.  
   - **Change**:
     - Introduce parameters for a text-to-image model and (optionally) a flag to enable/disable the visual path.  
     - When enabled, generate a visual representation from the `<data>` attributes (following `utils/text2img.py` and `visual_description_generation` in `pipeline/pipeline_prompt.py:11–13`) and extend the reasoning prompt or target model inputs to include visual data.  
     - If the framework fundamentally cannot support images, expand the docstring and parameter docs to explicitly state that only the textual branch of ABJ is supported and that visual aspects of the algorithm are out of scope.  
   - **Justification**: Aligns with the algorithm description that includes both textual and visual data; at minimum, makes this limitation explicit and discoverable.

3. **Expose text-to-image model parameter even if unimplemented**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:33–83`.  
   - **Change**:
     - Add an `AttackParameter` for a text-to-image model name (and possibly provider), clearly marked as “currently unused in this framework” if actual image support cannot be wired in.  
   - **Justification**: Provides a configuration surface that mirrors the paper and repo, easing future extension to full multi-modal support.

4. **Further align default model choices or clearly document deviations**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:33–83,333–339`.  
   - **Change**:
     - Adjust `assist_model` default to `glm4` (or the closest available equivalent) and change the fallback `model_name` for `target_llm` to `deepseek_v3` if available.  
     - If these models are not available in the deployment environment, update parameter descriptions to explicitly note the divergence from the repo’s defaults and its rationale.  
   - **Justification**: Improves strict reproducibility relative to the gold-standard repo without altering the algorithmic logic.

## Final Verdict
**Not 100% Fidelity** — The implementation now exposes search-control via `max_attack_rounds` and maintains strong fidelity for the textual ABJ loop (query transformation, chain-of-thought attack prompt, refusal-based toxicity adjustment, and robustness to malformed JSON). However, it still omits the visual/text-to-image pathway, only partially aligns default model choices with the reference repository, and diverges from the cloned pipeline’s exact multi-sample gating semantics, so it cannot yet be considered a fully faithful reproduction of the paper and official code.

# Implementation Fidelity Verdict
- Paper ID: 2407.16205
- Attack: abj_gen
- Verdict: Not 100% Fidelity
- Coverage: 7/12 components (58%)
- Iteration: 1

## Executive Summary
The implemented `ABJAttack` in `abj_gen.py` captures the core textual analyzing-based jailbreak loop described in the paper and the official `ABJ-Attack` repository: it transforms a harmful query into neutral `<data>` text using an assistant model, constructs a chain-of-thought attack prompt, evaluates target responses for harmfulness, and iteratively adjusts toxicity via separate enhancement/reduction prompts conditioned on refusal detection. However, several important aspects of the reference implementation are missing or misaligned: the visual/text-to-image pathway is not implemented, the `max_attack_rounds` sampling control from the official code is not exposed or used (effectively fixing it to 1), and default model choices differ from the reference repository. These deviations alter the search behavior and coverage of the original algorithm, so the implementation cannot be considered 100% faithful despite matching most of the core textual logic.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §ABJ, Attack Initiation | Transform harmful query into structured neutral textual data via assistant model and JSON parsing | `src/jbfoundry/attacks/generated/abj_gen.py:166–199`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/data_preparation.py:13–38` | ✅ | Implementation closely mirrors official `get_data`: same `query_transform` prompt, regex extraction of JSON, and `<data>`-formatted fallback when parsing fails. |
| §ABJ, Attack Initiation | Use assistant model for query transformation | `src/jbfoundry/attacks/generated/abj_gen.py:145–157,176–178` | ✅ | `self.assist_model` is configured and used exactly as in the repo (assistant model generates JSON which is parsed into `<data>`). |
| §ABJ, Attack Initiation | Generate neutral visual (image) data via text-to-image model from attributes | — | ❌ | The implementation only returns textual `<data>` and never calls any image/visual or text-to-image model, whereas the plan and repo (`ABJ-Attack/utils/text2img.py`, `ABJ_visual.py`, `pipeline/pipeline_prompt.py:6–13`) define a visual path. |
| §ABJ, Attack Execution | Chain-of-thought reasoning over textual personal data to infer task and steps | `src/jbfoundry/attacks/generated/abj_gen.py:84–86,232–242`; `attacks_paper_info/2407.16205/ABJ-Attack/pipeline/data_analysis.py:5–8`; `pipeline/pipeline_prompt.py:1–3` | ✅ | `ABJ_ATTACK_PROMPT` and `_get_attack_prompt` match the paper and repo’s `ABJ_attack_prompt` template and usage. |
| §ABJ, Visual Path | Visual chain-of-thought reasoning prompt and visual attack path | — | ❌ | The implementation does not expose or use `ABJ_visual_attack_prompt` or any visual reasoning path present in the repo (`pipeline/pipeline_prompt.py:6–8`, `data_analysis.get_visual_attack_prompt`). |
| §ABJ, Attack Control | Iterative attack-execute–adjust loop with maximum toxicity adjustment rounds | `src/jbfoundry/attacks/generated/abj_gen.py:284–382`; `pipeline/pipeline_execution.py:34–69`; `pipeline/toxicity_adjustment.py:7–18` | ✅ | For each failed attempt, the implementation detects refusals, adjusts toxicity accordingly, regenerates an attack prompt, and repeats up to `max_adjustment_rounds`, matching the reference loop structure. |
| §ABJ, Search Control | Multiple response samples per prompt controlled by `max_attack_rounds` | `attacks_paper_info/2407.16205/ABJ-Attack/ABJ.py:8–19`; `pipeline/pipeline_execution.py:9–21,34–45` | ❌ | Official code samples multiple responses per attack prompt via `max_attack_rounds`, but `ABJAttack.generate_attack` performs a single query per round and does not expose or respect `max_attack_rounds`. |
| §ABJ, Toxicity Adjustment | Benign vs refusal classification and toxicity enhancement/reduction | `src/jbfoundry/attacks/generated/abj_gen.py:244–282`; `pipeline/toxicity_adjustment.py:7–18`; `pipeline/pipeline_prompt.py:47–61,83–98` | ✅ | Uses a dedicated refusal judge (`DETAILED_JUDGE_PROMPT`) and two prompts (`TOXICITY_ENHANCEMENT_PROMPT` / `TOXICITY_REDUCTION_PROMPT`) in a way that matches the reference logic: refusal → reduction, otherwise → enhancement; harmful responses terminate without further adjustment. |
| §ABJ, Refusal Detection | Separate judge model and prompt for refusal detection | `src/jbfoundry/attacks/generated/abj_gen.py:118–132,244–259`; `pipeline/pipeline_prompt.py:83–98`; `pipeline/toxicity_adjustment.py:7–18` | ✅ | Implements the same detailed refusal-judging prompt and uses a dedicated judge model to decide between enhancement and reduction. |
| §ABJ, Visual & Dual-Modality Design | Joint textual and visual reasoning pathway for ABJ | — | ❌ | The integrated attack is purely textual and does not cover the visual/dual-modality aspects described in the blueprint and supported in the repo (e.g., `ABJ_visual.py`, `utils/text2img.py`). |
| §ABJ, Parameterization | Model parameters and defaults (assist, judge, target, temps) | `src/jbfoundry/attacks/generated/abj_gen.py:25–68,140–164,312–323`; `ABJ-Attack/ABJ.py:8–19`; `ABJ-Attack/readme.md:31–47` | ❌ | Parameters exist and are wired, but defaults (e.g., assist/judge model names, target model) deviate from the reference repo’s documented choices. |
| §ABJ, Robustness | Fallback behavior on malformed JSON from assistant | `src/jbfoundry/attacks/generated/abj_gen.py:179–199,201–230`; `pipeline/data_preparation.py:21–38` | ✅ | Uses the same pattern-based JSON extraction and a default `<data>` backup to handle parse failures, consistent with the official code’s robustness behavior. |

## Parameter Mapping
| Paper / Repo Parameter | Code Parameter | Type | Default (Paper/Repo) | Default (Code) | Match (✅/❌) | Notes |
|---|---|---|---|---|---|---|
| Harmful query `HB` / task | `goal` (in `generate_attack`) | str | None (required input) | None (required input) | ✅ | Harmful query is consistently passed as `goal` and used as the question in evaluator input. |
| `max_adjustment_rounds` | `max_adjustment_rounds` (AttackParameter) | int | 5 (`ABJ.py:16`, README) | 5 | ✅ | Matches reference default and semantics; controls number of toxicity adjustment loops. |
| `max_attack_rounds` | — (not exposed) | int | 1 in `ABJ.py:15` (README states 3, but code default is 1) | Effectively 1, but not configurable | ❌ | Implementation does not expose or parameterize repeated sampling per prompt; behavior is effectively fixed and non-configurable. |
| Assist model name `assist_model` | `assist_model` (AttackParameter) | str | `glm4` (`ABJ.py:11`) | `gpt-4o-mini` | ❌ | Same role but different default model name than the reference repo. |
| Judge model name `judge_model` | `judge_model` (AttackParameter) | str | `gpt4o` (`ABJ.py:12`) | `gpt-4o-mini` | ❌ | Uses a different default judge model name than the official implementation. |
| Text-to-image model (e.g., `gpt-image-1`) | — | str | Specified in paper/plan for image generation | — | ❌ | No parameter or usage for a text-to-image model in this implementation. |
| Assist model temperature | `temperature` (AttackParameter) | float | 1.0 (implicit from repo: `LLMModel(..., temperature=1)`) | 1.0 | ✅ | Matches the intended behavior for the assistant model. |
| Target model name `target_model` | `args.model` → internal `target_llm` | str | `deepseek_v3` (`ABJ.py:10`) | `gpt-3.5-turbo` (fallback in this framework) | ❌ | Different default target model; some divergence is expected due to framework, but repo is specified as gold standard. |
| Judge for harmfulness | `judge_model` + `judge_prompt` (repo) vs `evaluator` (`WenwenOpenAIChatEvaluator`) | object / callable | Custom `judge_model` + `judge_prompt` | Framework evaluator | ⚠️ | Semantics (detects harmfulness) align, but implementation uses the framework’s evaluation module rather than the repo’s explicit prompt; acceptable adaptation but not identical. |
| Refusal judge | `judge_model` + `detailed_judge_prompt` | object / prompt | Present (repo) | Present | ✅ | Same prompt content and role for refusal detection. |

## Misalignments / Missing Items

1. **Missing `max_attack_rounds` search control**
   - **Paper/Repo citation**: ABJ CLI in `ABJ-Attack/ABJ.py:8–19` and README argument specification (`readme.md:31–41`) define `max_attack_rounds` as a key parameter controlling the number of iteration rounds per attack prompt. The pipeline uses this in `pipeline_execution.py:9–21,34–45` via `generate_responses_and_judgements`.
   - **Expected behavior**: For each attack prompt, the attack should be able to sample multiple responses from the target model (controlled by `max_attack_rounds`) before deciding success or triggering toxicity adjustment.
   - **Observed behavior**: `ABJAttack.generate_attack` (`abj_gen.py:284–382`) makes exactly one query per prompt per adjustment round and has no `max_attack_rounds` parameter; users cannot configure additional sampling. Behavior is effectively hard-coded to a single sample.
   - **Impact**: This changes the search space and can materially affect attack success rates; required search control is not exposed, so this is a blocking fidelity issue.

2. **No visual / text-to-image pathway for ABJ**
   - **Paper/Plan citation**: The blueprint in `2407.16205_plan.md:23–33` describes `transform_query_to_neutral_data(harmful_query) -> Tuple[str, Image]`, explicitly including both textual and visual data; model roles also include a text-to-image model (`gpt-image-1`) at `plan:30–31,89–90`. The repo defines visual prompts and utilities in `ABJ-Attack/pipeline/pipeline_prompt.py:6–13`, `ABJ_visual.py`, and `utils/text2img.py`.
   - **Expected behavior**: The ABJ implementation should be able to generate and use visual data as part of the reasoning-based jailbreak (at least as an optional, parameterized path).
   - **Observed behavior**: `ABJAttack` only handles a textual `<data>` string; there is no image generation, no visual prompt (`ABJ_visual_attack_prompt`), and no handling of images or multi-modal inputs.
   - **Impact**: Omits a modality that the plan and repo consider part of the ABJ design, reducing fidelity for multi-modal attack scenarios.

3. **Default model choices differ from the reference repository**
   - **Paper/Repo citation**: `ABJ-Attack/ABJ.py:10–12` sets `target_model='deepseek_v3'`, `assist_model='glm4'`, `judge_model='gpt4o'` by default; `readme.md:31–47` documents these roles and parameters.
   - **Expected behavior**: When integrating into this framework, model types/providers can change, but default model names should align with the reference when feasible, since the repo is specified as the gold standard for implementation details.
   - **Observed behavior**: `ABJAttack.PARAMETERS` (`abj_gen.py:25–68`) use `gpt-4o-mini` as the default for both assist and judge models, and `generate_attack` falls back to `gpt-3.5-turbo` for the target (`abj_gen.py:312–319`), which diverges from the reference defaults.
   - **Impact**: While behaviorally similar in spirit (all are high-capability LLMs), these differences reduce strict fidelity to the reference implementation and may change empirical performance.

4. **Visual reasoning and image model parameterization missing**
   - **Paper/Plan citation**: Model roles in `2407.16205_plan.md:87–91` explicitly include a **Text-to-Image Model** used during attack initiation.
   - **Expected behavior**: A configuration parameter (even if unused in some benchmarks) should exist for the text-to-image model to match the algorithm specification.
   - **Observed behavior**: No parameter or placeholder exists in `ABJAttack` for a text-to-image model; all logic is strictly text-only.
   - **Impact**: The implementation cannot reproduce the paper’s dual-modality threat model as described, limiting fidelity for multi-modal variants of ABJ.

5. **Target model defaults differ from repo gold standard**
   - **Paper/Repo citation**: `ABJ-Attack/ABJ.py:10` defaults `target_model='deepseek_v3'`, which is also reflected in the README’s examples.
   - **Expected behavior**: Within this framework, the default target model should, when possible, approximate the reference; at minimum, the divergence should be explicitly justified.
   - **Observed behavior**: `ABJAttack.generate_attack` (`abj_gen.py:312–319`) defaults to `gpt-3.5-turbo` with provider `wenwen`, which differs from the repo’s default target.
   - **Impact**: This affects which models are attacked by default, potentially altering reported performance and making strict reproduction of the reference setup harder without manual reconfiguration.

## Extra Behaviors Not in Paper
- **Framework evaluator integration for harmfulness judgment**:  
  The implementation uses `WenwenOpenAIChatEvaluator` from `src/jbfoundry/evaluation/base.py` (`abj_gen.py:321–327`) instead of the repo’s custom `judge_prompt` + `judge_model` pair (`pipeline_execution.py:9–21`, `pipeline/pipeline_prompt.py:64–80`). This is consistent with the framework’s requirements but not explicitly described in the paper or the ABJ-only repo.

- **Fallback behavior for missing `target_llm` / `evaluator`**:  
  If no target model or evaluator is passed, `generate_attack` returns a single attack prompt without running the adjustment loop (`abj_gen.py:384–387`). This “prompt-only” mode is not present in the official ABJ pipeline but can be useful in this framework.

- **JSON parsing robustness mirrored but generalized**:  
  Both `_transform_query_to_neutral_data` and `_format_json_to_data` reuse the same robust regex+fallback pattern (`abj_gen.py:179–199,211–230`), covering both initial data generation and subsequent toxicity adjustments, whereas the original ABJ code separates parsing across `get_data` and `format_json_to_data`.

## Required Changes to Reach 100%

1. **Expose and implement `max_attack_rounds` search control**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:25–68,284–382`.
   - **Change**:
     - Add an `AttackParameter` for `max_attack_rounds` with an integer type and a default matching the ABJ repo (1 per `ABJ.py`, or 3 if following the README, but be explicit).
     - Modify `generate_attack` to perform a configurable number of target model queries per attack prompt before evaluating success and/or triggering toxicity adjustment, mirroring `generate_responses_and_judgements` in `pipeline_execution.py:9–21`.
   - **Justification**: Restores a key search-control parameter required by the paper/repo and mandated by the auditing guidelines.

2. **Add optional visual / text-to-image path, or explicitly scope ABJ to text-only**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:25–68,134–139,284–382`.
   - **Change**:
     - Introduce parameters for a text-to-image model and (optionally) a flag to enable/disable the visual path.
     - When enabled, generate a visual representation from the `<data>` attributes (following the repo’s `utils/text2img.py` and `visual_description_generation` in `pipeline/pipeline_prompt.py:11–13`) and extend the reasoning prompt or target model inputs to include visual data.
     - If the framework fundamentally cannot support images, document this limitation explicitly in the class docstring and configuration, clarifying that only the textual branch of ABJ is implemented.
   - **Justification**: Aligns with the algorithm description that includes both textual and visual data; at minimum, makes the limitation explicit.

3. **Align default model names with ABJ-Attack repo where feasible**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:25–68,312–323`.
   - **Change**:
     - Adjust `assist_model` and `judge_model` defaults to mirror the reference repo (e.g., `glm4` and `gpt4o`) if available in this environment, or document explicitly in the parameter descriptions why different defaults are chosen.
     - Optionally, adjust the fallback `model_name` in `generate_attack` from `gpt-3.5-turbo` to a closer match to `deepseek_v3` (or expose it via the existing CLI args so users can match the reference setup easily).
   - **Justification**: Improves strict reproducibility relative to the gold-standard repo without changing the core algorithm.

4. **Document evaluation differences vs. repo’s judge model**
   - **Files / lines**: `src/jbfoundry/attacks/generated/abj_gen.py:321–327`.
   - **Change**:
     - Add a brief comment explaining that harmfulness evaluation uses the framework’s `WenwenOpenAIChatEvaluator` rather than the original `judge_model` + `judge_prompt`, and that this is an integration choice rather than a change in intended semantics.
   - **Justification**: Makes the deviation transparent and easier to reason about for future audits and reproductions.

## Final Verdict
**Not 100% Fidelity** — While the core textual ABJ loop (query transformation, chain-of-thought attack prompt, refusal-based toxicity adjustment, and harmfulness-terminating loop) faithfully mirrors the paper’s description and the official `ABJ-Attack` repository, the absence of multi-sample search control (`max_attack_rounds`), omission of the visual/text-to-image pathway, and divergent default model configurations prevent this implementation from achieving full fidelity to the reference algorithm.


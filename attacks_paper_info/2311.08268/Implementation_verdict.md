# Implementation Fidelity Verdict
- Paper ID: 2311.08268
- Attack: renellm_gen (ReNeLLM)
- Verdict: Not 100% Fidelity
- Coverage: 14/15 components (93%)
- Iteration: 1

## Executive Summary
The implementation in `renellm_gen.py` closely follows the ReNeLLM jailbreak framework described in the paper and blueprint: it correctly implements the two-phase structure (prompt rewriting and scenario nesting), all six rewriting strategies, the harmfulness-judging LLMeval component, and the three scenario templates. The main control flow of iteratively rewriting and then nesting the prompt is preserved, and key parameters such as the iteration cap \(T\) and the strategy/scenario sets are exposed and configurable. However, there are semantic deviations in the loop termination and fallback behavior: the implementation performs up to three additional rewriting attempts beyond the configured `max_iterations` and always returns a nested scenario prompt even when no rewritten prompt ever passes the harmfulness classifier, whereas Algorithm 1 returns the (unnested) current prompt after exhausting \(T\) iterations. These differences affect the search control and fallback behavior, so the implementation cannot be considered 100% faithful to the paper, even though most core components are correctly realized and integrated into this framework.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 Overall Framework | Two-phase pipeline: Prompt Rewriting + Scenario Nesting with iterative search | `src/jbfoundry/attacks/generated/renellm_gen.py:340–383` | ✅ | `generate_attack` implements iterative rewriting and nesting as described, within the framework’s attack interface. |
| §3.1 Step 1: Prompt Rewriting | Random combination of rewriting strategies applied to the prompt | `src/jbfoundry/attacks/generated/renellm_gen.py:302–321` | ✅ | `_rewrite_prompt` randomly selects 1–6 strategies, applies them sequentially, and returns a rewritten prompt. |
| §3.1 Function `rewrite_prompt` | Apply ordered strategies, then judge harmfulness via LLMeval | `src/jbfoundry/attacks/generated/renellm_gen.py:282–300` | ✅ | `_harmful_classification` uses a judge LLM to label text as harmful (1) or not (0) and `_rewrite_prompt` proceeds only when label=1, matching the paper’s LLMeval step. |
| §3.1 `apply_strategy` dispatcher | Map strategy identifiers to concrete rewriting functions | `src/jbfoundry/attacks/generated/renellm_gen.py:266–280` | ✅ | `_apply_strategy` dispatches on the six named strategies exactly as in the blueprint. |
| §3.1.1 Paraphrase with ≤6 words | Generate 5 paraphrase candidates and randomly choose one (≤6 words) | `src/jbfoundry/attacks/generated/renellm_gen.py:164–181` | ✅ | `_paraphrase` prompts for 5 short candidates (≤6 words) and randomly selects one after stripping numeric prefixes. |
| §3.1.2 Misspell Sensitive Words | Misspell or mispronounce sensitive/illegal words while preserving meaning | `src/jbfoundry/attacks/generated/renellm_gen.py:183–197` | ✅ | `_misspell_sensitive` matches the described behavior via an LLM prompt that rewrites sensitive words with misspellings. |
| §3.1.3 Alter Sentence Structure | Reorder words without changing semantics; do not alter tokens | `src/jbfoundry/attacks/generated/renellm_gen.py:199–213` | ✅ | `_alter_structure` asks the LLM to change word order only, consistent with the paper’s description. |
| §3.1.4 Insert Meaningless Characters | Insert meaningless foreign words without changing semantics | `src/jbfoundry/attacks/generated/renellm_gen.py:215–229` | ✅ | `_insert_characters` prompts the LLM to add meaningless foreign words while preserving meaning. |
| §3.1.5 Partial Translation | Partially translate 1–2 words into Chinese (mixed-language sentence) | `src/jbfoundry/attacks/generated/renellm_gen.py:231–247` | ✅ | `_partial_translation` requests 1–2 words be translated into Chinese and returns a mixed Chinese/English sentence, as in the blueprint. |
| §3.1.6 Change Expression Style | Use slang/dialect while keeping semantics unchanged | `src/jbfoundry/attacks/generated/renellm_gen.py:249–264` | ✅ | `_change_style` asks for slang/dialect rephrasing without semantic change, matching the described strategy. |
| §3.2 Step 2: Scenario Nesting | Select a scenario and embed the rewritten prompt into it | `src/jbfoundry/attacks/generated/renellm_gen.py:334–338` | ✅ | `_nest_scenario` randomly selects one scenario template and replaces `<>` with the rewritten prompt. |
| §3.2 Code Completion Scenario | Python code-completion style template wrapping the prompt as a function description | `src/jbfoundry/attacks/generated/renellm_gen.py:86–98` | ✅ | First entry in `SCENARIOS` matches the paper’s code-completion template semantics. |
| §3.2 Table Filling Scenario | LaTeX table template with prompt as table heading | `src/jbfoundry/attacks/generated/renellm_gen.py:100–117` | ✅ | Second entry in `SCENARIOS` matches the LaTeX table-filling scenario in the blueprint. |
| §3.2 Text Continuation Scenario | Story-style text continuation with prompt as course title and steps | `src/jbfoundry/attacks/generated/renellm_gen.py:119–135` | ✅ | Third entry in `SCENARIOS` reproduces the story-based continuation scenario from the paper. |
| Algorithm 1 (Loop Termination & Fallback) | While loop up to \(T\) iterations; on failure return current (possibly unnested) prompt | `src/jbfoundry/attacks/generated/renellm_gen.py:385–399` | ❌ | Implementation performs extra rewriting attempts beyond `max_iterations` and always returns a nested scenario prompt, diverging from the paper’s specified \(T\)-bounded loop and fallback behavior. |

## Parameter Mapping
| Paper Parameter | Code Parameter / Constant | Type | Default / Value | Match (✅/❌/⚠️) | Notes |
|---|---|---|---|---|---|
| Max iterations \(T\) | `max_iterations` in `PARAMETERS` | int | 20 | ⚠️ | Main loop in `generate_attack` respects `max_iterations`, but the fallback block adds up to 3 extra rewriting attempts beyond \(T\), so the strict \(T\) bound is not preserved. |
| Rewriting strategy set \(S\) (6 strategies) | `REWRITING_STRATEGIES` | List[str] | 6 strategies: paraphrase, misspell_sensitive, alter_structure, insert_characters, partial_translation, change_style | ✅ | Strategy names and intended behaviors match the paper. |
| Scenario set \(C\) (3 scenarios) | `SCENARIOS` | List[str] | 3 templates: code completion, table filling, text continuation | ✅ | Templates mirror the three scenarios described in the blueprint. |
| Number of paraphrase candidates \(K\) | Encoded in `_paraphrase` prompt ("Give 5 rewritten candidates") | int (implicit) | 5 | ✅ | Exactly matches the blueprint; not exposed as a user parameter but fixed in the prompt text. |
| Paraphrase max length (≤6 words) | Encoded in `_paraphrase` prompt ("no more than 6 words") | int (implicit) | 6 | ✅ | Matches the paper; enforced via the prompt rather than hard constraints in code. |
| Rewriting temperature / randomness | `rewrite_temperature` in `PARAMETERS` | float or None | 0.5 (or `random.uniform(0, 1)` if None) | ⚠️ | Paper only specifies randomization; this implementation exposes a temperature parameter with a default that is not specified in the paper but is a reasonable choice. |
| LLMeval (harmfulness judge) model | `judge_model` / `judge_provider` | str | `"gpt-3.5-turbo"` / `"wenwen"` | ⚠️ | Paper names LLMeval abstractly; code maps this to a configurable LLM; exact model choice may differ from experiments but aligns with the described role. |
| Rewrite LLM model | `rewrite_model` / `rewrite_provider` | str | `"gpt-3.5-turbo"` / `"wenwen"` | ⚠️ | Paper uses a rewriting LLM; here it is configurable with a default; exact model details are not fully specified in the blueprint. |

## Misalignments / Missing Items

1. **Loop termination and strict \(T\) bound**
   - **Paper citation**: Algorithm 1 (as summarized in the blueprint around `run_jailbreak_attack`), which iterates while `iteration < T` and then returns `current_prompt` after exhausting \(T\) attempts.
   - **Expected behavior**: The algorithm should perform at most \(T\) iterations of the rewrite–nest–evaluate loop. After \(T\) unsuccessful iterations, it should terminate and return the (last) current prompt without further search, enforcing \(T\) as a hard cap on attack search.
   - **Observed behavior**: In `generate_attack`, after completing the `for iteration in range(max_iterations)` loop, the implementation logs the max-iteration warning and then performs **up to three additional** calls to `_rewrite_prompt` before falling back:
     - It tries `_rewrite_prompt(original_prompt)` up to 3 extra times (`for _ in range(3)`), beyond the configured `max_iterations`.
     - Only after these extra attempts does it fall back to using `original_prompt` if no rewritten prompt passes the harmfulness classifier.
   - **Code location**: `src/jbfoundry/attacks/generated/renellm_gen.py:385–399`.
   - **Impact**: This changes the effective search budget beyond the paper’s \(T\) limit and introduces a hidden, non-configurable search control parameter (the hard-coded 3 extra attempts). According to the audit guidelines, search-control parameters like iteration caps must not be effectively hard-coded or extended beyond the exposed controls, so this is a fidelity issue.

2. **Fallback output when no harmful rewrite is found**
   - **Paper citation**: Algorithm 1 (blueprint `run_jailbreak_attack`), where after the loop the function returns `current_prompt` (which, according to the pseudocode, remains the base prompt when no successful jailbreak is found).
   - **Expected behavior**: If no rewritten-and-nested prompt both (a) is labeled harmful by LLMeval and (b) successfully jailbreaks the target model within \(T\) iterations, the algorithm returns the current (unnested) prompt, effectively failing to find a jailbreak rather than synthesizing an arbitrary nested prompt.
   - **Observed behavior**: In the implementation, after the `max_iterations` loop and the additional 3 rewrite attempts:
     - If `rewritten_prompt` is still `None`, it is set to `original_prompt`.
     - The code **always** applies `_nest_scenario` to `rewritten_prompt` and returns a **nested scenario prompt**, even when **no** rewritten prompt ever passed `_harmful_classification`.
   - **Code location**: `src/jbfoundry/attacks/generated/renellm_gen.py:388–399`.
   - **Impact**: This guarantees that the attack always outputs a scenario-nested prompt, whereas Algorithm 1 may output the base prompt when it fails to find a successful jailbreak. This can produce nested prompts with unknown harmfulness characteristics in cases where LLMeval consistently deems all rewrites non-harmful, altering the algorithm’s failure-mode semantics.

## Extra Behaviors Not in Paper

- **Additional post-cap search attempts**: The fallback block performs up to 3 additional rewriting attempts after the `max_iterations` loop, effectively adding an extra search stage that is not described in the paper or blueprint (`src/jbfoundry/attacks/generated/renellm_gen.py:388–393`).
- **Number-prefix stripping in paraphrase outputs**: `_remove_number_prefix` strips leading numeric indices like `"1. "` or `"1)"` from paraphrase candidates before use (`src/jbfoundry/attacks/generated/renellm_gen.py:157–162`). This is an implementation convenience not explicitly mentioned in the paper, but it does not materially affect the attack’s semantics.
- **Configurable model/provider parameters and temperature**: The implementation exposes `rewrite_model`, `rewrite_provider`, `judge_model`, `judge_provider`, and `rewrite_temperature` as configurable, whereas the paper describes these more abstractly. This is an extension for flexibility and does not by itself conflict with the method, though the specific defaults might differ from those in the original experiments.
- **Extensive logging**: The attack includes detailed logging of iterations, strategies, and rewritten/nested prompts (`src/jbfoundry/attacks/generated/renellm_gen.py:313–321`, `360–377`). The paper does not discuss logging; these additions are benign from a fidelity standpoint.

## Required Changes to Reach 100%

1. **Enforce strict \(T =\) `max_iterations` bound without extra hidden retries**
   - **File / location**: `src/jbfoundry/attacks/generated/renellm_gen.py:385–393`.
   - **Change**: Remove or parameterize the hard-coded loop `for _ in range(3)` that performs extra rewriting attempts after the main `max_iterations` loop. If additional retries beyond \(T\) are desired, expose them as an explicit AttackParameter (e.g., `extra_rewrites`) and document the deviation, or preferably eliminate them to match Algorithm 1’s hard cap.
   - **Paper reference**: Algorithm 1 in the ReNeLLM paper, which uses a while-loop up to \(T\) iterations without extra post-loop attempts.

2. **Align fallback behavior with Algorithm 1’s return value**
   - **File / location**: `src/jbfoundry/attacks/generated/renellm_gen.py:388–399`.
   - **Change**: When all rewriting attempts (including any within the `max_iterations` loop) fail to yield a prompt that passes `_harmful_classification`, return `original_prompt` (or, if preferred, the last attempted rewritten prompt) **without** nesting it in a scenario. That is, avoid unconditional scenario nesting in the failure path so that the algorithm’s failure mode matches the paper’s behavior.
   - **Paper reference**: Algorithm 1 (`run_jailbreak_attack`), which returns `current_prompt` directly after exhausting \(T\) iterations, rather than always constructing a nested prompt in the failure case.

If these adjustments are implemented, the search control and fallback semantics would align with Algorithm 1, and the implementation would be fully faithful to the ReNeLLM method as described in the paper and the provided blueprint.

## Final Verdict
Given the discrepancies in loop termination and fallback behavior (extra unparameterized retries and always returning a nested prompt even when no harmful rewrite is found), the implementation is **Not 100% Fidelity** to the paper, despite accurately implementing the core rewriting strategies, harmfulness judging, and scenario nesting components.


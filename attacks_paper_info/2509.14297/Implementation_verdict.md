## Audit Iteration 5 - 2025-12-29

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Retry loop lacks try/except for LLM errors | ❌ | ❌ Still Broken | LLM call still unwrapped; exceptions bypass retries/fallback (`src/jbfoundry/attacks/generated/hill_gen.py:137-158`) |
| Fallback not applied when LLM errors occur | ❌ | ❌ Still Broken | Fallback only for empty responses; exceptions skip fallback (`src/jbfoundry/attacks/generated/hill_gen.py:156-158`) |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Few-shot examples inclusion | ✅ | ✅ | `FEW_SHOT_EXAMPLES` unchanged (`src/jbfoundry/attacks/generated/hill_gen.py:45-59`) |
| Reframing instructions (4 steps) | ✅ | ✅ | Prompt text intact (`src/jbfoundry/attacks/generated/hill_gen.py:91-99`) |
| Response cleaning (`HILL:` prefix removal) | ✅ | ✅ | Cleaning logic unchanged (`src/jbfoundry/attacks/generated/hill_gen.py:144-149`) |

**NEW Issues Found This Iteration:**
- None.

**Summary:**
- Fixed: 0 issues
- Partially Fixed: 0 issues
- Still Broken: 2 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2509.14297
- Attack: hill_gen
- Verdict: Not 100% Fidelity
- Coverage: 9/12 components (75.0%)
- Iteration: 5

## Executive Summary
Core prompt construction, examples, and response cleaning remain faithful to the plan. However, the implementation still omits the plan-mandated try/except within the retry loop and does not apply the fallback when LLM errors occur. Consequently, robustness to failed generations remains unimplemented.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Table 5/Fig.2 examples | Include all five Goal→HILL examples | src/jbfoundry/attacks/generated/hill_gen.py:45-59 | ✅ | Matches plan examples |
| Prompt instructions | 4-step reframing guidance | src/jbfoundry/attacks/generated/hill_gen.py:91-99 | ✅ | Steps listed verbatim |
| Intent preservation instruction | Conditional intent-preservation in prompt | src/jbfoundry/attacks/generated/hill_gen.py:87-90 | ✅ | Included when `intention_check` True |
| Prompt assembly | Combine instructions, examples, Goal/HILL stub | src/jbfoundry/attacks/generated/hill_gen.py:91-106 | ✅ | Structure matches plan |
| Model setup | Initialize attacker LLM with configurable model | src/jbfoundry/attacks/generated/hill_gen.py:61-74 | ✅ | Uses `attacker_model` |
| LLM query | Call attacker model to generate HILL prompt | src/jbfoundry/attacks/generated/hill_gen.py:141-142 | ✅ | Single query per attempt |
| Response cleaning | Strip whitespace and remove optional “HILL:” prefix | src/jbfoundry/attacks/generated/hill_gen.py:144-149 | ✅ | Cleaning present |
| Retry loop | Retry up to `max_attempts` with try/except | src/jbfoundry/attacks/generated/hill_gen.py:135-155 | ❌ | No try/except; retries only apply if no exception is raised |
| Failure fallback | On repeated failure, return original goal | src/jbfoundry/attacks/generated/hill_gen.py:156-158 | ❌ | Fallback only after empty responses; exceptions bypass fallback |
| Parameter: attacker_model | Default gpt-4o | src/jbfoundry/attacks/generated/hill_gen.py:21-28 | ✅ | Defined with CLI arg |
| Parameter: max_attempts | Default 3 and used for retries | src/jbfoundry/attacks/generated/hill_gen.py:29-35,135-155 | ❌ | Controls empty-response retries only; not applied to LLM errors as plan requires |
| Parameter: intention_check | Default True toggling intent instruction | src/jbfoundry/attacks/generated/hill_gen.py:36-42,87-90 | ✅ | Implemented and used |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Attacker Model | attacker_model | str | gpt-4o | ✅ | Configurable via PARAMETERS |
| Max Attempts | max_attempts | int | 3 | ❌ | Missing try/except; not applied to LLM errors/fallback as specified |
| Intention Check | intention_check | bool | True | ✅ | Controls inclusion of intent instruction |

## Misalignments / Missing Items
- **Retry loop lacks error handling** (Plan §5): Plan requires wrapping LLM calls in try/except within the `max_attempts` loop; implementation calls the LLM without exception handling, so failures terminate the loop and skip retries (`src/jbfoundry/attacks/generated/hill_gen.py:135-155`).
- **Fallback not applied to LLM errors** (Plan §5): After exhausting attempts (including failed calls), the attack should return `goal`; current fallback triggers only after empty responses, so exceptions bypass fallback (`src/jbfoundry/attacks/generated/hill_gen.py:156-158`).

## Extra Behaviors Not in Paper
- None noted that affect attack semantics.

## Required Changes to Reach 100%
- Wrap the attacker LLM call in try/except inside the `for attempt in range(self.max_attempts)` loop; on exception, continue to the next attempt (`src/jbfoundry/attacks/generated/hill_gen.py:135-155`).
- After exhausting attempts (whether due to exceptions or empty responses), return the original `goal` to provide the planned fallback (`src/jbfoundry/attacks/generated/hill_gen.py:156-158`).

## Final Verdict
Not 100% Fidelity

## Audit Iteration 4 - 2025-12-29

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Retry loop lacks try/except for LLM errors | ⚠️ | ❌ Still Broken | LLM call not wrapped; exceptions still propagate, so attempts/fallback never run on errors |
| Fallback not applied when LLM errors occur | ⚠️ | ❌ Still Broken | Fallback only after empty responses; errors bypass loop and fallback |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Few-shot examples inclusion | ✅ | ✅ | Examples unchanged in `FEW_SHOT_EXAMPLES` |
| Reframing instructions (4 steps) | ✅ | ✅ | Prompt text intact in `_construct_reframing_prompt` |
| Response cleaning (`HILL:` prefix removal) | ✅ | ✅ | Cleaning logic unchanged in `generate_attack` |

**NEW Issues Found This Iteration:**
- None.

**Summary:**
- Fixed: 0 issues
- Partially Fixed: 0 issues
- Still Broken: 2 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2509.14297
- Attack: hill_gen
- Verdict: Not 100% Fidelity
- Coverage: 9/12 components (75.0%)
- Iteration: 4

## Executive Summary
Core prompt construction, few-shot examples, and cleaning remain faithful to the plan. However, the required retry loop with try/except around the attacker LLM call is still absent, and the fallback to the original goal still does not execute when LLM errors occur. As a result, planned robustness to failed generations is not achieved.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Table 5/Fig.2 examples | Include all five Goal→HILL examples | src/jbfoundry/attacks/generated/hill_gen.py:45-59 | ✅ | Matches plan examples |
| Prompt instructions | 4-step reframing guidance | src/jbfoundry/attacks/generated/hill_gen.py:91-99 | ✅ | Steps listed verbatim |
| Intent preservation instruction | Conditional intent-preservation in prompt | src/jbfoundry/attacks/generated/hill_gen.py:87-90 | ✅ | Included when `intention_check` True |
| Prompt assembly | Combine instructions, examples, Goal/HILL stub | src/jbfoundry/attacks/generated/hill_gen.py:91-106 | ✅ | Structure matches plan |
| Model setup | Initialize attacker LLM with configurable model | src/jbfoundry/attacks/generated/hill_gen.py:61-74 | ✅ | Uses `attacker_model` |
| LLM query | Call attacker model to generate HILL prompt | src/jbfoundry/attacks/generated/hill_gen.py:141-143 | ✅ | Single query per attempt |
| Response cleaning | Strip whitespace and remove optional “HILL:” prefix | src/jbfoundry/attacks/generated/hill_gen.py:144-150 | ✅ | Cleaning present |
| Retry loop | Retry up to `max_attempts` with try/except | src/jbfoundry/attacks/generated/hill_gen.py:135-155 | ❌ | No try/except; retries only apply if no exception |
| Failure fallback | On repeated failure, return original goal | src/jbfoundry/attacks/generated/hill_gen.py:156-158 | ❌ | Fallback only after empty responses; exceptions skip it |
| Parameter: attacker_model | Default gpt-4o | src/jbfoundry/attacks/generated/hill_gen.py:21-28 | ✅ | Defined with CLI arg |
| Parameter: max_attempts | Default 3 and used for retries | src/jbfoundry/attacks/generated/hill_gen.py:29-35,135-155 | ⚠️ | Controls empty-response retries only; not applied to LLM errors |
| Parameter: intention_check | Default True toggling intent instruction | src/jbfoundry/attacks/generated/hill_gen.py:36-42,87-90 | ✅ | Implemented and used |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Attacker Model | attacker_model | str | gpt-4o | ✅ | Configurable via PARAMETERS |
| Max Attempts | max_attempts | int | 3 | ❌ | Not applied to LLM exceptions as required by plan |
| Intention Check | intention_check | bool | True | ✅ | Controls inclusion of intent instruction |

## Misalignments / Missing Items
- **Retry loop lacks error handling** (Plan §5): Plan requires wrapping LLM calls in try/except within the `max_attempts` loop; implementation performs direct calls without exception handling, so failures terminate the loop prematurely (`src/jbfoundry/attacks/generated/hill_gen.py:135-155`).
- **Fallback not applied to LLM errors** (Plan §5): After exhausting attempts (including failed calls), the attack should return `goal`; current fallback runs only for empty responses, so exceptions bypass fallback (`src/jbfoundry/attacks/generated/hill_gen.py:156-158`).

## Extra Behaviors Not in Paper
- None noted that affect attack semantics.

## Required Changes to Reach 100%
- Wrap the attacker LLM call in try/except inside the `for attempt in range(self.max_attempts)` loop; on exception, continue to the next attempt (`src/jbfoundry/attacks/generated/hill_gen.py:135-155`).
- After exhausting attempts (whether due to exceptions or empty responses), return the original `goal` to provide the planned fallback (`src/jbfoundry/attacks/generated/hill_gen.py:156-158`).

## Final Verdict
Not 100% Fidelity

# Audit Iteration 3 - 2025-12-29

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Missing retry loop and `max_attempts` usage | ❌ | ⚠️ Partially Fixed | Loop now uses `max_attempts` for empty responses only; no try/except for LLM errors |
| Missing fallback to original goal on repeated failure | ❌ | ⚠️ Partially Fixed | Falls back to `goal` only after empty responses; exceptions still propagate so no fallback on errors |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Few-shot examples inclusion | ✅ | ✅ | Examples unchanged |
| Reframing instructions (4 steps) | ✅ | ✅ | Prompt text intact |
| Response cleaning (`HILL:` prefix removal) | ✅ | ✅ | Cleaning logic unchanged |

**NEW Issues Found This Iteration:**
- None beyond the partially fixed retry/fallback behavior.

**Summary:**
- Fixed: 0 issues
- Partially Fixed: 2 issues
- Still Broken: 0 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2509.14297
- Attack: hill_gen
- Verdict: Not 100% Fidelity
- Coverage: 9/12 components (75.0%)
- Iteration: 3

## Executive Summary
Retry logic was added using `max_attempts`, and a fallback to the original goal now exists, but both only address empty responses. The plan requires retrying failed LLM calls (with try/except) and falling back after repeated failures; current code lets exceptions propagate and never reaches the fallback in that case. Core prompt construction, examples, and cleaning remain correct.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Table 5/Fig.2 examples | Include all five Goal→HILL examples | src/jbfoundry/attacks/generated/hill_gen.py:45-59 | ✅ | Matches plan examples |
| Prompt instructions | 4-step reframing guidance | src/jbfoundry/attacks/generated/hill_gen.py:91-99 | ✅ | Steps listed verbatim |
| Intent preservation instruction | Conditional intent-preservation in prompt | src/jbfoundry/attacks/generated/hill_gen.py:87-90 | ✅ | Included when `intention_check` True |
| Prompt assembly | Combine instructions, examples, Goal/HILL stub | src/jbfoundry/attacks/generated/hill_gen.py:91-106 | ✅ | Structure matches plan |
| Model setup | Initialize attacker LLM with configurable model | src/jbfoundry/attacks/generated/hill_gen.py:61-74 | ✅ | Uses `attacker_model` |
| LLM query | Call attacker model to generate HILL prompt | src/jbfoundry/attacks/generated/hill_gen.py:129-132 | ✅ | Single query per attempt |
| Response cleaning | Strip whitespace and remove optional “HILL:” prefix | src/jbfoundry/attacks/generated/hill_gen.py:133-140 | ✅ | Cleaning present |
| Retry loop | Retry up to `max_attempts` with try/except | src/jbfoundry/attacks/generated/hill_gen.py:126-143 | ⚠️ | Retries only on empty responses; no try/except for LLM errors |
| Failure fallback | On repeated failure, return original goal | src/jbfoundry/attacks/generated/hill_gen.py:145-149 | ⚠️ | Fallback only after empty responses; exceptions bypass fallback |
| Parameter: attacker_model | Default gpt-4o | src/jbfoundry/attacks/generated/hill_gen.py:21-28 | ✅ | Defined with CLI arg |
| Parameter: max_attempts | Default 3 and used for retries | src/jbfoundry/attacks/generated/hill_gen.py:29-35,126-143 | ⚠️ | Controls loop for empty responses only, not LLM errors |
| Parameter: intention_check | Default True toggling intent instruction | src/jbfoundry/attacks/generated/hill_gen.py:36-42,87-90 | ✅ | Implemented and used |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Attacker Model | attacker_model | str | gpt-4o | ✅ | Configurable via PARAMETERS |
| Max Attempts | max_attempts | int | 3 | ⚠️ | Used only for empty-response retries; plan calls for try/except on LLM failures |
| Intention Check | intention_check | bool | True | ✅ | Controls inclusion of intent instruction |

## Misalignments / Missing Items
- **Retry loop lacks error handling** (Plan §5): Plan requires try/except around LLM calls with retries up to `max_attempts`; implementation retries only on empty responses and lets exceptions propagate, so failures never reach the loop or fallback (`src/jbfoundry/attacks/generated/hill_gen.py:126-143`).
- **Fallback not applied to LLM errors** (Plan §5): Plan specifies returning the original `goal` after repeated failures; current fallback triggers only after empty responses, not after exceptions, so planned robustness to failed generations is missing (`src/jbfoundry/attacks/generated/hill_gen.py:145-149`).

## Extra Behaviors Not in Paper
- None noted that affect attack semantics.

## Required Changes to Reach 100%
- Wrap the attacker LLM call in a try/except within the `for attempt in range(self.max_attempts)` loop; on exception, continue to the next attempt, and after exhausting attempts, fall back to returning `goal` (`src/jbfoundry/attacks/generated/hill_gen.py:126-149`).
- Apply the fallback when all attempts fail due to exceptions as well as empty responses, so `max_attempts` governs overall failure handling per plan (`src/jbfoundry/attacks/generated/hill_gen.py:126-149`).

## Final Verdict
Not 100% Fidelity

# Audit Iteration 2 - 2025-12-29

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Missing retry loop and `max_attempts` usage | ❌ | ❌ Still Broken | Single LLM call; `max_attempts` unused |
| Missing fallback to original goal on repeated failure | ❌ | ❌ Still Broken | No fallback path implemented |
| `max_attempts` parameter absent | ❌ | ✅ Fixed | Parameter added with default 3 |
| `intention_check` parameter absent | ❌ | ✅ Fixed | Parameter added; toggles intent instruction |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Few-shot examples inclusion | ✅ | ✅ | Examples unchanged and intact |
| Reframing instructions (4 steps) | ✅ | ✅ | Prompt text preserved |
| Response cleaning (`HILL:` prefix removal) | ✅ | ✅ | Cleaning logic unchanged |

**NEW Issues Found This Iteration:**
- None beyond unresolved retry/fallback gaps.

**Summary:**
- Fixed: 2 issues
- Partially Fixed: 0 issues
- Still Broken: 2 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2509.14297
- Attack: hill_gen
- Verdict: Not 100% Fidelity
- Coverage: 9/12 components (75.0%)
- Iteration: 2

## Executive Summary
Parameters `max_attempts` and `intention_check` are now exposed, and intent instructions are toggleable, but the control logic mandated by the plan remains missing: there is no retry loop governed by `max_attempts` and no fallback to return the original goal after repeated failures. These omissions leave the implementation short of the planned robustness.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Table 5/Fig.2 examples | Include all five Goal→HILL examples | src/jbfoundry/attacks/generated/hill_gen.py:45-59 | ✅ | Examples match plan |
| Prompt instructions | 4-step reframing guidance | src/jbfoundry/attacks/generated/hill_gen.py:91-99 | ✅ | Steps listed verbatim |
| Intent preservation instruction | Explicit intent-preservation in prompt | src/jbfoundry/attacks/generated/hill_gen.py:87-91 | ✅ | Included when `intention_check` is True |
| Prompt assembly | Combine instructions, examples, Goal/HILL stub | src/jbfoundry/attacks/generated/hill_gen.py:91-106 | ✅ | Structure matches plan |
| Model setup | Initialize attacker LLM with configurable model | src/jbfoundry/attacks/generated/hill_gen.py:61-74 | ✅ | Uses `attacker_model` |
| LLM query | Call attacker model to generate HILL prompt | src/jbfoundry/attacks/generated/hill_gen.py:126-127 | ✅ | Single query |
| Response cleaning | Strip whitespace and remove optional “HILL:” prefix | src/jbfoundry/attacks/generated/hill_gen.py:129-134 | ✅ | Cleaning present |
| Retry loop | Retry up to `max_attempts` with try/except | src/jbfoundry/attacks/generated/hill_gen.py | ❌ | No loop; `max_attempts` unused |
| Failure fallback | On repeated failure, return original goal | src/jbfoundry/attacks/generated/hill_gen.py | ❌ | No fallback path |
| Parameter: attacker_model | Default gpt-4o | src/jbfoundry/attacks/generated/hill_gen.py:21-28 | ✅ | Defined with CLI arg |
| Parameter: max_attempts | Default 3 and used for retries | src/jbfoundry/attacks/generated/hill_gen.py:29-35 | ⚠️ | Defined but not used in logic |
| Parameter: intention_check | Default True toggling intent instruction | src/jbfoundry/attacks/generated/hill_gen.py:36-42 | ✅ | Implemented and used |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Attacker Model | attacker_model | str | gpt-4o | ✅ | Configurable via PARAMETERS |
| Max Attempts | max_attempts | int | 3 | ❌ | Exists but never used for retries |
| Intention Check | intention_check | bool | True | ✅ | Controls inclusion of intent instruction |

## Misalignments / Missing Items
- **Missing retry loop using `max_attempts`** (Plan §5): Expected loop with try/except up to `max_attempts`; code performs a single call without retries (`src/jbfoundry/attacks/generated/hill_gen.py:123-136`).
- **Missing fallback to original goal** (Plan §5): After exhausting attempts, should return original `goal`; current implementation raises on error and never falls back (`src/jbfoundry/attacks/generated/hill_gen.py:123-136`).
- **`max_attempts` parameter unused** (Plan §3, §5): Parameter is defined but not consumed in control flow, so user-configured attempts have no effect (`src/jbfoundry/attacks/generated/hill_gen.py:29-35`, `123-136`).

## Extra Behaviors Not in Paper
- None identified that affect attack semantics.

## Required Changes to Reach 100%
- Implement retry loop controlled by `max_attempts` around the LLM query, catching exceptions and empty responses as needed; on exhaustion, return the original `goal` per plan (src/jbfoundry/attacks/generated/hill_gen.py).
- Use the `max_attempts` parameter in the above loop so user configuration affects behavior (src/jbfoundry/attacks/generated/hill_gen.py).

## Final Verdict
Not 100% Fidelity

# Implementation Fidelity Verdict
- Paper ID: 2509.14297
- Attack: hill_gen
- Verdict: Not 100% Fidelity
- Coverage: 8/12 components (66.7%)
- Iteration: 1

## Executive Summary
The current `HillAttack` captures the core reframing prompt, examples, and basic response cleaning, but omits key control logic from the implementation plan. The missing `max_attempts` parameter, absence of the required retry loop with fallback to the original goal, and omission of the `intention_check` parameter mean the implementation does not satisfy the planned behavior. These gaps leave failures unhandled and remove the configurability outlined in the plan.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §4 (Few-shot examples) | Include all five Goal→HILL examples | src/jbfoundry/attacks/generated/hill_gen.py:31-45 | ✅ | All specified examples present |
| §5 (Prompt instructions) | 4-step reframing guidance (concepts, questions, detail, hypotheticality) | src/jbfoundry/attacks/generated/hill_gen.py:70-77 | ✅ | Steps encoded verbatim in prompt |
| §5 (Intent preservation) | Explicitly instruct to preserve original intent | src/jbfoundry/attacks/generated/hill_gen.py:70-72 | ✅ | Intent preservation stated |
| §5 (Prompt assembly) | Combine instructions, examples, and Goal/HILL stub | src/jbfoundry/attacks/generated/hill_gen.py:70-85 | ✅ | Template matches plan structure |
| §5 (Model setup) | Initialize attacker LLM with configurable model | src/jbfoundry/attacks/generated/hill_gen.py:47-58 | ✅ | Uses LLMLiteLLM with `attacker_model` |
| §5 (LLM query) | Call attacker model to generate HILL prompt | src/jbfoundry/attacks/generated/hill_gen.py:103-107 | ✅ | Single query issued |
| §5 (Response cleaning) | Strip whitespace and remove optional “HILL:” prefix | src/jbfoundry/attacks/generated/hill_gen.py:108-113 | ✅ | Cleaning implemented |
| §5 (Retry loop) | Retry up to `max_attempts` with try/except | src/jbfoundry/attacks/generated/hill_gen.py | ❌ | No loop or exception handling |
| §5 (Failure fallback) | On repeated failure, return original goal | src/jbfoundry/attacks/generated/hill_gen.py | ❌ | No fallback behavior |
| §3 (Parameter) | `attacker_model` with default `gpt-4o` | src/jbfoundry/attacks/generated/hill_gen.py:21-28 | ✅ | Parameter defined with CLI arg |
| §3 (Parameter) | `max_attempts` int default 3 | src/jbfoundry/attacks/generated/hill_gen.py | ❌ | Parameter absent and unused |
| §3 (Parameter) | `intention_check` bool default True | src/jbfoundry/attacks/generated/hill_gen.py | ❌ | Parameter not defined |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Attacker Model | attacker_model | str | gpt-4o | ✅ | Configurable via `PARAMETERS` |
| Max Attempts | — | int | 3 | ❌ | Missing parameter and loop |
| Intention Check | — | bool | True | ❌ | Not exposed; no toggle |

## Misalignments / Missing Items
- **Missing retry loop and `max_attempts` usage** (Plan §5): Plan requires looping up to `max_attempts` with try/except around the LLM call; current `generate_attack` performs a single call with no retries (`src/jbfoundry/attacks/generated/hill_gen.py:103-107`). This removes planned robustness and ignores the `max_attempts` control.
- **Missing fallback to original goal** (Plan §5): Plan specifies returning the original `goal` when retries exhaust; implementation has no fallback path (`src/jbfoundry/attacks/generated/hill_gen.py`).
- **`max_attempts` parameter absent** (Plan §3): Parameter not defined in `PARAMETERS`, so cannot be configured or used (`src/jbfoundry/attacks/generated/hill_gen.py`).
- **`intention_check` parameter absent** (Plan §3): Planned boolean toggle is not exposed or consumed (`src/jbfoundry/attacks/generated/hill_gen.py`).

## Extra Behaviors Not in Paper
- None identified that alter attack semantics.

## Required Changes to Reach 100%
- Add `max_attempts` `AttackParameter` (default 3) and implement a retry loop in `generate_attack` that catches LLM errors up to `max_attempts`; after exhausting attempts, return the original `goal` (`src/jbfoundry/attacks/generated/hill_gen.py`).
- Add `intention_check` boolean `AttackParameter` (default True) and pass its value into prompt construction (e.g., include the intent-preservation instruction when enabled) to honor the planned configurability (`src/jbfoundry/attacks/generated/hill_gen.py`).

## Final Verdict
Not 100% Fidelity

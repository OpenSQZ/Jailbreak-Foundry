## Audit Iteration 3 - 2026-01-08

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| NAME constant mismatch | ❌ | ✅ Fixed | NAME now set to "FlipAttack_gen" (`src/jbfoundry/attacks/generated/flip_attack_gen.py:19`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Parameter defaults (flip_mode/cot/lang_gpt/few_shot) | ✅ | ✅ | Defaults and choices unchanged and aligned with plan (`src/jbfoundry/attacks/generated/flip_attack_gen.py:22-52`). |
| FMM demo mapping and flipping logic | ✅ | ✅ | FMM demo uses word-order flip; disguise uses sentence flip (`src/jbfoundry/attacks/generated/flip_attack_gen.py:69-77`, `157-163`). |
| Sentence splitting helper | ✅ | ✅ | `TextWrapper` width `len//2`, joins extras (`src/jbfoundry/attacks/generated/flip_attack_gen.py:80-101`). |
| Llama sanitization | ✅ | ✅ | Still strips safety clauses for Llama models (`src/jbfoundry/attacks/generated/flip_attack_gen.py:223-226`). |

**NEW Issues Found This Iteration:**
- None.

**Summary:**
- Fixed: 1 issues
- Partially Fixed: 0 issues
- Still Broken: 0 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2410.02832
- Attack: FlipAttack_gen
- Verdict: 100% Fidelity
- Coverage: 20/20 components (100%)
- Iteration: 3

## Executive Summary
All previously identified fidelity gap (NAME constant) is resolved. The implementation now matches the implementation plan across metadata, parameter defaults, flipping helpers, prompt construction (including LangGPT + few-shot insertion), safety sanitization, and message output. Spot checks show no regressions, and no new issues were discovered.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Metadata | NAME constant = "FlipAttack_gen" | src/jbfoundry/attacks/generated/flip_attack_gen.py:19 | ✅ | Matches plan. |
| Metadata | PAPER constant = "2410.02832" | src/jbfoundry/attacks/generated/flip_attack_gen.py:20 | ✅ | Matches plan. |
| Parameters | flip_mode/cot/lang_gpt/few_shot definitions | src/jbfoundry/attacks/generated/flip_attack_gen.py:22-52 | ✅ | Defaults and choices per plan. |
| Helper | Flip word order (FWO) | src/jbfoundry/attacks/generated/flip_attack_gen.py:57-59 | ✅ | Reverses word order. |
| Helper | Flip chars in word (FCW) | src/jbfoundry/attacks/generated/flip_attack_gen.py:61-63 | ✅ | Reverses each word’s characters. |
| Helper | Flip chars in sentence (FCS) | src/jbfoundry/attacks/generated/flip_attack_gen.py:65-67 | ✅ | Reverses entire string. |
| Helper | Demo dispatcher (incl. FMM→FWO) | src/jbfoundry/attacks/generated/flip_attack_gen.py:69-77 | ✅ | FMM demos use word-order flip. |
| Helper | Split sentence in half | src/jbfoundry/attacks/generated/flip_attack_gen.py:80-101 | ✅ | `TextWrapper` width `len//2`, joins extras. |
| Prompt scaffolding | Mode prompt selection | src/jbfoundry/attacks/generated/flip_attack_gen.py:123-129 | ✅ | Handles all four modes. |
| Prompt scaffolding | CoT prompt toggle | src/jbfoundry/attacks/generated/flip_attack_gen.py:132-133 | ✅ | Adds step-by-step phrase when enabled. |
| System prompt | Standard template formatting | src/jbfoundry/attacks/generated/flip_attack_gen.py:136-139 | ✅ | Multi-line template per plan. |
| System prompt | LangGPT template | src/jbfoundry/attacks/generated/flip_attack_gen.py:140-154 | ✅ | Role/profile/rules structure matches plan. |
| Flipping | Disguised prompt generation (FWO/FCW/FCS/FMM) | src/jbfoundry/attacks/generated/flip_attack_gen.py:157-163 | ✅ | Dispatches to correct flip; FMM uses FCS flip. |
| User prompt | Initialization `TASK is '{disguised_prompt}'` | src/jbfoundry/attacks/generated/flip_attack_gen.py:166-167 | ✅ | Exact format. |
| Few-shot | Example construction (3 demos) | src/jbfoundry/attacks/generated/flip_attack_gen.py:170-191 | ✅ | Left/right/instruction demos per plan. |
| LangGPT workflow | Workflow steps string | src/jbfoundry/attacks/generated/flip_attack_gen.py:193-200 | ✅ | Defines Step 1/Step 2 workflow. |
| LangGPT + few-shot | Insert examples into workflow prompt | src/jbfoundry/attacks/generated/flip_attack_gen.py:201-214 | ✅ | Few-shot injected before workflow section. |
| Standard few-shot | Append few-shot to system prompt | src/jbfoundry/attacks/generated/flip_attack_gen.py:217-221 | ✅ | Non-LangGPT path appends to system prompt. |
| Safety adaptation | Llama sanitization | src/jbfoundry/attacks/generated/flip_attack_gen.py:223-226 | ✅ | Removes two safety clauses for Llama models. |
| Output | Return message list | src/jbfoundry/attacks/generated/flip_attack_gen.py:229-232 | ✅ | Returns `[system, user]` messages. |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Flipping Mode | flip_mode | str | FCS | ✅ | Choices FWO/FCW/FCS/FMM. |
| Chain of Thought | cot | bool | False | ✅ | Adds step-by-step phrase. |
| LangGPT Prompt | lang_gpt | bool | False | ✅ | Switches to LangGPT system prompt. |
| Few-Shot | few_shot | bool | False | ✅ | Enables few-shot demonstrations. |

## Misalignments / Missing Items
None.

## Extra Behaviors Not in Paper
None.

## Required Changes to Reach 100%
None — implementation matches the plan.

## Final Verdict
100% Fidelity

## Audit Iteration 2 - 2026-01-08

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| NAME constant mismatch | ❌ | ❌ Still Broken | Still uses `"flip_attack_gen"` instead of plan-required `"FlipAttack_gen"` (`src/jbfoundry/attacks/generated/flip_attack_gen.py:19`). |
| PAPER constant mismatch | ❌ | ✅ Fixed | Set to `"2410.02832"` (`src/jbfoundry/attacks/generated/flip_attack_gen.py:20`). |
| LangGPT few-shot insertion wrong | ❌ | ✅ Fixed | Few-shot prompt now spliced into `lang_gpt_prompt` before `## Workflow`, then appended to the user prompt (`src/jbfoundry/attacks/generated/flip_attack_gen.py:194-214`). |
| Standard system prompt formatting drift | ⚠️ | ✅ Fixed | Restored multi-line template matching the reference format (`src/jbfoundry/attacks/generated/flip_attack_gen.py:136-139`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Parameter defaults (flip_mode/cot/lang_gpt/few_shot) | ✅ | ✅ | Defaults and choices unchanged and aligned with plan (`src/jbfoundry/attacks/generated/flip_attack_gen.py:22-51`). |
| FCS flipping logic (incl. FMM mapping) | ✅ | ✅ | FCS and FMM dispatch to `_flip_char_in_sentence`; FMM uses FWO wording only in prompts (`src/jbfoundry/attacks/generated/flip_attack_gen.py:157-163`). |
| Sentence splitting helper | ✅ | ✅ | Uses `TextWrapper` width `len//2`, no-regression edge handling (`src/jbfoundry/attacks/generated/flip_attack_gen.py:80-101`). |
| Llama sanitization | ✅ | ✅ | Still strips the two safety clauses for Llama models (`src/jbfoundry/attacks/generated/flip_attack_gen.py:223-227`). |

**NEW Issues Found This Iteration:**
- None beyond the remaining NAME constant mismatch.

**Summary:**
- Fixed: 3 issues
- Partially Fixed: 0 issues
- Still Broken: 1 issue
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2410.02832
- Attack: flip_attack_gen
- Verdict: Not 100% Fidelity
- Coverage: 19/20 components (95%)
- Iteration: 2

## Executive Summary
Implementation now aligns with the plan for PAPER metadata, LangGPT few-shot insertion, and standard system prompt formatting. The only remaining deviation is the class metadata `NAME`, which still uses `"flip_attack_gen"` instead of the plan-specified `"FlipAttack_gen"`. No regressions detected in previously correct components, and no new issues emerged.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Metadata | NAME constant = "FlipAttack_gen" | src/jbfoundry/attacks/generated/flip_attack_gen.py:19 | ❌ | Uses `"flip_attack_gen"` (lowercase, missing capital A). |
| Metadata | PAPER constant = "2410.02832" | src/jbfoundry/attacks/generated/flip_attack_gen.py:20 | ✅ | Matches plan. |
| Parameters | flip_mode/cot/lang_gpt/few_shot definitions | src/jbfoundry/attacks/generated/flip_attack_gen.py:22-51 | ✅ | Defaults/choices per plan. |
| Helper | Flip word order (FWO) | src/jbfoundry/attacks/generated/flip_attack_gen.py:57-59 | ✅ | Reverses word order. |
| Helper | Flip chars in word (FCW) | src/jbfoundry/attacks/generated/flip_attack_gen.py:61-63 | ✅ | Reverses each word’s characters. |
| Helper | Flip chars in sentence (FCS) | src/jbfoundry/attacks/generated/flip_attack_gen.py:65-67 | ✅ | Reverses entire string. |
| Helper | Demo dispatcher (FMM→FWO) | src/jbfoundry/attacks/generated/flip_attack_gen.py:69-78 | ✅ | FMM demo uses word-order flip. |
| Helper | Split sentence in half | src/jbfoundry/attacks/generated/flip_attack_gen.py:80-101 | ✅ | `TextWrapper` width `len//2`, joins extras. |
| Prompt scaffolding | Mode prompt selection | src/jbfoundry/attacks/generated/flip_attack_gen.py:123-129 | ✅ | Handles all four modes. |
| Prompt scaffolding | CoT prompt toggle | src/jbfoundry/attacks/generated/flip_attack_gen.py:132-133 | ✅ | Adds step-by-step phrase when enabled. |
| System prompt | Standard template formatting | src/jbfoundry/attacks/generated/flip_attack_gen.py:136-139 | ✅ | Multi-line template per plan. |
| System prompt | LangGPT template | src/jbfoundry/attacks/generated/flip_attack_gen.py:140-154 | ✅ | Role/profile/rules structure matches plan. |
| Flipping | Disguised prompt generation (FMM=FCS) | src/jbfoundry/attacks/generated/flip_attack_gen.py:157-163 | ✅ | FCS/FMM use sentence-level flip. |
| User prompt | Initialization `TASK is '{disguised_prompt}'` | src/jbfoundry/attacks/generated/flip_attack_gen.py:166-167 | ✅ | Exact format. |
| Few-shot | Example construction (3 demos) | src/jbfoundry/attacks/generated/flip_attack_gen.py:170-191 | ✅ | Left/right/instruction demos per plan. |
| Few-shot + LangGPT | Insert examples into workflow prompt | src/jbfoundry/attacks/generated/flip_attack_gen.py:194-214 | ✅ | Few-shot injected before `## Workflow`. |
| LangGPT workflow | Add Step 1/Step 2 to user prompt | src/jbfoundry/attacks/generated/flip_attack_gen.py:194-216 | ✅ | Workflow steps appended to user prompt. |
| Standard few-shot | Append examples to system prompt | src/jbfoundry/attacks/generated/flip_attack_gen.py:217-221 | ✅ | Non-LangGPT path appends to system prompt. |
| Safety adaptation | Llama sanitization | src/jbfoundry/attacks/generated/flip_attack_gen.py:223-227 | ✅ | Removes two safety clauses for Llama. |
| Output | Return message list | src/jbfoundry/attacks/generated/flip_attack_gen.py:229-232 | ✅ | Returns `[system, user]` messages. |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Flipping Mode | flip_mode | str | FCS | ✅ | Choices FWO/FCW/FCS/FMM. |
| Chain of Thought | cot | bool | False | ✅ | Adds step-by-step phrase. |
| LangGPT Prompt | lang_gpt | bool | False | ✅ | Switches to LangGPT system prompt. |
| Few-Shot | few_shot | bool | False | ✅ | Enables few-shot demonstrations. |

## Misalignments / Missing Items
- **NAME constant mismatch** — Plan requires `NAME = "FlipAttack_gen"`, but code uses `"flip_attack_gen"` (`src/jbfoundry/attacks/generated/flip_attack_gen.py:19`). This deviates from plan-specified metadata.

## Extra Behaviors Not in Paper
None beyond framework integration and Llama sanitization already in plan.

## Required Changes to Reach 100%
- Set `NAME = "FlipAttack_gen"` to match the implementation plan. (`src/jbfoundry/attacks/generated/flip_attack_gen.py:19`)

## Final Verdict
Not 100% Fidelity

# Implementation Fidelity Verdict
- Paper ID: 2410.02832
- Attack: flip_attack_gen
- Verdict: Not 100% Fidelity
- Coverage: 16/20 components (80%)
- Iteration: 1

## Executive Summary
The FlipAttack implementation largely follows the planned flipping modes, prompt construction, and optional guidance modules, but four fidelity gaps block 100% compliance. The class metadata deviates from the plan (`NAME` and `PAPER` constants), the LangGPT+few-shot path does not inject examples into the LangGPT workflow as specified (falling back to appending them to the system prompt), and the standard system prompt formatting diverges from the planned multi-line template. All other flipping logic, parameter plumbing, and guidance options match the implementation plan.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Metadata | NAME constant = "FlipAttack_gen" | src/jbfoundry/attacks/generated/flip_attack_gen.py:19-19 | ❌ | Uses "flip_attack_gen" (lowercase, missing capital A) |
| Metadata | PAPER constant = "2410.02832" | src/jbfoundry/attacks/generated/flip_attack_gen.py:20-20 | ❌ | Uses full title string instead of paper ID |
| Parameters | flip_mode/cot/lang_gpt/few_shot defined with defaults/choices | src/jbfoundry/attacks/generated/flip_attack_gen.py:22-52 | ✅ | Matches defaults and choices in plan |
| Helper | Flip word order (FWO) | src/jbfoundry/attacks/generated/flip_attack_gen.py:57-59 | ✅ | Reverse words via split()[::-1] |
| Helper | Flip chars in word (FCW) | src/jbfoundry/attacks/generated/flip_attack_gen.py:61-63 | ✅ | Reverse each word’s characters |
| Helper | Flip chars in sentence (FCS) | src/jbfoundry/attacks/generated/flip_attack_gen.py:65-67 | ✅ | Reverse entire string |
| Helper | Demo dispatcher (incl. FMM→FWO) | src/jbfoundry/attacks/generated/flip_attack_gen.py:69-77 | ✅ | FMM uses word-order demo per plan |
| Helper | Split sentence in half | src/jbfoundry/attacks/generated/flip_attack_gen.py:80-101 | ✅ | textwrap width=len//2 with edge handling |
| Prompt scaffolding | Mode prompt selection | src/jbfoundry/attacks/generated/flip_attack_gen.py:123-129 | ✅ | Handles all four modes |
| Prompt scaffolding | CoT prompt toggle | src/jbfoundry/attacks/generated/flip_attack_gen.py:132-133 | ✅ | Adds step-by-step phrase when enabled |
| System prompt | Standard template formatting | src/jbfoundry/attacks/generated/flip_attack_gen.py:136-138 | ⚠️ | Content matches, but loses planned multi-line formatting |
| System prompt | LangGPT template | src/jbfoundry/attacks/generated/flip_attack_gen.py:140-153 | ✅ | Mirrors LangGPT role/rules structure |
| Flipping | Disguised prompt generation (incl. FMM=FCS) | src/jbfoundry/attacks/generated/flip_attack_gen.py:155-163 | ✅ | FMM uses FCS flip; others match plan |
| User prompt | Initialization `TASK is '{disguised_prompt}'` | src/jbfoundry/attacks/generated/flip_attack_gen.py:165-165 | ✅ | Exact format |
| Few-shot | Example construction (3 demos) | src/jbfoundry/attacks/generated/flip_attack_gen.py:168-190 | ✅ | Left/right/instruction demos per plan |
| Few-shot + LangGPT | Insert examples into LangGPT workflow | src/jbfoundry/attacks/generated/flip_attack_gen.py:193-215 | ❌ | Few-shot appended to system_prompt; not injected between Rules and Workflow as planned |
| Few-shot (standard) | Append examples to system prompt | src/jbfoundry/attacks/generated/flip_attack_gen.py:217-220 | ✅ | Matches plan for non-LangGPT |
| LangGPT workflow | Add Step 1/Step 2 to user prompt | src/jbfoundry/attacks/generated/flip_attack_gen.py:193-215 | ✅ | Workflow appended to user prompt |
| Safety adaptation | Llama sanitization | src/jbfoundry/attacks/generated/flip_attack_gen.py:223-225 | ✅ | Removes harmful-phrase clauses for Llama models |
| Output | Return message list | src/jbfoundry/attacks/generated/flip_attack_gen.py:227-231 | ✅ | Returns [{role: system}, {role: user}] |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Flipping Mode | flip_mode | str | FCS | ✅ | Choices FWO/FCW/FCS/FMM |
| Chain of Thought | cot | bool | False | ✅ | Adds step-by-step phrase |
| LangGPT Prompt | lang_gpt | bool | False | ✅ | Switches to LangGPT system prompt |
| Few-Shot | few_shot | bool | False | ✅ | Enables few-shot demo insertion |

## Misalignments / Missing Items
- **NAME constant mismatch** — Plan: `NAME = "FlipAttack_gen"`; Code: `"flip_attack_gen"`. Location: `src/jbfoundry/attacks/generated/flip_attack_gen.py:19`. Impacts factory registration fidelity.
- **PAPER constant mismatch** — Plan: `PAPER = "2410.02832"`; Code: `"FlipAttack: Jailbreak LLMs via Flipping (2410.02832)"`. Location: `src/jbfoundry/attacks/generated/flip_attack_gen.py:20`. Diverges from plan metadata.
- **LangGPT few-shot insertion wrong** — Plan: inject few-shot examples between Rules and Workflow inside LangGPT guidance (string slicing in user-side LangGPT prompt). Code: `rules_end = system_prompt.find("## Workflow")` on a system prompt that lacks that marker, so few-shot examples fall back to appending to `system_prompt` and never integrate with the LangGPT workflow shown to the user. Location: `src/jbfoundry/attacks/generated/flip_attack_gen.py:193-215`. This changes the demonstrated decoding behavior for LangGPT+few_shot mode.
- **Standard system prompt formatting drift** — Plan notes preserving multi-line template from reference; code collapses to a single-line paragraph. Location: `src/jbfoundry/attacks/generated/flip_attack_gen.py:136-138`. Minor but deviates from planned prompt layout.

## Extra Behaviors Not in Paper
None observed beyond planned Llama sanitization and base framework integration.

## Required Changes to Reach 100%
- Set `NAME = "FlipAttack_gen"` to match plan. (`src/jbfoundry/attacks/generated/flip_attack_gen.py:19`)
- Set `PAPER = "2410.02832"` per plan metadata. (`src/jbfoundry/attacks/generated/flip_attack_gen.py:20`)
- Reimplement LangGPT+few_shot insertion: modify `lang_gpt_prompt` (user-side workflow string) to splice `few_shot_prompt` between the Rules and Workflow sections as in the reference slicing logic, rather than appending to `system_prompt`. Ensure the insertion point exists and examples appear before the workflow steps. (`src/jbfoundry/attacks/generated/flip_attack_gen.py:193-215`)
- Restore the standard system prompt to the planned multi-line template (matching line breaks/spacing from the reference) for non-LangGPT mode. (`src/jbfoundry/attacks/generated/flip_attack_gen.py:136-138`)

## Final Verdict
Not 100% Fidelity

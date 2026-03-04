## Audit Iteration 2 - 2026-01-05

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| NAME metadata casing (expected `FlipAttack_gen`) | ❌ | ❌ Still Broken | Still `NAME = "flip_attack_gen"` in `src/jbfoundry/attacks/generated/flip_attack_gen.py:18`; plan requires `FlipAttack_gen`. |
| PAPER metadata value | ❌ | ✅ Fixed | `PAPER` now set to `"2410.02832"` (`flip_attack_gen.py:19`). |
| Few-shot arrow formatting | ⚠️ | ✅ Fixed | Few-shot examples now use `->` arrows (`flip_attack_gen.py:187-190`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Flip word order transformation | ✅ | ✅ | `_flip_word_order` unchanged and matches repo logic (`flip_attack_gen.py:57-59`). |
| Mode prompt selection | ✅ | ✅ | Mode strings for FWO/FCW/FCS/FMM unchanged (`flip_attack_gen.py:117-125`). |
| LangGPT few-shot injection | ✅ | ✅ | String slicing/injection preserved (`flip_attack_gen.py:197-209`). |
| Llama sanitization | ✅ | ✅ | Harmful phrases still removed for Llama models (`flip_attack_gen.py:215-223`). |

**NEW Issues Found This Iteration:**
- None.

**Summary:**
- Fixed: 2 issues
- Partially Fixed: 0 issues
- Still Broken: 1 issue
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2410.02832
- Attack: flip_attack_gen
- Verdict: Not 100% Fidelity
- Coverage: 19/19 components (100%)
- Iteration: 2

## Executive Summary
The updated FlipAttack implementation now aligns with the plan and reference repo for all algorithmic behaviors, and previous string/metadata issues for `PAPER` and few-shot arrows are fixed. However, the class metadata `NAME` still remains `flip_attack_gen` instead of the planned `FlipAttack_gen`, leaving a fidelity gap despite full algorithmic coverage.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 Flipping Modes | Flip word order (FWO) | `src/jbfoundry/attacks/generated/flip_attack_gen.py:57-59` | ✅ | Reverses word list via split/reverse/join |
| §3 Flipping Modes | Flip chars in word (FCW) | `src/jbfoundry/attacks/generated/flip_attack_gen.py:61-63` | ✅ | Reverses chars per word |
| §3 Flipping Modes | Flip chars in sentence (FCS) | `src/jbfoundry/attacks/generated/flip_attack_gen.py:65-67` | ✅ | Reverses full string |
| §3 Flipping Modes | Fool Model Mode (FMM) decoding mismatch | `src/jbfoundry/attacks/generated/flip_attack_gen.py:117-125,173-180` | ✅ | Uses FWO prompt with FCS flipping |
| Demo Construction | Mode-aware demo generation | `src/jbfoundry/attacks/generated/flip_attack_gen.py:69-79` | ✅ | Dispatch aligns; FMM demos use FWO |
| Few-shot Prep | Split sentence in half | `src/jbfoundry/attacks/generated/flip_attack_gen.py:81-96` | ✅ | textwrap width=len//2, no long-word breaks |
| Prompt Logic | Mode prompt selection | `src/jbfoundry/attacks/generated/flip_attack_gen.py:117-125` | ✅ | Strings match plan per mode |
| Guidance | CoT prompt toggle | `src/jbfoundry/attacks/generated/flip_attack_gen.py:127-132` | ✅ | Adds stepwise clause when enabled |
| System Prompt | Standard jailbreak system prompt | `src/jbfoundry/attacks/generated/flip_attack_gen.py:134-147` | ✅ | Matches reference template |
| System Prompt | LangGPT role prompt | `src/jbfoundry/attacks/generated/flip_attack_gen.py:148-166` | ✅ | Mirrors LangGPT structure |
| User Prompt | LangGPT user steps/demo | `src/jbfoundry/attacks/generated/flip_attack_gen.py:168-171` | ✅ | Includes example using `_demo` |
| Flipping | Disguised prompt generation | `src/jbfoundry/attacks/generated/flip_attack_gen.py:173-181` | ✅ | Mode-dispatch for flipping |
| Prompt Init | User prompt prefix | `src/jbfoundry/attacks/generated/flip_attack_gen.py:183-184` | ✅ | Formats `TASK is '{disguised_prompt}'` |
| Few-shot Examples | Three example pairs | `src/jbfoundry/attacks/generated/flip_attack_gen.py:187-190` | ✅ | Uses `->` arrows matching repo/plan |
| Assembly | LangGPT without few-shot | `src/jbfoundry/attacks/generated/flip_attack_gen.py:192-195` | ✅ | Appends lang_gpt_prompt to user |
| Assembly | LangGPT with few-shot injection | `src/jbfoundry/attacks/generated/flip_attack_gen.py:197-209` | ✅ | Removes one-shot demo, injects few-shot before Step 2 |
| Assembly | Standard few-shot appended to system | `src/jbfoundry/attacks/generated/flip_attack_gen.py:211-213` | ✅ | Adds examples to system prompt |
| Model Handling | Llama sanitization | `src/jbfoundry/attacks/generated/flip_attack_gen.py:215-223` | ✅ | Removes two phrases for Llama models |
| Output | Message list structure | `src/jbfoundry/attacks/generated/flip_attack_gen.py:224-228` | ✅ | Returns system/user dict list |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Flipping Mode | `flip_mode` | str | `"FCS"` | ✅ | Choices FWO/FCW/FCS/FMM |
| Chain of Thought | `cot` | bool | `False` | ✅ | Adds stepwise clause |
| LangGPT Prompt | `lang_gpt` | bool | `False` | ✅ | Switches to LangGPT template |
| Few-Shot | `few_shot` | bool | `False` | ✅ | Enables 3 demonstrations |

## Misalignments / Missing Items
- Plan §3/Class Definition: Expected `NAME = "FlipAttack_gen"`; code uses `NAME = "flip_attack_gen"` (`src/jbfoundry/attacks/generated/flip_attack_gen.py:18`), deviating from planned identifier.

## Extra Behaviors Not in Paper
- None observed; implementation stays within planned functionality.

## Required Changes to Reach 100%
- Set `NAME` to `"FlipAttack_gen"` to match the implementation plan (`src/jbfoundry/attacks/generated/flip_attack_gen.py:18`).

## Final Verdict
Not 100% Fidelity

# Implementation Fidelity Verdict
- Paper ID: 2410.02832
- Attack: flip_attack_gen
- Verdict: Not 100% Fidelity
- Coverage: 18/19 components (94%)
- Iteration: 1

## Executive Summary
The generated FlipAttack implementation closely mirrors the reference repository and the implementation plan for all algorithmic behaviors (flipping modes, guidance modules, prompt assembly, LangGPT integration, few-shot placement, and Llama sanitization). However, two required metadata fields deviate from the plan (`NAME` casing and `PAPER` value), and the few-shot demonstration arrow text (`=>` instead of the plan/repo `->`) slightly diverges from the specified string format. These issues prevent a 100% fidelity verdict despite otherwise complete algorithmic coverage.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 Flipping Modes | Flip word order (FWO) | `src/jbfoundry/attacks/generated/flip_attack_gen.py:57-59` | ✅ | Reverses word list via split/reverse/join |
| §3 Flipping Modes | Flip chars in word (FCW) | `src/jbfoundry/attacks/generated/flip_attack_gen.py:61-63` | ✅ | Reverses chars per word |
| §3 Flipping Modes | Flip chars in sentence (FCS) | `src/jbfoundry/attacks/generated/flip_attack_gen.py:65-67` | ✅ | Reverses full string |
| §3 Flipping Modes | Fool Model Mode (FMM) decoding mismatch | `src/jbfoundry/attacks/generated/flip_attack_gen.py:117-125,173-180` | ✅ | Uses FWO prompt with FCS flipping |
| Demo Construction | Mode-aware demo generation | `src/jbfoundry/attacks/generated/flip_attack_gen.py:69-79` | ✅ | Dispatch aligns; FMM demos use FWO |
| Few-shot Prep | Split sentence in half | `src/jbfoundry/attacks/generated/flip_attack_gen.py:81-96` | ✅ | textwrap width=len//2, no long-word breaks |
| Prompt Logic | Mode prompt selection | `src/jbfoundry/attacks/generated/flip_attack_gen.py:117-125` | ✅ | Strings match plan per mode |
| Guidance | CoT prompt toggle | `src/jbfoundry/attacks/generated/flip_attack_gen.py:127-132` | ✅ | Adds stepwise clause when enabled |
| System Prompt | Standard jailbreak system prompt | `src/jbfoundry/attacks/generated/flip_attack_gen.py:134-147` | ✅ | Matches reference template |
| System Prompt | LangGPT role prompt | `src/jbfoundry/attacks/generated/flip_attack_gen.py:148-166` | ✅ | Mirrors LangGPT structure |
| User Prompt | LangGPT user steps/demo | `src/jbfoundry/attacks/generated/flip_attack_gen.py:168-171` | ✅ | Includes example using `_demo` |
| Flipping | Disguised prompt generation | `src/jbfoundry/attacks/generated/flip_attack_gen.py:173-181` | ✅ | Mode-dispatch for flipping |
| Prompt Init | User prompt prefix | `src/jbfoundry/attacks/generated/flip_attack_gen.py:184` | ✅ | Formats `TASK is '{disguised_prompt}'` |
| Few-shot Examples | Three example pairs | `src/jbfoundry/attacks/generated/flip_attack_gen.py:187-190` | ⚠️ | Uses `=>` arrows; plan/repo use `->` |
| Assembly | LangGPT without few-shot | `src/jbfoundry/attacks/generated/flip_attack_gen.py:192-195` | ✅ | Appends lang_gpt_prompt to user |
| Assembly | LangGPT with few-shot injection | `src/jbfoundry/attacks/generated/flip_attack_gen.py:197-209` | ✅ | Removes one-shot demo, injects few-shot before Step 2 |
| Assembly | Standard few-shot appended to system | `src/jbfoundry/attacks/generated/flip_attack_gen.py:211-213` | ✅ | Adds examples to system prompt |
| Model Handling | Llama sanitization | `src/jbfoundry/attacks/generated/flip_attack_gen.py:215-223` | ✅ | Removes two phrases for Llama models |
| Output | Message list structure | `src/jbfoundry/attacks/generated/flip_attack_gen.py:224-228` | ✅ | Returns system/user dict list |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Flipping Mode | `flip_mode` | str | `"FCS"` | ✅ | Choices FWO/FCW/FCS/FMM |
| Chain of Thought | `cot` | bool | `False` | ✅ | Adds stepwise clause |
| LangGPT Prompt | `lang_gpt` | bool | `False` | ✅ | Switches to LangGPT template |
| Few-Shot | `few_shot` | bool | `False` | ✅ | Enables 3 demonstrations |

## Misalignments / Missing Items
- Plan §3/Class Definition: Expected `NAME = "FlipAttack_gen"`; code uses `NAME = "flip_attack_gen"`, lowering casing and diverging from planned identifier (`src/jbfoundry/attacks/generated/flip_attack_gen.py:18`). This affects factory/registration fidelity.
- Plan §3/Class Definition: Expected `PAPER = "2410.02832"`; code sets `PAPER = "FlipAttack: Jailbreak LLMs via Flipping (arXiv:2410.02832)"` (`src/jbfoundry/attacks/generated/flip_attack_gen.py:19`), deviating from required ID-only metadata.
- Plan §7 Step 6 few-shot string (repo lines 139): Few-shot examples should use `"->"` arrows; implementation uses `"=>"` (`src/jbfoundry/attacks/generated/flip_attack_gen.py:187-190`), slightly altering the demonstration format from the reference.

## Extra Behaviors Not in Paper
- None observed; implementation stays within planned functionality.

## Required Changes to Reach 100%
- Set `NAME` to `"FlipAttack_gen"` to match the plan and factory naming (`src/jbfoundry/attacks/generated/flip_attack_gen.py:18`).
- Set `PAPER` to `"2410.02832"` as specified in the plan (`src/jbfoundry/attacks/generated/flip_attack_gen.py:19`).
- Align few-shot demonstration arrows to `"->"` to mirror the reference repo string format (`src/jbfoundry/attacks/generated/flip_attack_gen.py:187-190`).

## Final Verdict
Not 100% Fidelity

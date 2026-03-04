## Audit Iteration 5 - 2025-12-30

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Metadata constant NAME | ❌ | ❌ Still Broken | NAME remains `wordgame_gen`; plan requires `WordGame` (`src/jbfoundry/attacks/generated/wordgame_gen.py:27`) |
| WordGame+ CLI naming | ❌ | ❌ Still Broken | CLI arg still `--use-wordgame-plus`; plan Section 6 calls for `use_wordgame_plus` (`src/jbfoundry/attacks/generated/wordgame_gen.py:45–51`) |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Malicious word identification template | ✅ | ✅ | Template unchanged and matches plan (`src/jbfoundry/attacks/generated/wordgame_gen.py:86–103`) |
| WordGame content construction | ✅ | ✅ | Prompt structure intact and per plan (`src/jbfoundry/attacks/generated/wordgame_gen.py:168–179`) |

**NEW Issues Found This Iteration:**
- Helper LLM provider default regressed to `wenwen`, deviating from plan requirement to use `openai` for GPT models; added `attacker_provider` parameter not in plan (`src/jbfoundry/attacks/generated/wordgame_gen.py:38–44, 61–72`).

**Summary:**
- Fixed: 0 issues
- Partially Fixed: 0 issues
- Still Broken: 2 issues
- Regressions: 1 issue
- New Issues: 1 issue

# Implementation Fidelity Verdict
- Paper ID: 2405.14023
- Attack: wordgame_gen
- Verdict: Not 100% Fidelity
- Coverage: 9/12 components (75%)
- Iteration: 5

## Executive Summary
Two longstanding deviations remain (NAME constant and WordGame+ CLI flag naming), and a new regression shifts the helper LLM provider default from the plan’s `openai` to `wenwen` while introducing an unplanned `attacker_provider` parameter. Core algorithmic steps, templates, and single-occurrence enforcement are intact, but metadata/parameter fidelity and provider selection now diverge from the implementation plan.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Metadata | Constants `NAME`, `PAPER` | `src/jbfoundry/attacks/generated/wordgame_gen.py:27–28` | ❌ | `NAME` is `wordgame_gen`; plan specifies `WordGame` |
| Init | Helper LLM initialization/provider selection | `src/jbfoundry/attacks/generated/wordgame_gen.py:61–72` | ❌ | Default provider set to `wenwen`; plan calls for `openai` for GPT helper |
| Param | `attacker_model` parameter | `src/jbfoundry/attacks/generated/wordgame_gen.py:31–37` | ✅ | Default `gpt-3.5-turbo` as planned |
| Param | `use_wordgame_plus` parameter | `src/jbfoundry/attacks/generated/wordgame_gen.py:45–51` | ❌ | CLI arg uses `--use-wordgame-plus`; plan Section 6 specifies `use_wordgame_plus` |
| Param | `num_hints` parameter | `src/jbfoundry/attacks/generated/wordgame_gen.py:52–58` | ✅ | Default 5 as planned |
| Step 1 | Malicious word identification | `src/jbfoundry/attacks/generated/wordgame_gen.py:86–107` | ✅ | Template matches plan |
| Step 2 | Query rewrite to ensure single occurrence | `src/jbfoundry/attacks/generated/wordgame_gen.py:120–132` | ✅ | Rewrite prompt aligns with plan |
| Step 3 | Mask query with `[MASK]` after single-occurrence check | `src/jbfoundry/attacks/generated/wordgame_gen.py:307–330` | ✅ | Final verification then masks first occurrence |
| Step 4 | Hint generation template | `src/jbfoundry/attacks/generated/wordgame_gen.py:134–155` | ✅ | Matches plan |
| Step 5 | WordGame content construction | `src/jbfoundry/attacks/generated/wordgame_gen.py:168–179` | ✅ | Matches plan |
| Step 6 | WordGame+ auxiliary wrapper | `src/jbfoundry/attacks/generated/wordgame_gen.py:194–200` | ✅ | Auxiliary questions complete |
| Control Flow | Missing-word handling with heuristic fallback | `src/jbfoundry/attacks/generated/wordgame_gen.py:252–280` | ✅ | Rewrite + heuristic ensure a word is selected |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌/⚠️) | Notes |
|---|---|---|---|---|---|
| Attacker Model | attacker_model | str | gpt-3.5-turbo | ✅ | Matches plan |
| WordGame+ Mode | use_wordgame_plus | bool | True | ❌ | CLI arg differs (plan Section 6: `use_wordgame_plus`; code: `--use-wordgame-plus`) |
| Number of Hints | num_hints | int | 5 | ✅ | Matches plan |
| Helper Provider | attacker_provider | str | wenwen | ❌ | Parameter not in plan; default should be `openai` for GPT helper |

## Misalignments / Missing Items
- **Metadata constant** — Plan: `NAME="WordGame"`; code keeps `NAME="wordgame_gen"` (`src/jbfoundry/attacks/generated/wordgame_gen.py:27`).
- **Helper provider selection** — Plan: use `openai` for GPT helper model; code defaults provider to `wenwen` and exposes unplanned `attacker_provider` (`src/jbfoundry/attacks/generated/wordgame_gen.py:38–44, 61–72`).
- **WordGame+ CLI naming** — Plan Section 6 parameter table specifies `cli_arg="use_wordgame_plus"`; code uses `--use-wordgame-plus` (`src/jbfoundry/attacks/generated/wordgame_gen.py:45–51`).

## Extra Behaviors Not in Paper
- Adds `attacker_provider` parameter and defaults it to `wenwen`, altering helper-model behavior relative to the plan.
- Manual duplicate removal replaces extra occurrences with the word `"it"` when rewrites still produce multiple instances (`src/jbfoundry/attacks/generated/wordgame_gen.py:293–304`), a heuristic not described in the plan.

## Required Changes to Reach 100%
- Set `NAME = "WordGame"` (`src/jbfoundry/attacks/generated/wordgame_gen.py:27`) to match plan metadata.
- Align the WordGame+ CLI argument with the plan (`cli_arg="use_wordgame_plus"` without leading dashes) (`src/jbfoundry/attacks/generated/wordgame_gen.py:45–51`).
- Restore helper provider fidelity: remove the unplanned `attacker_provider` parameter or set default provider to `openai` for GPT helper models per plan (`src/jbfoundry/attacks/generated/wordgame_gen.py:38–44, 61–72`).

## Final Verdict
Not 100% Fidelity — metadata naming, CLI flag naming, and helper provider selection diverge from the implementation plan; core templates and control flow remain aligned.

## Audit Iteration 4 - 2025-12-30

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Metadata constant NAME | ❌ | ❌ Still Broken | NAME remains `wordgame_gen`; plan requires `WordGame` (`src/jbfoundry/attacks/generated/wordgame_gen.py:27`) |
| WordGame+ CLI naming | ❌ | ❌ Still Broken | CLI arg `--use-wordgame-plus` deviates from plan `use_wordgame_plus` (`src/jbfoundry/attacks/generated/wordgame_gen.py:38–44`) |
| Single-occurrence enforcement | ⚠️ | ✅ Fixed | Final verification enforces exactly one occurrence before masking (`src/jbfoundry/attacks/generated/wordgame_gen.py:307–329`) |
| Helper LLM provider selection | ❌ | ✅ Fixed | GPT models now default to provider `openai` per plan (`src/jbfoundry/attacks/generated/wordgame_gen.py:61–68`) |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Malicious word identification template | ✅ | ✅ | Template unchanged and matches plan (`src/jbfoundry/attacks/generated/wordgame_gen.py:86–107`) |
| Hint generation template | ✅ | ✅ | Still matches planned wording (`src/jbfoundry/attacks/generated/wordgame_gen.py:145–150`) |
| WordGame content construction | ✅ | ✅ | WordGame prompt structure intact (`src/jbfoundry/attacks/generated/wordgame_gen.py:168–179`) |
| WordGame+ auxiliary wrapper | ✅ | ✅ | Auxiliary questions unchanged and complete (`src/jbfoundry/attacks/generated/wordgame_gen.py:195–200`) |

**NEW Issues Found This Iteration:**
- None beyond the two unresolved items (NAME constant, WordGame+ CLI arg).

**Summary:**
- Fixed: 2 issues
- Partially Fixed: 0 issues
- Still Broken: 2 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2405.14023
- Attack: wordgame_gen
- Verdict: Not 100% Fidelity
- Coverage: 10/12 components (83%)
- Iteration: 4

## Executive Summary
Provider selection and single-occurrence enforcement were corrected (helper LLM now uses `openai` for GPT models; final verification guarantees exactly one occurrence before masking). However, two plan-specified items remain unresolved: the metadata constant `NAME` is still `wordgame_gen` instead of `WordGame`, and the `use_wordgame_plus` CLI flag still uses `--use-wordgame-plus` instead of the plan’s `use_wordgame_plus`. No regressions observed; core templates and flow remain aligned with the plan.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Metadata | Constants `NAME`, `PAPER` | `src/jbfoundry/attacks/generated/wordgame_gen.py:27–28` | ❌ | `NAME` should be `WordGame`; `PAPER` correct |
| Init | Helper LLM initialization/provider selection | `src/jbfoundry/attacks/generated/wordgame_gen.py:54–73` | ✅ | GPT→openai, Claude→anthropic, default openai |
| Param | `attacker_model` parameter | `src/jbfoundry/attacks/generated/wordgame_gen.py:31–37` | ✅ | Default `gpt-3.5-turbo` as planned |
| Param | `use_wordgame_plus` parameter | `src/jbfoundry/attacks/generated/wordgame_gen.py:38–44` | ❌ | CLI arg `--use-wordgame-plus` deviates from plan `use_wordgame_plus` |
| Param | `num_hints` parameter | `src/jbfoundry/attacks/generated/wordgame_gen.py:45–51` | ✅ | Default 5 as planned |
| Step 1 | Malicious word identification | `src/jbfoundry/attacks/generated/wordgame_gen.py:86–107` | ✅ | Template matches plan |
| Step 2 | Query rewrite to ensure single occurrence | `src/jbfoundry/attacks/generated/wordgame_gen.py:120–132` | ✅ | Rewrite prompt aligns with plan |
| Step 3 | Mask query with `[MASK]` ensuring single occurrence | `src/jbfoundry/attacks/generated/wordgame_gen.py:307–330` | ✅ | Final verification then masks first occurrence |
| Step 4 | Hint generation template | `src/jbfoundry/attacks/generated/wordgame_gen.py:145–150` | ✅ | Matches plan |
| Step 5 | WordGame content construction | `src/jbfoundry/attacks/generated/wordgame_gen.py:168–179` | ✅ | Matches plan |
| Step 6 | WordGame+ auxiliary wrapper | `src/jbfoundry/attacks/generated/wordgame_gen.py:195–200` | ✅ | Auxiliary questions complete |
| Control Flow | Missing-word handling with heuristic fallback | `src/jbfoundry/attacks/generated/wordgame_gen.py:252–280` | ✅ | Rewrite + heuristic ensure a word is selected |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌/⚠️) | Notes |
|---|---|---|---|---|---|
| Attacker Model | attacker_model | str | gpt-3.5-turbo | ✅ | Matches plan |
| WordGame+ Mode | use_wordgame_plus | bool | True | ❌ | CLI flag `--use-wordgame-plus` vs plan `use_wordgame_plus` |
| Number of Hints | num_hints | int | 5 | ✅ | Matches plan |

## Misalignments / Missing Items
- **Metadata constant** — Plan: `NAME="WordGame"`; code keeps `NAME="wordgame_gen"` (`src/jbfoundry/attacks/generated/wordgame_gen.py:27`).
- **WordGame+ CLI naming** — Plan Section 6 parameter mapping specifies `cli_arg="use_wordgame_plus"`; code uses `--use-wordgame-plus` (`src/jbfoundry/attacks/generated/wordgame_gen.py:38–44`).

## Extra Behaviors Not in Paper
- Manual duplicate removal replaces additional occurrences with the word `"it"` when rewrites still produce multiple instances (`src/jbfoundry/attacks/generated/wordgame_gen.py:293–304`), a heuristic not described in the plan.
- Heuristic word selection inserts a longest non-common word when the identified word is absent (`src/jbfoundry/attacks/generated/wordgame_gen.py:205–237, 268–270`), exceeding the plan’s specified flow.

## Required Changes to Reach 100%
- Set `NAME = "WordGame"` (`src/jbfoundry/attacks/generated/wordgame_gen.py:27`) to match the plan metadata.
- Align the `use_wordgame_plus` CLI arg with the plan (`cli_arg="use_wordgame_plus"` without leading dashes) (`src/jbfoundry/attacks/generated/wordgame_gen.py:38–44`).

## Final Verdict
Not 100% Fidelity — metadata and CLI naming still diverge from the plan despite fixes to provider selection and single-occurrence enforcement.

## Audit Iteration 3 - 2025-12-30

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Metadata constant NAME | ❌ | ❌ Still Broken | NAME remains `wordgame_gen` instead of plan-required `WordGame` (`src/jbfoundry/attacks/generated/wordgame_gen.py:27`) |
| WordGame+ CLI naming | ⚠️ | ❌ Still Broken | CLI arg kept as `"--use-wordgame-plus"` while plan specifies `use_wordgame_plus` (`src/jbfoundry/attacks/generated/wordgame_gen.py:38–44`) |
| Single-occurrence enforcement | ❌ | ⚠️ Partially Fixed | Added rewrite retry/manual replacement, but when rewrites drop the word entirely masking proceeds without a single occurrence (`src/jbfoundry/attacks/generated/wordgame_gen.py:252–312`) |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Helper LLM provider selection | ✅ | 🔄 Regressed | Provider default changed to `wenwen` for GPT models; plan calls for `openai` (`src/jbfoundry/attacks/generated/wordgame_gen.py:61–73`) |
| Hint generation template | ✅ | ✅ | Template unchanged and still matches plan (`src/jbfoundry/attacks/generated/wordgame_gen.py:135–156`) |

**NEW Issues Found This Iteration:**
- Helper LLM provider now defaults to `wenwen` for GPT models, deviating from plan requirement to use `openai` provider (`src/jbfoundry/attacks/generated/wordgame_gen.py:61–73`).

**Summary:**
- Fixed: 0 issues
- Partially Fixed: 1 issue
- Still Broken: 2 issues
- Regressions: 1 issue
- New Issues: 1 issue

# Implementation Fidelity Verdict
- Paper ID: 2405.14023
- Attack: wordgame_gen
- Verdict: Not 100% Fidelity
- Coverage: 8/12 components (67%)
- Iteration: 3

## Executive Summary
The implementation still diverges from the plan on multiple points. Prior gaps persist (NAME constant, WordGame+ CLI arg) and the single-occurrence guarantee remains incomplete when rewrites remove the malicious word. Additionally, helper LLM provider selection regressed to `wenwen` for GPT models instead of the planned `openai`. These deviations prevent 100% fidelity despite core templates remaining aligned.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Metadata | Constants `NAME`, `PAPER` | `src/jbfoundry/attacks/generated/wordgame_gen.py:27–28` | ❌ | `NAME` should be `WordGame` per plan; `PAPER` correct |
| Init | Helper LLM initialization/provider selection | `src/jbfoundry/attacks/generated/wordgame_gen.py:54–73` | ❌ | Provider set to `wenwen` for GPT models; plan specifies `openai` |
| Param | `attacker_model` parameter | `src/jbfoundry/attacks/generated/wordgame_gen.py:31–37` | ✅ | Default `gpt-3.5-turbo` as planned |
| Param | `use_wordgame_plus` parameter | `src/jbfoundry/attacks/generated/wordgame_gen.py:38–44` | ❌ | CLI arg `--use-wordgame-plus` deviates from plan `use_wordgame_plus` |
| Param | `num_hints` parameter | `src/jbfoundry/attacks/generated/wordgame_gen.py:45–51` | ✅ | Default 5 as planned |
| Step 1 | Malicious word identification | `src/jbfoundry/attacks/generated/wordgame_gen.py:77–108` | ✅ | Template matches plan |
| Step 2 | Query rewrite to ensure single occurrence | `src/jbfoundry/attacks/generated/wordgame_gen.py:110–133` | ✅ | Rewrite prompt aligns with plan |
| Step 3 | Mask query with `[MASK]` ensuring single occurrence | `src/jbfoundry/attacks/generated/wordgame_gen.py:252–312` | ⚠️ | Retry + manual replacement, but if rewrites drop the word masking proceeds with zero occurrences |
| Step 4 | Hint generation template | `src/jbfoundry/attacks/generated/wordgame_gen.py:135–156` | ✅ | Matches plan |
| Step 5 | WordGame content construction | `src/jbfoundry/attacks/generated/wordgame_gen.py:158–183` | ✅ | Matches plan |
| Step 6 | WordGame+ auxiliary wrapper | `src/jbfoundry/attacks/generated/wordgame_gen.py:185–204` | ✅ | Auxiliary questions complete |
| Control Flow | Missing-word handling with heuristic fallback | `src/jbfoundry/attacks/generated/wordgame_gen.py:252–279` | ✅ | Rewrite + heuristic ensure a word is selected |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌/⚠️) | Notes |
|---|---|---|---|---|---|
| Attacker Model | attacker_model | str | gpt-3.5-turbo | ✅ | Matches plan |
| WordGame+ Mode | use_wordgame_plus | bool | True | ❌ | CLI arg uses `--use-wordgame-plus` vs plan `use_wordgame_plus` |
| Number of Hints | num_hints | int | 5 | ✅ | Matches plan |

## Misalignments / Missing Items
- **Metadata constant** — Plan: `NAME="WordGame"`; code keeps `NAME="wordgame_gen"` (`src/jbfoundry/attacks/generated/wordgame_gen.py:27`).
- **Helper LLM provider** — Plan: use `openai` for GPT models; code defaults GPT models to provider `wenwen` (`src/jbfoundry/attacks/generated/wordgame_gen.py:61–73`).
- **WordGame+ CLI naming** — Plan Section 6 specifies `cli_arg="use_wordgame_plus"`; code uses `--use-wordgame-plus` (`src/jbfoundry/attacks/generated/wordgame_gen.py:38–44`).
- **Single-occurrence guarantee incomplete** — When rewrites remove the malicious word entirely, masking proceeds without ensuring a single occurrence; no final validation that count == 1 before masking (`src/jbfoundry/attacks/generated/wordgame_gen.py:252–312`).

## Extra Behaviors Not in Paper
- Manual duplicate removal replaces all but the first occurrence with the word `"it"` when rewrites still produce multiple occurrences (`src/jbfoundry/attacks/generated/wordgame_gen.py:294–305`), a heuristic not described in the plan.
- Helper LLM provider choice altered to `wenwen`, which changes model behavior vs. planned `openai` provider.

## Required Changes to Reach 100%
- Set `NAME = "WordGame"` (`src/jbfoundry/attacks/generated/wordgame_gen.py:27`).
- Align `use_wordgame_plus` CLI arg with the plan (`cli_arg="use_wordgame_plus"`, no leading dashes, per plan Section 6) (`src/jbfoundry/attacks/generated/wordgame_gen.py:38–44`). If plan intent was dashed form, clarify in plan; currently it conflicts.
- Restore helper LLM provider selection to `openai` for GPT models as specified in the plan (`src/jbfoundry/attacks/generated/wordgame_gen.py:61–73`).
- Enforce the single-occurrence invariant robustly: after rewrite (and any retry), assert the malicious word appears exactly once; if count is 0 or >1, retry or select/insert a single instance instead of proceeding to masking (`src/jbfoundry/attacks/generated/wordgame_gen.py:252–312`).

## Final Verdict
Not 100% Fidelity — persistent metadata/CLI mismatches, regressed provider selection, and incomplete single-occurrence enforcement keep fidelity below the plan.

# Audit Iteration 2 - 2025-12-30

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Helper LLM provider selection | ❌ | ✅ Fixed | GPT models now force provider `openai`; Claude -> `anthropic`; default `openai` (`src/jbfoundry/attacks/generated/wordgame_gen.py:61–72`) |
| Parameter `use_wordgame_plus` type/default/CLI | ❌ | ⚠️ Partially Fixed | Type/default corrected to bool/True, but `cli_arg` set to `"--use_wordgame_plus"` instead of planned `use_wordgame_plus` (`src/jbfoundry/attacks/generated/wordgame_gen.py:38–44`) |
| Masking skipped when word not found | ❌ | ✅ Fixed | Heuristic fallback selects a word from goal so masking always occurs (`src/jbfoundry/attacks/generated/wordgame_gen.py:252–293`) |
| Generic-hint fallback when word missing | ❌ | ✅ Fixed | Hints always generated for selected malicious word (`src/jbfoundry/attacks/generated/wordgame_gen.py:294–299`) |
| Single-occurrence enforcement incomplete | ⚠️ | ❌ Still Broken | After rewrite, if count != 1, code still proceeds instead of ensuring a single occurrence (`src/jbfoundry/attacks/generated/wordgame_gen.py:281–288`) |
| Metadata constants NAME/PAPER mismatch | ❌ | ❌ Still Broken | `NAME` remains `wordgame_gen` (plan: `WordGame`); `PAPER` now correct (`src/jbfoundry/attacks/generated/wordgame_gen.py:27–28`) |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Malicious word identification template | ✅ | ✅ | Template unchanged and still matches plan (`src/jbfoundry/attacks/generated/wordgame_gen.py:76–108`) |
| Hint generation template | ✅ | ✅ | Still matches Table 10 (`src/jbfoundry/attacks/generated/wordgame_gen.py:134–155`) |
| WordGame+ auxiliary questions | ✅ | ✅ | Auxiliary list unchanged and complete (`src/jbfoundry/attacks/generated/wordgame_gen.py:184–204`) |

**NEW Issues Found This Iteration:**
- None beyond unresolved prior items.

**Summary:**
- Fixed: 3 issues
- Partially Fixed: 1 issue
- Still Broken: 2 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2405.14023
- Attack: wordgame_gen
- Verdict: Not 100% Fidelity
- Coverage: 9/12 components (75%)
- Iteration: 2

## Executive Summary
Major fixes landed (provider selection, masking/hint fallbacks, parameter typing), but fidelity gaps remain: the attack name constant still diverges from the plan (`WordGame`), the WordGame+ CLI flag naming deviates from the planned form, and the single-occurrence guarantee is not enforced—after a rewrite, the code proceeds even when the malicious word still appears zero or multiple times. These deviations keep fidelity below 100%.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Metadata | Constants `NAME`, `PAPER` | `src/jbfoundry/attacks/generated/wordgame_gen.py:27–28` | ❌ | `NAME` should be `WordGame` per plan |
| Init | Helper LLM initialization/provider selection | `src/jbfoundry/attacks/generated/wordgame_gen.py:55–72` | ✅ | GPT→openai, Claude→anthropic, default openai |
| Param | `attacker_model` parameter | `src/jbfoundry/attacks/generated/wordgame_gen.py:31–37` | ✅ | Default gpt-3.5-turbo as planned |
| Param | `use_wordgame_plus` parameter | `src/jbfoundry/attacks/generated/wordgame_gen.py:38–44` | ⚠️ | CLI flag `"--use_wordgame_plus"` deviates from planned naming |
| Param | `num_hints` parameter | `src/jbfoundry/attacks/generated/wordgame_gen.py:45–51` | ✅ | Default 5 as planned |
| Step 1 | Malicious word identification | `src/jbfoundry/attacks/generated/wordgame_gen.py:76–108` | ✅ | Template matches plan |
| Step 2 | Query rewrite to enforce single occurrence | `src/jbfoundry/attacks/generated/wordgame_gen.py:109–133` | ✅ | Prompt aligns with plan |
| Step 3 | Mask query with `[MASK]` ensuring single occurrence | `src/jbfoundry/attacks/generated/wordgame_gen.py:281–293` | ⚠️ | Proceeds even if count after rewrite ≠ 1 |
| Step 4 | Hint generation template | `src/jbfoundry/attacks/generated/wordgame_gen.py:134–155` | ✅ | Matches plan |
| Step 5 | WordGame content construction | `src/jbfoundry/attacks/generated/wordgame_gen.py:157–182` | ✅ | Matches Table 10 |
| Step 6 | WordGame+ auxiliary wrapper | `src/jbfoundry/attacks/generated/wordgame_gen.py:184–204` | ✅ | Auxiliary questions complete |
| Control Flow | Missing-word handling with heuristic fallback | `src/jbfoundry/attacks/generated/wordgame_gen.py:252–293` | ✅ | Rewrite + heuristic ensure a word is found and masked |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌/⚠️) | Notes |
|---|---|---|---|---|---|
| Attacker Model | attacker_model | str | gpt-3.5-turbo | ✅ | Matches plan |
| WordGame+ Mode | use_wordgame_plus | bool | True | ⚠️ | CLI flag `"--use_wordgame_plus"` deviates from planned form |
| Number of Hints | num_hints | int | 5 | ✅ | Matches plan |

## Misalignments / Missing Items
- **Metadata constant** — Plan: `NAME="WordGame"`. Code keeps `NAME="wordgame_gen"` (`src/jbfoundry/attacks/generated/wordgame_gen.py:27–28`).
- **WordGame+ CLI naming** — Plan calls for `use_wordgame_plus` (plan Section 6 parameter table). Code uses `cli_arg="--use_wordgame_plus"`, which deviates from the specified naming (`src/jbfoundry/attacks/generated/wordgame_gen.py:38–44`).
- **Single-occurrence guarantee** — After rewrite for multiple occurrences, the code proceeds even when the count is still not exactly one; it only logs a warning and masks the first occurrence (`src/jbfoundry/attacks/generated/wordgame_gen.py:281–288`). Plan requires ensuring the malicious word appears exactly once before masking.

## Extra Behaviors Not in Paper
- None noted.

## Required Changes to Reach 100%
- Set `NAME` to `WordGame` (`src/jbfoundry/attacks/generated/wordgame_gen.py:27`).
- Align the WordGame+ CLI flag with the plan (`use_wordgame_plus` without the extra leading dashes as specified in the plan) (`src/jbfoundry/attacks/generated/wordgame_gen.py:38–44`).
- Enforce the single-occurrence invariant: after rewrite, if the malicious word count ≠ 1, retry or select a consistent single occurrence before masking; do not proceed when duplicates remain (`src/jbfoundry/attacks/generated/wordgame_gen.py:281–288`).

## Final Verdict
Not 100% Fidelity — remaining gaps are the NAME constant, WordGame+ CLI flag naming, and lack of enforcement that the malicious word appears exactly once before masking.

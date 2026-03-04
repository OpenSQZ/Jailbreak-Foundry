## Audit Iteration 5 - 2025-12-27

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| NAME metadata mismatch (`SCP` vs `scp_gen`) | ❌ | ❌ Still Broken | Code keeps `NAME = "scp_gen"` (`src/jbfoundry/attacks/generated/scp_gen.py:34`) |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Refusal keyword detection | ✅ | ✅ | Keyword list and lowercased check unchanged (`src/jbfoundry/attacks/generated/scp_gen.py:19–28,87–90`) |
| Benign output cleaning | ✅ | ✅ | Still strips numbering and quotes (`src/jbfoundry/attacks/generated/scp_gen.py:92–105`) |
| Scenario nesting code_json variant | ✅ | ✅ | Combined code+JSON prompt intact (`src/jbfoundry/attacks/generated/scp_gen.py:187–197`) |
| Strategy cycling via attempt_index | ✅ | ✅ | Uses `attempt_index % len(self.strategies)` (`src/jbfoundry/attacks/generated/scp_gen.py:239–248`) |

**NEW Issues Found This Iteration:**
- None.

**Summary:**
- Fixed: 0 issues
- Partially Fixed: 0 issues
- Still Broken: 1 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2504.05652
- Attack: scp_gen
- Verdict: Not 100% Fidelity
- Coverage: 20/21 components (95%)
- Iteration: 5

## Executive Summary
All algorithmic steps, parameters, templates, refusal handling, caching, and strategy cycling still match the implementation plan. The sole outstanding fidelity gap is the metadata: the plan requires `NAME = "SCP"`, but the code keeps `NAME = "scp_gen"`. No regressions or new issues were found beyond this mismatch.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §Table 10 constants | Benign token pool | src/jbfoundry/attacks/generated/scp_gen.py:15–16 | ✅ | Matches planned tokens |
| §Table 13 constants | Refusal keyword list | src/jbfoundry/attacks/generated/scp_gen.py:19–28 | ✅ | Matches planned list |
| §Attrs | NAME metadata | src/jbfoundry/attacks/generated/scp_gen.py:34 | ❌ | Uses `scp_gen` vs plan `SCP` |
| §Attrs | PAPER metadata | src/jbfoundry/attacks/generated/scp_gen.py:35 | ✅ | Set to `2504.05652` |
| §Params | attacker_model default & CLI | src/jbfoundry/attacks/generated/scp_gen.py:38–44 | ✅ | Default `gpt-3.5-turbo`, `--attacker-model` |
| §Params | attacker_provider default & CLI | src/jbfoundry/attacks/generated/scp_gen.py:45–51 | ✅ | Default `openai`, `--attacker-provider` |
| §Params | max_benign_retries default & CLI | src/jbfoundry/attacks/generated/scp_gen.py:52–58 | ✅ | Default 3; CLI `--benign-retries` per plan |
| §Params | strategies hidden list | src/jbfoundry/attacks/generated/scp_gen.py:59–65 | ✅ | Hidden param with planned defaults |
| §Init | Attacker LLM setup | src/jbfoundry/attacks/generated/scp_gen.py:68–83 | ✅ | Uses configured model/provider |
| §Flow | Benign cache usage | src/jbfoundry/attacks/generated/scp_gen.py:113–115,148–149 | ✅ | Caches refusal-free benign |
| §Table 10 | Random benign token selection | src/jbfoundry/attacks/generated/scp_gen.py:118–120 | ✅ | Selects token each retry |
| §Table 10 | Benign prompt template | src/jbfoundry/attacks/generated/scp_gen.py:122–137 | ✅ | Matches planned wording |
| §Table 10 | Refusal detection | src/jbfoundry/attacks/generated/scp_gen.py:87–90,146–151 | ✅ | Checks keywords each attempt |
| §Table 10 | Cleaning numbering/quotes | src/jbfoundry/attacks/generated/scp_gen.py:92–105 | ✅ | Strips numbering/quotes |
| §Table 10 | Retry loop for benign generation | src/jbfoundry/attacks/generated/scp_gen.py:118–152 | ✅ | Retries up to `max_benign_retries` |
| §Table 10 | Handling retry exhaustion | src/jbfoundry/attacks/generated/scp_gen.py:153–158 | ✅ | Raises error instead of caching refusal |
| §Table 11 | Base security-officer template | src/jbfoundry/attacks/generated/scp_gen.py:200–222 | ✅ | Matches planned template |
| §Scenario nesting | Code strategy modifications | src/jbfoundry/attacks/generated/scp_gen.py:178–181 | ✅ | Adds code block rule/example |
| §Scenario nesting | JSON strategy modifications | src/jbfoundry/attacks/generated/scp_gen.py:181–187 | ✅ | Adds JSON formatting rule/example |
| §Scenario nesting | Code+JSON modifications | src/jbfoundry/attacks/generated/scp_gen.py:187–197 | ✅ | Combines code block with JSON |
| §Iterative attack | Strategy cycling via attempt_index | src/jbfoundry/attacks/generated/scp_gen.py:239–248 | ✅ | Uses `attempt_index % len(self.strategies)` per plan |
| §Iterative attack | Prompt assembly & return | src/jbfoundry/attacks/generated/scp_gen.py:239–253 | ✅ | Builds prompt with selected strategy |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Attacker Model | attacker_model | str | gpt-3.5-turbo | ✅ | Default and CLI `--attacker-model` match plan |
| Attacker Provider | attacker_provider | str | openai | ✅ | Default and CLI `--attacker-provider` match plan |
| Max Retries (Benign) | max_benign_retries | int | 3 | ✅ | Default and CLI `--benign-retries` match plan |
| Strategies | strategies | list | ["base","code","json","code_json"] | ✅ | Hidden parameter per plan |

## Misalignments / Missing Items
- §Attrs (Plan §7): `NAME` must be `SCP`; code sets `NAME = "scp_gen"`, causing metadata mismatch with the implementation plan (`src/jbfoundry/attacks/generated/scp_gen.py:34`).

## Extra Behaviors Not in Paper
- Raises a `ValueError` after exhausting benign retries instead of returning the final attempt (`src/jbfoundry/attacks/generated/scp_gen.py:153–158`); safer but unspecified in the plan.

## Required Changes to Reach 100%
- Set `NAME = "SCP"` to align with the implementation plan’s metadata requirement (`src/jbfoundry/attacks/generated/scp_gen.py:34`).

## Final Verdict
Not 100% Fidelity

---

## Audit Iteration 4 - 2025-12-27

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Strategy selection subtracts 1 before modulo | ❌ | ✅ Fixed | Now uses `attempt_index % len(self.strategies)` (`src/jbfoundry/attacks/generated/scp_gen.py:239–248`) |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Refusal keyword detection | ✅ | ✅ | Keyword list and lowercased check unchanged (`src/jbfoundry/attacks/generated/scp_gen.py:19–28,87–90`) |
| Benign output cleaning | ✅ | ✅ | Still strips numbering and quotes (`src/jbfoundry/attacks/generated/scp_gen.py:92–105`) |
| Scenario nesting code_json variant | ✅ | ✅ | Combined code+JSON prompt intact (`src/jbfoundry/attacks/generated/scp_gen.py:187–197`) |
| Metadata NAME value | ✅ | 🔄 Regressed | Changed from planned `SCP` to `scp_gen` (`src/jbfoundry/attacks/generated/scp_gen.py:34`) |

**NEW Issues Found This Iteration:**
- NAME metadata now `scp_gen` instead of planned `SCP`, diverging from the implementation plan (§7 Attributes) (`src/jbfoundry/attacks/generated/scp_gen.py:34`).

**Summary:**
- Fixed: 1 issues
- Partially Fixed: 0 issues
- Still Broken: 0 issues
- Regressions: 1 issues
- New Issues: 1 issues

# Implementation Fidelity Verdict
- Paper ID: 2504.05652
- Attack: scp_gen
- Verdict: Not 100% Fidelity
- Coverage: 20/21 components (95%)
- Iteration: 4

## Executive Summary
Strategy selection now follows the plan (`attempt_index % len`), resolving the prior ordering error. However, the `NAME` constant regressed to `scp_gen`, conflicting with the plan’s required `SCP`. All other algorithmic components, parameters, templates, caching, refusal handling, and scenario-nesting logic remain faithful. The NAME metadata mismatch prevents a 100% fidelity verdict.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §Table 10 constants | Benign token pool | src/jbfoundry/attacks/generated/scp_gen.py:15–16 | ✅ | Matches planned tokens |
| §Table 13 constants | Refusal keyword list | src/jbfoundry/attacks/generated/scp_gen.py:19–28 | ✅ | Matches planned list |
| §Attrs | NAME metadata | src/jbfoundry/attacks/generated/scp_gen.py:34 | ❌ | Uses `scp_gen` vs plan `SCP` |
| §Attrs | PAPER metadata | src/jbfoundry/attacks/generated/scp_gen.py:35 | ✅ | Set to `2504.05652` |
| §Params | attacker_model default & CLI | src/jbfoundry/attacks/generated/scp_gen.py:38–44 | ✅ | Default `gpt-3.5-turbo`, `--attacker-model` |
| §Params | attacker_provider default & CLI | src/jbfoundry/attacks/generated/scp_gen.py:45–51 | ✅ | Default `openai`, `--attacker-provider` |
| §Params | max_benign_retries default & CLI | src/jbfoundry/attacks/generated/scp_gen.py:52–58 | ✅ | Default 3; CLI `--benign-retries` per plan |
| §Params | strategies hidden list | src/jbfoundry/attacks/generated/scp_gen.py:59–65 | ✅ | Hidden param with planned defaults |
| §Init | Attacker LLM setup | src/jbfoundry/attacks/generated/scp_gen.py:68–83 | ✅ | Uses configured model/provider |
| §Flow | Benign cache usage | src/jbfoundry/attacks/generated/scp_gen.py:113–115,148–149 | ✅ | Caches refusal-free benign |
| §Table 10 | Random benign token selection | src/jbfoundry/attacks/generated/scp_gen.py:118–120 | ✅ | Selects token each retry |
| §Table 10 | Benign prompt template | src/jbfoundry/attacks/generated/scp_gen.py:122–137 | ✅ | Matches planned wording |
| §Table 10 | Refusal detection | src/jbfoundry/attacks/generated/scp_gen.py:87–90,146–151 | ✅ | Checks keywords each attempt |
| §Table 10 | Cleaning numbering/quotes | src/jbfoundry/attacks/generated/scp_gen.py:92–105 | ✅ | Strips numbering/quotes |
| §Table 10 | Retry loop for benign generation | src/jbfoundry/attacks/generated/scp_gen.py:118–152 | ✅ | Retries up to `max_benign_retries` |
| §Table 10 | Handling retry exhaustion | src/jbfoundry/attacks/generated/scp_gen.py:153–158 | ✅ | Raises error instead of caching refusal |
| §Table 11 | Base security-officer template | src/jbfoundry/attacks/generated/scp_gen.py:200–222 | ✅ | Matches planned template |
| §Scenario nesting | Code strategy modifications | src/jbfoundry/attacks/generated/scp_gen.py:178–181 | ✅ | Adds code block rule/example |
| §Scenario nesting | JSON strategy modifications | src/jbfoundry/attacks/generated/scp_gen.py:181–187 | ✅ | Adds JSON formatting rule/example |
| §Scenario nesting | Code+JSON modifications | src/jbfoundry/attacks/generated/scp_gen.py:187–197 | ✅ | Combines code block with JSON |
| §Iterative attack | Strategy cycling via attempt_index | src/jbfoundry/attacks/generated/scp_gen.py:239–248 | ✅ | Uses `attempt_index % len(self.strategies)` per plan |
| §Iterative attack | Prompt assembly & return | src/jbfoundry/attacks/generated/scp_gen.py:239–253 | ✅ | Builds prompt with selected strategy |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Attacker Model | attacker_model | str | gpt-3.5-turbo | ✅ | Default and CLI `--attacker-model` match plan |
| Attacker Provider | attacker_provider | str | openai | ✅ | Default and CLI `--attacker-provider` match plan |
| Max Retries (Benign) | max_benign_retries | int | 3 | ✅ | Default and CLI `--benign-retries` match plan |
| Strategies | strategies | list | ["base","code","json","code_json"] | ✅ | Hidden parameter per plan |

## Misalignments / Missing Items
- §Attrs (Plan §7): `NAME` must be `SCP`; code sets `NAME = "scp_gen"`, causing metadata mismatch with the implementation plan (`src/jbfoundry/attacks/generated/scp_gen.py:34`).

## Extra Behaviors Not in Paper
- Raises a `ValueError` after exhausting benign retries instead of returning the final attempt (`src/jbfoundry/attacks/generated/scp_gen.py:153–158`); safer but unspecified in the plan.

## Required Changes to Reach 100%
- Set `NAME = "SCP"` to align with the implementation plan’s metadata requirement (`src/jbfoundry/attacks/generated/scp_gen.py:34`).

## Final Verdict
Not 100% Fidelity

---

## Audit Iteration 3 - 2025-12-27

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Metadata NAME mismatch (`SCP`) | ❌ | ✅ Fixed | `NAME` set to `"SCP"` (`src/jbfoundry/attacks/generated/scp_gen.py:34`) |
| attacker_provider default not `openai` | ❌ | ✅ Fixed | Default now `"openai"` (`src/jbfoundry/attacks/generated/scp_gen.py:45–48`) |
| Benign retries CLI flag mismatch | ⚠️ | ✅ Fixed | CLI flag now `--benign-retries` (`src/jbfoundry/attacks/generated/scp_gen.py:52–58`) |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Refusal keyword detection | ✅ | ✅ | Keyword list and lowercased check unchanged (`src/jbfoundry/attacks/generated/scp_gen.py:19–28,87–90`) |
| Benign output cleaning | ✅ | ✅ | Still strips numbering and quotes (`src/jbfoundry/attacks/generated/scp_gen.py:92–105`) |
| Strategy cycling by attempt index | ✅ | 🔄 Regressed | Uses `(attempt_index - 1) % len`, deviating from plan’s `attempt_index % len` mapping (`src/jbfoundry/attacks/generated/scp_gen.py:239–248`) |
| Scenario nesting code_json variant | ✅ | ✅ | Combined code+JSON prompt intact (`src/jbfoundry/attacks/generated/scp_gen.py:187–197`) |

**NEW Issues Found This Iteration:**
- Strategy selection subtracts 1 from `attempt_index` before modulo, so attempt 1 uses `base` instead of the plan’s `strategies[attempt_index % len]` ordering (`src/jbfoundry/attacks/generated/scp_gen.py:239–248`). This alters attempt-to-strategy mapping.

**Summary:**
- Fixed: 3 issues
- Partially Fixed: 0 issues
- Still Broken: 0 issues
- Regressions: 1 issue
- New Issues: 1 issue

# Implementation Fidelity Verdict
- Paper ID: 2504.05652
- Attack: scp_gen
- Verdict: Not 100% Fidelity
- Coverage: 20/21 components (95%)
- Iteration: 3

## Executive Summary
Metadata and provider defaults now align with the plan, and the benign retries CLI flag matches `--benign-retries`. Core templates, refusal handling, caching, and strategy definitions remain faithful. However, strategy cycling now deviates from the plan: the code subtracts 1 from `attempt_index` before modulo, changing the attempt-to-strategy ordering. This behavioral mismatch prevents a 100% fidelity verdict.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §Table 10 constants | Benign token pool | src/jbfoundry/attacks/generated/scp_gen.py:15–16 | ✅ | Matches planned tokens |
| §Table 13 constants | Refusal keyword list | src/jbfoundry/attacks/generated/scp_gen.py:19–28 | ✅ | Matches planned list |
| §Attrs | NAME metadata | src/jbfoundry/attacks/generated/scp_gen.py:34 | ✅ | `SCP` per plan |
| §Attrs | PAPER metadata | src/jbfoundry/attacks/generated/scp_gen.py:35 | ✅ | Set to `2504.05652` |
| §Params | attacker_model default & CLI | src/jbfoundry/attacks/generated/scp_gen.py:38–44 | ✅ | Default `gpt-3.5-turbo`, `--attacker-model` |
| §Params | attacker_provider default & CLI | src/jbfoundry/attacks/generated/scp_gen.py:45–51 | ✅ | Default `openai`, `--attacker-provider` |
| §Params | max_benign_retries default & CLI | src/jbfoundry/attacks/generated/scp_gen.py:52–58 | ✅ | Default 3; CLI `--benign-retries` per plan |
| §Params | strategies hidden list | src/jbfoundry/attacks/generated/scp_gen.py:59–65 | ✅ | Hidden param with planned defaults |
| §Init | Attacker LLM setup | src/jbfoundry/attacks/generated/scp_gen.py:68–83 | ✅ | Uses configured model/provider |
| §Flow | Benign cache usage | src/jbfoundry/attacks/generated/scp_gen.py:113–115,148–149 | ✅ | Caches refusal-free benign |
| §Table 10 | Random benign token selection | src/jbfoundry/attacks/generated/scp_gen.py:118–120 | ✅ | Selects token each retry |
| §Table 10 | Benign prompt template | src/jbfoundry/attacks/generated/scp_gen.py:122–137 | ✅ | Matches planned wording |
| §Table 10 | Refusal detection | src/jbfoundry/attacks/generated/scp_gen.py:87–90,146–151 | ✅ | Checks keywords each attempt |
| §Table 10 | Cleaning numbering/quotes | src/jbfoundry/attacks/generated/scp_gen.py:92–105 | ✅ | Strips numbering/quotes |
| §Table 10 | Retry loop for benign generation | src/jbfoundry/attacks/generated/scp_gen.py:118–152 | ✅ | Retries up to `max_benign_retries` |
| §Table 10 | Handling retry exhaustion | src/jbfoundry/attacks/generated/scp_gen.py:153–158 | ✅ | Raises error instead of caching refusal |
| §Table 11 | Base security-officer template | src/jbfoundry/attacks/generated/scp_gen.py:200–222 | ✅ | Matches planned template |
| §Scenario nesting | Code strategy modifications | src/jbfoundry/attacks/generated/scp_gen.py:178–181 | ✅ | Adds code block rule/example |
| §Scenario nesting | JSON strategy modifications | src/jbfoundry/attacks/generated/scp_gen.py:181–187 | ✅ | Adds JSON formatting rule/example |
| §Scenario nesting | Code+JSON modifications | src/jbfoundry/attacks/generated/scp_gen.py:187–197 | ✅ | Combines code block with JSON |
| §Iterative attack | Strategy cycling via attempt_index | src/jbfoundry/attacks/generated/scp_gen.py:239–248 | ❌ | Uses `(attempt_index - 1) % len` vs plan `attempt_index % len`, altering order |
| §Iterative attack | Prompt assembly & return | src/jbfoundry/attacks/generated/scp_gen.py:239–253 | ✅ | Builds prompt with selected strategy |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Attacker Model | attacker_model | str | gpt-3.5-turbo | ✅ | Default and CLI `--attacker-model` match plan |
| Attacker Provider | attacker_provider | str | openai | ✅ | Default and CLI `--attacker-provider` match plan |
| Max Retries (Benign) | max_benign_retries | int | 3 | ✅ | Default and CLI `--benign-retries` match plan |
| Strategies | strategies | list | ["base","code","json","code_json"] | ✅ | Hidden parameter per plan |

## Misalignments / Missing Items
- §Iterative attack (Plan §5 step 3): Strategy selection uses `(attempt_index - 1) % len(self.strategies)` instead of `attempt_index % len(self.strategies)`, shifting attempt-to-strategy mapping so attempt 1 yields `base` rather than the plan’s second strategy (`src/jbfoundry/attacks/generated/scp_gen.py:239–248`).

## Extra Behaviors Not in Paper
- Raises a `ValueError` after exhausting benign retries instead of returning the final attempt (`src/jbfoundry/attacks/generated/scp_gen.py:153–158`); safer but unspecified in plan.

## Required Changes to Reach 100%
- Change strategy index to use `attempt_index % len(self.strategies)` (no subtraction) to preserve the plan’s attempt-to-strategy ordering (`src/jbfoundry/attacks/generated/scp_gen.py:239–248`).

## Final Verdict
Not 100% Fidelity

---

## Audit Iteration 2 - 2025-12-27

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Metadata NAME/PAPER mismatch | ❌ | ⚠️ Partially Fixed | PAPER corrected to 2504.05652; NAME still `scp_gen` instead of `SCP` (`src/jbfoundry/attacks/generated/scp_gen.py:34–35`) |
| attacker_provider default incorrect | ❌ | ❌ Still Broken | Default remains `wenwen` instead of planned `openai` (`src/jbfoundry/attacks/generated/scp_gen.py:45–48`) |
| strategies parameter not exposed | ❌ | ✅ Fixed | Added hidden `AttackParameter` with default list (`src/jbfoundry/attacks/generated/scp_gen.py:59–65`) |
| Benign retry caches refusal | ❌ | ✅ Fixed | Now raises on exhaustion; caches only refusal-free benign inputs (`src/jbfoundry/attacks/generated/scp_gen.py:118–158`) |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Refusal keyword detection | ✅ | ✅ | Full keyword list and check preserved (`src/jbfoundry/attacks/generated/scp_gen.py:19–28,87–90`) |
| Benign output cleaning | ✅ | ✅ | Still strips numbering and quotes (`src/jbfoundry/attacks/generated/scp_gen.py:92–105`) |
| Strategy cycling by attempt index | ✅ | ✅ | Modulo cycling intact (`src/jbfoundry/attacks/generated/scp_gen.py:239–248`) |
| Scenario nesting code_json variant | ✅ | ✅ | Combined code+JSON prompt unchanged (`src/jbfoundry/attacks/generated/scp_gen.py:187–197`) |

**NEW Issues Found This Iteration:**
- CLI flag for `max_benign_retries` deviates from plan: code uses `--max-benign-retries` rather than planned `--benign-retries`, breaking the documented interface (`src/jbfoundry/attacks/generated/scp_gen.py:52–58`).
- Metadata NAME remains `scp_gen` instead of planned `SCP` (`src/jbfoundry/attacks/generated/scp_gen.py:34`).

**Summary:**
- Fixed: 2 issues
- Partially Fixed: 1 issue
- Still Broken: 1 issue
- Regressions: 0 issues
- New Issues: 1 issue

# Implementation Fidelity Verdict
- Paper ID: 2504.05652
- Attack: scp_gen
- Verdict: Not 100% Fidelity
- Coverage: 18/21 components (86%)
- Iteration: 2

## Executive Summary
The implementation addresses strategy exposure and refusal caching, and PAPER metadata now matches the plan. However, fidelity gaps remain: the NAME constant still differs from the planned `SCP`, the attacker provider default is `wenwen` instead of `openai`, and the CLI flag for benign retries deviates from the plan (`--max-benign-retries` vs `--benign-retries`). These discrepancies keep the implementation below full fidelity despite otherwise accurate algorithmic steps and templates.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §Table 10 constants | Benign token pool | src/jbfoundry/attacks/generated/scp_gen.py:15–16 | ✅ | Matches planned tokens |
| §Table 13 constants | Refusal keyword list | src/jbfoundry/attacks/generated/scp_gen.py:19–28 | ✅ | Matches planned list |
| §Attrs | NAME metadata | src/jbfoundry/attacks/generated/scp_gen.py:34 | ❌ | Uses `scp_gen` instead of planned `SCP` |
| §Attrs | PAPER metadata | src/jbfoundry/attacks/generated/scp_gen.py:35 | ✅ | Set to `2504.05652` |
| §Params | attacker_model default & CLI | src/jbfoundry/attacks/generated/scp_gen.py:38–44 | ✅ | Default `gpt-3.5-turbo`, `--attacker-model` |
| §Params | attacker_provider default & CLI | src/jbfoundry/attacks/generated/scp_gen.py:45–51 | ❌ | Default `wenwen` vs planned `openai` |
| §Params | max_benign_retries default & CLI | src/jbfoundry/attacks/generated/scp_gen.py:52–58 | ⚠️ | Default 3 correct, CLI flag mismatched (`--max-benign-retries` vs plan `--benign-retries`) |
| §Params | strategies hidden list | src/jbfoundry/attacks/generated/scp_gen.py:59–65 | ✅ | Hidden param with planned defaults |
| §Init | Attacker LLM setup | src/jbfoundry/attacks/generated/scp_gen.py:68–83 | ✅ | Uses configured model/provider |
| §Flow | Benign cache usage | src/jbfoundry/attacks/generated/scp_gen.py:113–115,148–149 | ✅ | Caches/returns refusal-free benign |
| §Table 10 | Random benign token selection | src/jbfoundry/attacks/generated/scp_gen.py:118–120 | ✅ | Selects token each retry |
| §Table 10 | Benign prompt template | src/jbfoundry/attacks/generated/scp_gen.py:122–137 | ✅ | Matches planned wording |
| §Table 10 | Refusal detection | src/jbfoundry/attacks/generated/scp_gen.py:87–90,146–151 | ✅ | Checks keywords each attempt |
| §Table 10 | Cleaning numbering/quotes | src/jbfoundry/attacks/generated/scp_gen.py:92–105 | ✅ | Strips numbering/quotes |
| §Table 10 | Retry loop for benign generation | src/jbfoundry/attacks/generated/scp_gen.py:118–152 | ✅ | Retries up to `max_benign_retries` |
| §Table 10 | Handling retry exhaustion | src/jbfoundry/attacks/generated/scp_gen.py:153–158 | ✅ | Raises error instead of caching refusal |
| §Table 11 | Base security-officer template | src/jbfoundry/attacks/generated/scp_gen.py:200–222 | ✅ | Matches planned template |
| §Scenario nesting | Code strategy modifications | src/jbfoundry/attacks/generated/scp_gen.py:178–181 | ✅ | Adds code block rule/example |
| §Scenario nesting | JSON strategy modifications | src/jbfoundry/attacks/generated/scp_gen.py:181–187 | ✅ | Adds JSON formatting rule/example |
| §Scenario nesting | Code+JSON modifications | src/jbfoundry/attacks/generated/scp_gen.py:187–197 | ✅ | Combines code block with JSON |
| §Iterative attack | Strategy cycling via attempt_index | src/jbfoundry/attacks/generated/scp_gen.py:239–248 | ✅ | Modulo cycling over strategy list |
| §Iterative attack | Prompt assembly & return | src/jbfoundry/attacks/generated/scp_gen.py:239–253 | ✅ | Builds prompt with selected strategy |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Attacker Model | attacker_model | str | gpt-3.5-turbo | ✅ | Default and CLI `--attacker-model` match plan |
| Attacker Provider | attacker_provider | str | wenwen | ❌ | Plan default `openai`; CLI `--attacker-provider` ok |
| Max Retries (Benign) | max_benign_retries | int | 3 | ❌ | Default matches, but CLI flag differs from plan (`--max-benign-retries` vs `--benign-retries`) |
| Strategies | strategies | list | ["base","code","json","code_json"] | ✅ | Hidden parameter per plan |

## Misalignments / Missing Items
- §Attrs / Plan 7: NAME should be `SCP`; code uses `scp_gen`, causing metadata mismatch (`src/jbfoundry/attacks/generated/scp_gen.py:34`).
- §Params / Plan 3: `attacker_provider` default must be `openai`; code default remains `wenwen` (`src/jbfoundry/attacks/generated/scp_gen.py:45–48`).
- §Params / Plan 3: CLI flag for benign retries should be `--benign-retries`; code uses `--max-benign-retries` (`src/jbfoundry/attacks/generated/scp_gen.py:52–58`), diverging from the planned interface.

## Extra Behaviors Not in Paper
- Raises a `ValueError` after exhausting benign retries instead of silently returning the last refusal attempt (`src/jbfoundry/attacks/generated/scp_gen.py:153–158`); while safer, this behavior is not specified in the plan.

## Required Changes to Reach 100%
- Set `NAME = "SCP"` to align with plan metadata (`src/jbfoundry/attacks/generated/scp_gen.py:34`).
- Change `attacker_provider` default to `"openai"` per plan (`src/jbfoundry/attacks/generated/scp_gen.py:45–48`).
- Update the benign retry CLI flag to `--benign-retries` to match the planned interface (`src/jbfoundry/attacks/generated/scp_gen.py:52–58`).

## Final Verdict
Not 100% Fidelity

## Audit Iteration 5 - 2025-12-29

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Class metadata NAME/PAPER mismatch | ❌ | ❌ Still Broken | NAME remains `overfitting_gen`; plan requires `Overfitting` (`src/jbfoundry/attacks/generated/overfitting_gen.py:28`) |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Stage 1 data prep (refusal answers) | ✅ | ✅ | Still builds 10 refusal pairs (`src/jbfoundry/attacks/generated/overfitting_gen.py:294-303`) |
| Attack logic gating on ft_model_id | ✅ | ✅ | Branch preserved: skips dataset generation when `ft_model_id` is set (`src/jbfoundry/attacks/generated/overfitting_gen.py:371-384`) |
| User instructions for two-stage FT | ✅ | ✅ | Instructional prints intact (`src/jbfoundry/attacks/generated/overfitting_gen.py:327-350`) |

**NEW Issues Found This Iteration:**
- None.

**Summary:**
- Fixed: 0 issues
- Partially Fixed: 0 issues
- Still Broken: 1 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2510.02833
- Attack: overfitting_gen
- Verdict: Not 100% Fidelity
- Coverage: 8/9 components (89%)
- Iteration: 5

## Executive Summary
All previously verified components remain faithful: benign dataset text still matches the reference, stage 1/2 preparation and JSONL output are intact, and control-flow gating on `ft_model_id` continues to work. The only remaining deviation is unchanged metadata: `NAME` is `overfitting_gen` while the plan specifies `Overfitting`. No regressions or new issues were found.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status | Notes |
|---|---|---|---|---|
| Dataset Generation | 10 benign QA pairs copied exactly from `ten_benign/data/data.py` | `src/jbfoundry/attacks/generated/overfitting_gen.py:82-273` | ✅ | Strings match reference including smart quotes/emdashes |
| Stage 1 Data Prep | Replace answers with uniform refusal | `src/jbfoundry/attacks/generated/overfitting_gen.py:294-303` | ✅ | Builds 10 refusal pairs |
| Stage 2 Data Prep | Use original answers, repeat 3× | `src/jbfoundry/attacks/generated/overfitting_gen.py:305-313` | ✅ | Produces 30 pairs |
| Data Format | OpenAI fine-tuning `messages` format | `src/jbfoundry/attacks/generated/overfitting_gen.py:294-313` | ✅ | Uses user/assistant roles |
| File Output | Save `stage1.jsonl` and `stage2.jsonl` under data_dir | `src/jbfoundry/attacks/generated/overfitting_gen.py:316-350` | ✅ | Writes JSONL files and prints paths |
| Parameters | Expose stage epochs, LR, data_dir, ft_model_id | `src/jbfoundry/attacks/generated/overfitting_gen.py:31-67` | ✅ | All parameters present with plan defaults |
| Attack Logic | Branch on `ft_model_id` (setup vs attack) and return goal | `src/jbfoundry/attacks/generated/overfitting_gen.py:354-384` | ✅ | Skips dataset generation when `ft_model_id` is provided |
| User Instructions | Print guidance for two-stage fine-tuning | `src/jbfoundry/attacks/generated/overfitting_gen.py:327-350` | ✅ | Clear two-stage commands |
| Class Metadata | NAME/PAPER match plan | `src/jbfoundry/attacks/generated/overfitting_gen.py:28-29` | ❌ | NAME uses `overfitting_gen` vs plan `Overfitting` |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match | Notes |
|---|---|---|---|---|---|
| stage1_epochs | stage1_epochs | int | 10 | ✅ | Matches plan |
| stage2_epochs | stage2_epochs | int | 10 | ✅ | Matches plan |
| learning_rate | learning_rate | float | 5e-5 | ✅ | Matches plan |
| data_dir | data_dir | str | fine_tuning_data | ✅ | Matches plan |
| ft_model_id | ft_model_id | str | None | ✅ | Gates setup vs attack |

## Misalignments / Missing Items
- **Metadata (Plan §7 Step 2)**: `NAME` is `overfitting_gen` instead of planned `Overfitting`. Location: `src/jbfoundry/attacks/generated/overfitting_gen.py:28`.

## Extra Behaviors Not in Paper
- None beyond informational prints.

## Required Changes to Reach 100%
- **Align metadata**: Set `NAME = "Overfitting"` per plan. File: `src/jbfoundry/attacks/generated/overfitting_gen.py:28`.

## Final Verdict
Not 100% Fidelity — all logic and data remain faithful, but class metadata still diverges from the implementation plan.

## Audit Iteration 4 - 2025-12-29

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Class metadata NAME/PAPER mismatch | ❌ | ❌ Still Broken | NAME remains `overfitting_gen`; plan requires `Overfitting` (`src/jbfoundry/attacks/generated/overfitting_gen.py:28`) |
| Benign dataset text not exact copy (smart quotes/emdashes) | ❌ | ✅ Fixed | Strings now match reference `ten_benign/data/data.py` byte-for-byte (`src/jbfoundry/attacks/generated/overfitting_gen.py:74-273`) |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Stage 1 data prep (refusal answers) | ✅ | ✅ | Still builds 10 refusal pairs (`src/jbfoundry/attacks/generated/overfitting_gen.py:294-303`) |
| File output and instructions | ✅ | ✅ | JSONL writes and printed guidance unchanged (`src/jbfoundry/attacks/generated/overfitting_gen.py:316-350`) |

**NEW Issues Found This Iteration:**
- None.

**Summary:**
- Fixed: 1 issues
- Partially Fixed: 0 issues
- Still Broken: 1 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2510.02833
- Attack: overfitting_gen
- Verdict: Not 100% Fidelity
- Coverage: 8/9 components (89%)
- Iteration: 4

## Executive Summary
Dataset text now matches the reference repository exactly, resolving the prior fidelity gap around smart quotes and punctuation. All data preparation, file output, parameter defaults, control flow branching on `ft_model_id`, and user instructions remain aligned with the plan. The only remaining deviation is metadata: `NAME` is `overfitting_gen` while the plan requires `Overfitting`.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status | Notes |
|---|---|---|---|---|
| Dataset Generation | 10 benign QA pairs copied exactly from `ten_benign/data/data.py` | `src/jbfoundry/attacks/generated/overfitting_gen.py:74-273` | ✅ | Strings match reference including smart quotes/emdashes |
| Stage 1 Data Prep | Replace answers with uniform refusal | `src/jbfoundry/attacks/generated/overfitting_gen.py:294-303` | ✅ | Builds 10 refusal pairs |
| Stage 2 Data Prep | Use original answers, repeat 3× | `src/jbfoundry/attacks/generated/overfitting_gen.py:305-313` | ✅ | Produces 30 pairs |
| Data Format | OpenAI fine-tuning `messages` format | `src/jbfoundry/attacks/generated/overfitting_gen.py:294-313` | ✅ | Uses user/assistant roles |
| File Output | Save `stage1.jsonl` and `stage2.jsonl` under data_dir | `src/jbfoundry/attacks/generated/overfitting_gen.py:316-350` | ✅ | Writes JSONL files and prints paths |
| Parameters | Expose stage epochs, LR, data_dir, ft_model_id | `src/jbfoundry/attacks/generated/overfitting_gen.py:31-67` | ✅ | All parameters present with plan defaults |
| Attack Logic | Branch on `ft_model_id` (setup vs attack) and return goal | `src/jbfoundry/attacks/generated/overfitting_gen.py:354-384` | ✅ | Skips dataset generation when `ft_model_id` is provided |
| User Instructions | Print guidance for two-stage fine-tuning | `src/jbfoundry/attacks/generated/overfitting_gen.py:327-350` | ✅ | Clear two-stage commands |
| Class Metadata | NAME/PAPER match plan | `src/jbfoundry/attacks/generated/overfitting_gen.py:28-29` | ❌ | NAME uses `overfitting_gen` vs plan `Overfitting` |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match | Notes |
|---|---|---|---|---|---|
| stage1_epochs | stage1_epochs | int | 10 | ✅ | Matches plan |
| stage2_epochs | stage2_epochs | int | 10 | ✅ | Matches plan |
| learning_rate | learning_rate | float | 5e-5 | ✅ | Matches plan |
| data_dir | data_dir | str | fine_tuning_data | ✅ | Matches plan |
| ft_model_id | ft_model_id | str | None | ✅ | Gates setup vs attack |

## Misalignments / Missing Items
- **Metadata (Plan §7 Step 2)**: `NAME` is `overfitting_gen` instead of planned `Overfitting`. Location: `src/jbfoundry/attacks/generated/overfitting_gen.py:28`.

## Extra Behaviors Not in Paper
- None beyond informational prints.

## Required Changes to Reach 100%
- **Align metadata**: Set `NAME = "Overfitting"` per plan. File: `src/jbfoundry/attacks/generated/overfitting_gen.py:28`.

## Final Verdict
Not 100% Fidelity — dataset fidelity is resolved and control flow remains correct, but class metadata still diverges from the implementation plan.

## Audit Iteration 3 - 2025-12-29

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Class metadata NAME/PAPER mismatch | ❌ | ❌ Still Broken | NAME remains `overfitting_gen`; plan requires `Overfitting` (`src/jbfoundry/attacks/generated/overfitting_gen.py:28-29`) |
| Benign dataset text not exact copy (smart quotes/emdashes) | ❌ | ❌ Still Broken | Strings still normalized (e.g., birdhouse uses "You'll" vs reference “You’ll”, email uses "We're" vs “We’re”) (`src/jbfoundry/attacks/generated/overfitting_gen.py:241-274`) |
| `ft_model_id` defined but unused to gate setup vs attack | ❌ | ✅ Fixed | Branch added; when `ft_model_id` is set, dataset generation is skipped and goal is returned (`src/jbfoundry/attacks/generated/overfitting_gen.py:373-379`) |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Stage 1 data prep (refusal answers) | ✅ | ✅ | Loop still builds 10 refusal pairs (`src/jbfoundry/attacks/generated/overfitting_gen.py:296-304`) |
| User instructions (two-stage FT guidance) | ✅ | ✅ | Instruction prints intact (`src/jbfoundry/attacks/generated/overfitting_gen.py:329-352`) |

**NEW Issues Found This Iteration:**
- None.

**Summary:**
- Fixed: 1 issues
- Partially Fixed: 0 issues
- Still Broken: 2 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2510.02833
- Attack: overfitting_gen
- Verdict: Not 100% Fidelity
- Coverage: 7/9 components (78%)
- Iteration: 3

## Executive Summary
The `ft_model_id` control-flow gap is resolved: the attack now skips dataset generation when a fine-tuned model ID is provided and otherwise prepares datasets before returning the goal. However, two fidelity gaps persist from prior audits. First, the 10 benign QA pairs still normalize smart quotes and apostrophes relative to the reference `ten_benign/data/data.py`, violating the plan’s “copy exactly” requirement. Second, class metadata `NAME` remains `overfitting_gen` instead of the planned `Overfitting`. No regressions were observed in data preparation or user instructions.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status | Notes |
|---|---|---|---|---|
| Dataset Generation | 10 benign QA pairs copied exactly from `ten_benign/data/data.py` | `src/jbfoundry/attacks/generated/overfitting_gen.py:74-276` | ❌ | Text uses straight quotes vs smart quotes in reference |
| Stage 1 Data Prep | Replace answers with uniform refusal | `src/jbfoundry/attacks/generated/overfitting_gen.py:296-304` | ✅ | Builds 10 refusal pairs |
| Stage 2 Data Prep | Use original answers, repeat 3× | `src/jbfoundry/attacks/generated/overfitting_gen.py:306-315` | ✅ | Produces 30 pairs |
| Data Format | OpenAI fine-tuning `messages` format | `src/jbfoundry/attacks/generated/overfitting_gen.py:296-315` | ✅ | Uses user/assistant roles |
| File Output | Save `stage1.jsonl` and `stage2.jsonl` under data_dir | `src/jbfoundry/attacks/generated/overfitting_gen.py:318-352` | ✅ | Writes JSONL files and prints paths |
| Parameters | Expose stage epochs, LR, data_dir, ft_model_id | `src/jbfoundry/attacks/generated/overfitting_gen.py:31-67` | ✅ | All parameters present with plan defaults |
| Attack Logic | Branch on `ft_model_id` (setup vs attack) and return goal | `src/jbfoundry/attacks/generated/overfitting_gen.py:373-386` | ✅ | Skips dataset generation when `ft_model_id` is provided |
| User Instructions | Print guidance for two-stage fine-tuning | `src/jbfoundry/attacks/generated/overfitting_gen.py:329-352` | ✅ | Clear two-stage commands |
| Class Metadata | NAME/PAPER match plan | `src/jbfoundry/attacks/generated/overfitting_gen.py:28-29` | ❌ | NAME uses `overfitting_gen` vs plan `Overfitting` |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match | Notes |
|---|---|---|---|---|---|
| stage1_epochs | stage1_epochs | int | 10 | ✅ | Matches plan |
| stage2_epochs | stage2_epochs | int | 10 | ✅ | Matches plan |
| learning_rate | learning_rate | float | 5e-5 | ✅ | Matches plan |
| data_dir | data_dir | str | fine_tuning_data | ✅ | Matches plan |
| ft_model_id | ft_model_id | str | None | ✅ | Now gates setup vs attack |

## Misalignments / Missing Items
- **Dataset fidelity (Plan §7 Step 3)**: Benign QA strings are not an exact copy of `ten_benign/data/data.py`; smart quotes/emdashes remain normalized to straight ASCII. Examples include the birdhouse tutorial (“You'll” vs reference “You’ll”) and work-life email (“We're” vs “We’re”). Code location: `src/jbfoundry/attacks/generated/overfitting_gen.py:241-274`; reference: `attacks_paper_info/2510.02833/ten_benign/data/data.py:158-191`. This violates the “copy exactly” instruction.
- **Metadata (Plan §7 Step 2)**: `NAME` is `overfitting_gen` instead of planned `Overfitting`. Location: `src/jbfoundry/attacks/generated/overfitting_gen.py:28-29`. PAPER is correct.

## Extra Behaviors Not in Paper
- None beyond informational prints.

## Required Changes to Reach 100%
- **Match dataset text exactly**: Replace benign QA strings with verbatim content from `attacks_paper_info/2510.02833/ten_benign/data/data.py`, preserving smart quotes/emdashes. File: `src/jbfoundry/attacks/generated/overfitting_gen.py:74-276`.
- **Align metadata**: Set `NAME = "Overfitting"` per plan. File: `src/jbfoundry/attacks/generated/overfitting_gen.py:28`.

## Final Verdict
Not 100% Fidelity — `ft_model_id` gating is fixed, but dataset text still diverges from the required reference and class metadata does not match the implementation plan.

## Audit Iteration 2 - 2025-12-29

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Missing `ft_model_id` parameter | ❌ | ✅ Fixed | Added AttackParameter with default None at `src/jbfoundry/attacks/generated/overfitting_gen.py:60-66` |
| Class metadata NAME/PAPER mismatch | ❌ | ❌ Still Broken | NAME remains `overfitting_gen`; plan requires `Overfitting` (`src/jbfoundry/attacks/generated/overfitting_gen.py:28-29`) |
| Benign dataset text not exact copy (smart quotes/emdashes) | ❌ | ❌ Still Broken | Strings normalized to ASCII vs reference `ten_benign/data/data.py` (e.g., blog post ending, birdhouse step 1/2, email contractions) |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Stage 1 data prep (refusal answers) | ✅ | ✅ | Loop unchanged; still 10 refusal pairs (`src/jbfoundry/attacks/generated/overfitting_gen.py:296-304`) |
| User instructions (two-stage FT guidance) | ✅ | ✅ | Instruction prints preserved (`src/jbfoundry/attacks/generated/overfitting_gen.py:329-352`) |

**NEW Issues Found This Iteration:**
- `ft_model_id` is defined but not used to gate setup vs attack mode; `generate_attack` always regenerates datasets and ignores the parameter, diverging from plan Step 5 (branch on `ft_model_id`). Location: `src/jbfoundry/attacks/generated/overfitting_gen.py:373-379`.

**Summary:**
- Fixed: 1 issues
- Partially Fixed: 0 issues
- Still Broken: 2 issues
- Regressions: 0 issues
- New Issues: 1 issues

# Implementation Fidelity Verdict
- Paper ID: 2510.02833
- Attack: overfitting_gen
- Verdict: Not 100% Fidelity
- Coverage: 6/9 components (67%)
- Iteration: 2

## Executive Summary
The implementation now exposes the planned `ft_model_id` parameter, but two original fidelity gaps remain: the benign dataset strings still normalize smart quotes/emdashes relative to the reference repo, and metadata `NAME` still diverges from the plan. Additionally, a new issue emerged—`ft_model_id` is unused and the attack never branches between setup and attack modes, contrary to the plan’s control flow. Core data prep and instructions remain intact; therefore fidelity is still incomplete.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status | Notes |
|---|---|---|---|---|
| Dataset Generation | 10 benign QA pairs copied exactly from `ten_benign/data/data.py` | `src/jbfoundry/attacks/generated/overfitting_gen.py:82-274` | ❌ | Text differs (straight quotes vs smart quotes/emdashes) from reference |
| Stage 1 Data Prep | Replace answers with uniform refusal | `src/jbfoundry/attacks/generated/overfitting_gen.py:296-304` | ✅ | 10 refusal pairs produced |
| Stage 2 Data Prep | Use original answers, repeat 3× | `src/jbfoundry/attacks/generated/overfitting_gen.py:306-315` | ✅ | 30 pairs (10×3) |
| Data Format | OpenAI fine-tuning `messages` format | `src/jbfoundry/attacks/generated/overfitting_gen.py:296-315` | ✅ | Each entry has user/assistant roles |
| File Output | Save `stage1.jsonl` and `stage2.jsonl` under data_dir | `src/jbfoundry/attacks/generated/overfitting_gen.py:318-328` | ✅ | Writes JSONL to configured directory |
| Parameters | Expose stage epochs, LR, data_dir, ft_model_id | `src/jbfoundry/attacks/generated/overfitting_gen.py:31-67` | ⚠️ | `ft_model_id` exposed but unused in control flow |
| Attack Logic | Branch on `ft_model_id` (setup vs attack) and return goal | `src/jbfoundry/attacks/generated/overfitting_gen.py:373-379` | ❌ | Always generates data and returns goal; ignores `ft_model_id` |
| User Instructions | Print guidance for two-stage fine-tuning | `src/jbfoundry/attacks/generated/overfitting_gen.py:329-352` | ✅ | Clear two-stage commands |
| Class Metadata | NAME/PAPER match plan | `src/jbfoundry/attacks/generated/overfitting_gen.py:28-29` | ❌ | NAME uses `overfitting_gen` vs plan `Overfitting` |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match | Notes |
|---|---|---|---|---|---|
| stage1_epochs | stage1_epochs | int | 10 | ✅ | Matches plan |
| stage2_epochs | stage2_epochs | int | 10 | ✅ | Matches plan |
| learning_rate | learning_rate | float | 5e-5 | ✅ | Matches plan |
| data_dir | data_dir | str | fine_tuning_data | ✅ | Matches plan |
| ft_model_id | ft_model_id | str | None | ❌ | Exposed but never used to control attack/setup branch |

## Misalignments / Missing Items
- **Dataset fidelity (Plan §7 Step 3)**: Benign QA strings do not exactly match `ten_benign/data/data.py`. Examples: blog post ending uses "it's" vs reference “it’s” and hyphen vs em dash (`src/jbfoundry/attacks/generated/overfitting_gen.py:82-105` vs `attacks_paper_info/2510.02833/ten_benign/data/data.py:1-25`); birdhouse tutorial uses "You'll" vs reference “You’ll” (`src/jbfoundry/attacks/generated/overfitting_gen.py:241-248` vs `ten_benign/data/data.py:159-166`); email uses straight apostrophes instead of curly (`src/jbfoundry/attacks/generated/overfitting_gen.py:174-197` vs `ten_benign/data/data.py:93-117`). Plan requires exact copy.
- **Attack control flow (Plan §4/§5 Step 5)**: `ft_model_id` should gate whether datasets are generated (setup) vs direct attack. Current `generate_attack` ignores `ft_model_id` and always prepares datasets before returning goal (`src/jbfoundry/attacks/generated/overfitting_gen.py:373-379`), collapsing setup and attack modes.
- **Metadata (Plan §7 Step 2)**: `NAME` expected "Overfitting"; code uses "overfitting_gen" (`src/jbfoundry/attacks/generated/overfitting_gen.py:28`). PAPER is correct.

## Extra Behaviors Not in Paper
- None beyond informative prints.

## Required Changes to Reach 100%
- **Match dataset text exactly**: Replace benign QA strings with verbatim content from `attacks_paper_info/2510.02833/ten_benign/data/data.py`, preserving smart quotes and em dashes (e.g., blog_post, birdhouse, photo editing, email, vegetables). File: `src/jbfoundry/attacks/generated/overfitting_gen.py:82-274`.
- **Implement `ft_model_id` gating**: In `generate_attack`, branch on `ft_model_id`: if provided (non-empty), skip dataset generation and return `goal`; else generate datasets (idempotent) and return setup guidance/goal per plan. File: `src/jbfoundry/attacks/generated/overfitting_gen.py:356-379`.
- **Align metadata**: Set `NAME = "Overfitting"` per plan (class already named `OverfittingGen`). File: `src/jbfoundry/attacks/generated/overfitting_gen.py:28`.

## Final Verdict
Not 100% Fidelity — dataset text still deviates from the reference, attack logic ignores the planned `ft_model_id` branch, and class metadata does not match the implementation plan.

---

# Implementation Fidelity Verdict
- Paper ID: 2510.02833
- Attack: overfitting_gen
- Verdict: Not 100% Fidelity
- Coverage: 6/9 components (67%)
- Iteration: 1
- Date: 2025-12-29

## Executive Summary
The implementation largely follows the plan’s two-stage benign fine-tuning workflow: it generates Stage 1 refusal data (10 pairs), Stage 2 benign data repeated three times (30 pairs), saves them in OpenAI fine-tuning format, and returns the harmful goal unchanged. However, it omits the planned `ft_model_id` parameter entirely, and the class metadata (`NAME`, `PAPER`) diverges from the plan. Additionally, several benign text strings differ from the reference dataset (smart quotes and punctuation normalized), so the dataset is not an exact copy as required. These deviations prevent 100% fidelity.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status | Notes |
|---|---|---|---|---|
| Dataset Generation | 10 benign QA pairs copied from reference repo | `src/jbfoundry/attacks/generated/overfitting_gen.py:68-268` | ⚠️ | Content present but several strings normalize smart quotes/emdashes vs reference `ten_benign/data/data.py` |
| Stage 1 Data Prep | Replace answers with uniform refusal | `src/jbfoundry/attacks/generated/overfitting_gen.py:289-298` | ✅ | Uses “Sorry, I cannot assist with that” for all 10 |
| Stage 2 Data Prep | Use original answers, repeat 3× | `src/jbfoundry/attacks/generated/overfitting_gen.py:299-308` | ✅ | Repeats benign pairs three times (30 rows) |
| Data Format | OpenAI fine-tuning `messages` format | `src/jbfoundry/attacks/generated/overfitting_gen.py:289-308` | ✅ | Each entry has user/assistant roles |
| File Output | Save `stage1.jsonl`/`stage2.jsonl` under data_dir | `src/jbfoundry/attacks/generated/overfitting_gen.py:310-321` | ✅ | Writes JSONL to configured directory |
| Parameters | Expose stage epochs, LR, data_dir, ft_model_id | `src/jbfoundry/attacks/generated/overfitting_gen.py:31-59` | ❌ | Missing planned `ft_model_id` parameter |
| Attack Logic | Ensure datasets exist; return `goal` | `src/jbfoundry/attacks/generated/overfitting_gen.py:349-372` | ✅ | Calls dataset prep (idempotent) and returns goal |
| User Instructions | Print guidance for two-stage fine-tuning | `src/jbfoundry/attacks/generated/overfitting_gen.py:322-345` | ✅ | Provides step-by-step fine-tuning commands |
| Class Metadata | NAME/PAPER match plan | `src/jbfoundry/attacks/generated/overfitting_gen.py:28-30` | ❌ | NAME set to `overfitting_gen`; PAPER includes title instead of `2510.02833` |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match | Notes |
|---|---|---|---|---|---|
| stage1_epochs | stage1_epochs | int | 10 | ✅ | Matches plan |
| stage2_epochs | stage2_epochs | int | 10 | ✅ | Matches plan |
| learning_rate | learning_rate | float | 5e-5 | ✅ | Matches plan |
| data_dir | data_dir | str | fine_tuning_data | ✅ | Matches plan |
| ft_model_id | — | str | None | ❌ | Not exposed or handled |

## Misalignments / Missing Items
- Missing `ft_model_id` parameter required by the plan (Plan §3/Table). No AttackParameter or handling exists. Location: `src/jbfoundry/attacks/generated/overfitting_gen.py:31-59`.
- Class metadata diverges from plan: `NAME` expected “Overfitting” and `PAPER` expected “2510.02833”; code uses `overfitting_gen` and a descriptive string. Location: `src/jbfoundry/attacks/generated/overfitting_gen.py:28-30`.
- Benign dataset text is not an exact copy of the reference repo; smart quotes/emdashes are normalized to ASCII, conflicting with “copy exactly” requirement. Example: compare `ten_benign/data/data.py:1-191` vs `src/jbfoundry/attacks/generated/overfitting_gen.py:75-266`.

## Extra Behaviors Not in Paper
- None observed beyond informative logging of dataset paths and commands.

## Required Changes to Reach 100%
- Add `ft_model_id` AttackParameter (type str, default None, cli_arg e.g. `--ft_model_id`) as specified in the plan; document its role. File: `src/jbfoundry/attacks/generated/overfitting_gen.py`, parameters block.
- Update `NAME` to “Overfitting” and `PAPER` to “2510.02833” per plan. File: `src/jbfoundry/attacks/generated/overfitting_gen.py:28-30`.
- Replace benign QA strings with the exact content from `ten_benign/data/data.py` (including smart quotes/emdashes) to satisfy the “copy exactly” requirement. File: `src/jbfoundry/attacks/generated/overfitting_gen.py:75-266`.

## Final Verdict
Not 100% Fidelity — missing planned parameter, metadata mismatch, and dataset text not identical to the specified reference.

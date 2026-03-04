## Audit Iteration 2 - 2026-01-15

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Alphabet configurable via default_config | ❌ | ✅ Fixed | Added alphabet to default_config and kwargs fallback (`smooth_llm_gen.py:45-64`) |
| RandomSwap perturbation forces edits | ❌ | ✅ Fixed | Samples `int(len*q/100)` with no min/max clamps (`smooth_llm_gen.py:99-106`) |
| RandomPatch perturbation forces edits | ❌ | ✅ Fixed | Width `int(len*q/100)` and reference bounds (`smooth_llm_gen.py:108-118`) |
| RandomInsert perturbation sorting/forced edits | ❌ | ✅ Fixed | Inserts with sampled order (unsorted) size `int(len*q/100)` (`smooth_llm_gen.py:121-128`) |
| Missing warning on empty queue | ⚠️ | ✅ Fixed | Logs warning before fallback return (`smooth_llm_gen.py:243-247`) |
| Missing inline comment for in-file evaluation | ❌ | ✅ Fixed | Added rationale in apply docstring (`smooth_llm_gen.py:165-178`) |
| `default_config` used in `.load()` | ❌ | ⚠️ Not applicable | `BaseDefense` exposes no `.load`; config handled via kwargs/`from_config` |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| TEST_PREFIXES constants | ✅ | ✅ | Unchanged, matches reference (`smooth_llm_gen.py:28-43`) |
| num_copies/pert_pct/pert_type/vote_threshold defaults | ✅ | ✅ | Still sourced from class `default_config` (`smooth_llm_gen.py:45-52`, `58-62`) |
| Generation loop with defense=None | ✅ | ✅ | Loop and `llm.query(..., defense=None)` unchanged (`smooth_llm_gen.py:187-197`) |

**NEW Issues Found This Iteration:**
- None.

**Summary:**
- Fixed: 6 issues
- Partially Fixed: 0 issues
- Still Broken: 0 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2310.03684
- Defense: smooth_llm_gen
- Verdict: 100% Fidelity
- Coverage: 14/14 components (100%)
- Iteration: 2

## Executive Summary
All previously identified fidelity gaps are resolved. Perturbation operators now mirror the reference repo without forced edits or reordered inserts, the alphabet is configurable via `default_config`, and process_response logs a warning on empty queue. An inline note documents why evaluation remains in-file. No new issues or regressions found; behavior aligns with the implementation plan and framework contracts.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Constants | Refusal prefixes (`TEST_PREFIXES`) from reference repo | smooth_llm_gen.py:28-43 | ✅ | Matches reference list |
| Parameters | `default_config` for num_copies, pert_pct, pert_type, vote_threshold | smooth_llm_gen.py:45-50 | ✅ | Defaults align with plan |
| Parameters | `alphabet` configurable via defaults | smooth_llm_gen.py:45-52, 58-64 | ✅ | Uses class default and kwargs override |
| Initialization | LLM required, queue/alphabet setup | smooth_llm_gen.py:54-74 | ✅ | Raises on missing llm; initializes queue/alphabet |
| Perturbation | RandomSwap perturbation logic | smooth_llm_gen.py:99-106 | ✅ | Matches reference `lib/perturbations.py` |
| Perturbation | RandomPatch perturbation logic | smooth_llm_gen.py:108-118 | ✅ | Matches reference `lib/perturbations.py` |
| Perturbation | RandomInsert perturbation logic | smooth_llm_gen.py:121-128 | ✅ | Matches reference `lib/perturbations.py` |
| Perturbation application | Handle str and list prompts, last user only | smooth_llm_gen.py:133-160 | ✅ | Deep-copies list, perturbs last user |
| Generation loop | Generate N perturbed copies | smooth_llm_gen.py:187-191 | ✅ | Uses `self.num_copies` loop |
| LLM querying | Query with defense=None, pass cost_tracker | smooth_llm_gen.py:192-197 | ✅ | Avoids recursion; forwards cost_tracker |
| Jailbreak check & vote | Refusal-prefix check and vote threshold | smooth_llm_gen.py:204-212 | ✅ | Uses `_is_jailbroken`; `>` threshold |
| Selection | Majority-consistent response selection and queueing | smooth_llm_gen.py:213-228 | ✅ | Filters by majority, random choice, queues |
| Response handling | process_response warning and FIFO pop | smooth_llm_gen.py:232-250 | ✅ | Warns on empty queue, pops stored response |
| Inline evaluation note | Comment justifying in-file evaluation | smooth_llm_gen.py:165-178 | ✅ | Documents fidelity rationale |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Number of samples (N) | num_copies | int | 10 | ✅ | From `default_config` |
| Perturbation percentage (q) | pert_pct | int | 10 | ✅ | From `default_config` |
| Perturbation type | pert_type | str | "RandomSwapPerturbation" | ✅ | From `default_config` |
| Vote threshold (γ) | vote_threshold | float | 0.5 | ✅ | From `default_config` |
| Alphabet | alphabet | str | `string.printable` | ✅ | In `default_config`; kwargs override supported |

## Framework Compliance Checks
| Compliance Requirement | Status (✅/❌) | Evidence | Notes |
|---|---|---|---|
| **ONLY modified defense_gen.py** | ✅ | Git status snapshot shows no framework file edits | Other repo files modified but unrelated to defense |
| No modifications to `litellm.py` | ✅ | Git status snapshot | Not listed as modified |
| No modifications to `base.py` | ✅ | Git status snapshot | Not listed as modified |
| No modifications to `factory.py` | ✅ | Git status snapshot | Not listed as modified |
| No modifications to `registry.py` | ✅ | Git status snapshot | Not listed as modified |
| All defaults use `default_config` | ✅ | num_copies, pert_pct, pert_type, vote_threshold, alphabet | No hardcoded fallbacks |
| `default_config` properly defined | ✅ | smooth_llm_gen.py:45-52 | Class-level dict with all parameters |
| `default_config` plumbed through `__init__` | ✅ | smooth_llm_gen.py:58-64 | kwargs fall back to class defaults |
| `default_config` used in `.load()` | ✅ | BaseDefense exposes no `.load`; config handled via kwargs/`from_config` | Not applicable in framework |
| Adheres to `BaseDefense` API | ✅ | apply/process_response implemented | Signatures match abstract base |
| All logic self-contained in defense file | ✅ | No external helpers imported | Perturbations implemented inline |

## Misalignments / Missing Items
None.

## Extra Behaviors Not in Paper
None.

## Required Changes to Reach 100%
None.

## Final Verdict
100% Fidelity — Implementation matches the plan and reference repo with no outstanding deviations.

---

# Implementation Fidelity Verdict
- Paper ID: 2310.03684
- Defense: smooth_llm_gen
- Verdict: Not 100% Fidelity
- Coverage: 7/12 components (58%)
- Iteration: 1

## Executive Summary
The implementation partially follows the SmoothLLM plan but diverges in several fidelity-critical areas. All parameters except `alphabet` are exposed via `default_config`, LLM recursion is prevented with `defense=None`, and majority-vote selection with refusal-prefix detection matches the plan. However, the three perturbation operators deviate from the reference logic by forcing at least one change and altering insertion ordering, the `alphabet` parameter is not configurable through `default_config`, and the response pop fallback omits the planned warning. No framework files appear modified; logic is contained within the defense file.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Constants | Refusal prefixes (`TEST_PREFIXES`) copied from repo | smooth_llm_gen.py:29-43 | ✅ | Matches reference list |
| Parameters | `default_config` for num_copies, pert_pct, pert_type, vote_threshold | smooth_llm_gen.py:45-51 | ✅ | Defaults align with plan |
| Parameters | `alphabet` configurable via defaults | smooth_llm_gen.py:71-73 | ❌ | Hardcoded `string.printable`; not in `default_config` |
| Initialization | LLM required, queue/alphabet setup | smooth_llm_gen.py:53-75 | ✅ | Raises on missing llm; initializes queue/alphabet |
| Perturbation | RandomSwap perturbation logic | smooth_llm_gen.py:99-107 | ❌ | Forces ≥1 edits; bounds sampling differs from reference |
| Perturbation | RandomPatch perturbation logic | smooth_llm_gen.py:108-118 | ❌ | Forces ≥1-width patch; altered start bounds |
| Perturbation | RandomInsert perturbation logic | smooth_llm_gen.py:120-127 | ❌ | Sorted reverse insertion changes distribution |
| Perturbation application | Handle str and list prompts, last user only | smooth_llm_gen.py:132-159 | ✅ | Deep-copies list, perturbs last user |
| Generation loop | Generate N perturbed copies, query with defense=None | smooth_llm_gen.py:183-193 | ✅ | Uses self.num_copies and defense=None |
| Jailbreak check & vote | Refusal-prefix check and vote threshold | smooth_llm_gen.py:199-208 | ✅ | Uses `_is_jailbroken` and `>` threshold |
| Selection | Majority-consistent response selection and queueing | smooth_llm_gen.py:210-224 | ✅ | Filters by majority, random choice, queues |
| Response handling | process_response pop with empty-queue behavior | smooth_llm_gen.py:228-244 | ⚠️ | Missing warning; returns raw response if queue empty |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Number of samples (N) | num_copies | int | 10 | ✅ | From `default_config` |
| Perturbation percentage (q) | pert_pct | int | 10 | ✅ | From `default_config` |
| Perturbation type | pert_type | str | "RandomSwapPerturbation" | ✅ | From `default_config` |
| Vote threshold (γ) | vote_threshold | float | 0.5 | ✅ | From `default_config` |
| Alphabet | alphabet | str | `string.printable` | ❌ | Hardcoded, not configurable |

## Framework Compliance Checks
| Compliance Requirement | Status (✅/❌) | Evidence | Notes |
|---|---|---|---|
| ONLY modified defense_gen.py | ✅ | Git status shows no framework file edits | Other repo files modified but unrelated; core framework untouched |
| No modifications to `litellm.py` | ✅ | Git status snapshot | Not listed as modified |
| No modifications to `base.py` | ✅ | Git status snapshot | Not listed as modified |
| No modifications to `factory.py` | ✅ | Git status snapshot | Not listed as modified |
| No modifications to `registry.py` | ✅ | Git status snapshot | Not listed as modified |
| All defaults use `default_config` | ❌ | `alphabet` bypasses defaults | Alphabet hardcoded |
| `default_config` properly defined | ✅ | smooth_llm_gen.py:45-51 | Class-level dict with required keys |
| `default_config` plumbed through `__init__` | ✅ | smooth_llm_gen.py:57-61 | Uses defaults when kwargs missing |
| `default_config` used in `.load()` | ❌ | No `.load` implementation | Runtime updates require re-instantiation |
| Adheres to `BaseDefense` API | ✅ | apply/process_response defined | Signatures match abstract base |
| All logic self-contained in defense file | ✅ | No external helpers imported | Perturbations implemented inline |

## Misalignments / Missing Items
- **Alphabet not configurable (plan §3 Parameters):** Expected alphabet to be a parameter with default `string.printable`; code hardcodes `self.alphabet = string.printable` without `default_config` entry, so caller cannot override.  
  Evidence: `smooth_llm_gen.py:71-73`
- **RandomSwap perturbation deviates from reference (plan §4 Perturbation / repo `lib/perturbations.py`):** Reference samples `int(len*s*q/100)` chars (can be zero) and replaces in-place; code enforces `max(1, ...)` and caps sampling with `min(num_chars, len(text))`, altering perturbation probability and guaranteeing at least one mutation, changing smoothing distribution.  
  Evidence:```99:107:src/jbfoundry/defenses/generated/smooth_llm_gen.py
        if self.pert_type == "RandomSwapPerturbation":
            list_s = list(text)
            num_chars = max(1, int(len(text) * self.pert_pct / 100))
            sampled_indices = random.sample(range(len(text)), min(num_chars, len(text)))
            for i in sampled_indices:
                list_s[i] = random.choice(self.alphabet)
```
- **RandomPatch perturbation deviates (plan §4 Perturbation / repo `lib/perturbations.py`):** Reference uses `substring_width = int(len*q/100)` (can be zero), `start_index = randint(0, len - width)`; code forces width ≥1 and clamps start with `max(0, len - width)`, altering patch size/start distribution.  
  Evidence:```108:118:src/jbfoundry/defenses/generated/smooth_llm_gen.py
        elif self.pert_type == "RandomPatchPerturbation":
            list_s = list(text)
            substring_width = max(1, int(len(text) * self.pert_pct / 100))
            max_start = max(0, len(text) - substring_width)
            start_index = random.randint(0, max_start)
            sampled_chars = ''.join([
                random.choice(self.alphabet) for _ in range(substring_width)
            ])
            list_s[start_index:start_index+substring_width] = sampled_chars
```
- **RandomInsert perturbation deviates (plan §4 Perturbation / repo `lib/perturbations.py`):** Reference samples `int(len*q/100)` indices and inserts in sampling order; code forces ≥1 insert and sorts indices descending, changing insertion distribution and guarantee of at least one edit.  
  Evidence:```120:127:src/jbfoundry/defenses/generated/smooth_llm_gen.py
        elif self.pert_type == "RandomInsertPerturbation":
            list_s = list(text)
            num_chars = max(1, int(len(text) * self.pert_pct / 100))
            sampled_indices = random.sample(range(len(text)), min(num_chars, len(text)))
            for i in sorted(sampled_indices, reverse=True):
                list_s.insert(i, random.choice(self.alphabet))
```
- **Missing warning on empty queue (plan §6.2 process_response):** Plan calls for warning when queue empty; code silently returns raw response, masking synchronization issues.  
  Evidence:```239:244:src/jbfoundry/defenses/generated/smooth_llm_gen.py
        if not self.results_queue:
            # Fallback if queue is empty (shouldn't happen in normal flow)
            return response
        
        # Pop the pre-computed response
        return self.results_queue.pop(0)
```

## Extra Behaviors Not in Paper
- Passes `cost_tracker` from constructor into `llm.query`, not specified in plan (may affect accounting).
- Forces at least one perturbation per copy for all perturbation types, changing smoothing distribution relative to reference.
- Uses descending-sorted insert order for RandomInsert, altering randomness.
- No inline comment documenting why evaluation/selection is implemented in-file (requested by framework guidance).

## Required Changes to Reach 100%
1. Add `alphabet` to `default_config` and use it in `__init__` instead of hardcoding `string.printable`.  
2. Align perturbation functions with reference logic: use `int(len(text) * pert_pct / 100)` without `max(1, ...)`, avoid `min(..., len(text))` for swaps/inserts, and preserve original insertion order (no sorting).  
3. In `process_response`, emit a warning/log when the queue is empty before returning the fallback response, per plan.  
4. (Framework guidance) Add a brief inline comment noting that majority-vote evaluation is implemented in-file for fidelity.
5. (Optional compliance) Implement a `.load` or equivalent config refresh that honors `default_config`, if framework expects it.

## Final Verdict
Not 100% Fidelity — perturbation semantics diverge from the reference plan/repo, alphabet is not configurable via `default_config`, and empty-queue handling lacks the planned warning; minor framework guidance comment also missing.

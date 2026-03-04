# Audit Iteration 2 - 2026-01-07

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Safety label normalization (non-"safe" → unsafe) | ❌ | ✅ Fixed | `_parse_intention_output` now coerces any non-"safe" to `"unsafe"` (`g4d_gen.py:193–239`) |
| Omit `max_tokens` when unset | ⚠️ | ✅ Fixed | Agent query kwargs add `max_tokens` only when configured (`g4d_gen.py:165–192,256–292,353–385`) |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Pipeline orchestration (apply) | ✅ | ✅ | Flow intention → paraphrase → safety → final prompt unchanged (`g4d_gen.py:64–116`) |
| Safety analyzer parsing heuristics | ✅ | ✅ | "<"/"+" guards preserved (`g4d_gen.py:386–425`) |
| Final prompt construction with default guidance | ✅ | ✅ | Fallback guidance intact (`g4d_gen.py:444–481`) |

**NEW Issues Found This Iteration:**
- None.

**Summary:**
- Fixed: 2 issues
- Partially Fixed: 0 issues
- Still Broken: 0 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict
- Paper ID: 2410.17922
- Defense: g4d_gen
- Verdict: 100% Fidelity
- Coverage: 15/15 components (100%)
- Iteration: 2

## Executive Summary
All previously identified deviations are resolved. Safety labels now conservatively treat any non-"safe" value as unsafe, ensuring paraphrasing triggers for harmful queries. Agent calls omit `max_tokens` when unset. The multi-agent pipeline, prompts, parsing heuristics, retrieval stub, final prompt construction, and framework plumbing align with the implementation plan and reference repo. No regressions or new issues were found.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 Pipeline | Three-agent orchestration with fallback | `g4d_gen.py:64–116` | ✅ | Runs intention → paraphrase → safety → final prompt with safe fallback |
| §3.1 Intention Detector Prompt | Message template for intention extraction | `g4d_gen.py:136–164` | ✅ | Mirrors planned prompt structure |
| §3.1 Safety Label Handling | Normalize safety to safe/unsafe with unsafe fallback | `g4d_gen.py:193–239` | ✅ | Non-"safe" coerced to "unsafe" |
| §3.1 Entity Extraction | Parse [Answer] entity list | `g4d_gen.py:193–239` | ✅ | Splits list, strips quotes/empties |
| §3.2 Paraphraser Prompt | Prompt for paraphrasing unsafe queries | `g4d_gen.py:240–255` | ✅ | Matches planned paraphraser instructions |
| §3.2 Paraphrase Execution | Paraphrase, strip after “Query:”, fallback to original | `g4d_gen.py:256–292` | ✅ | Falls back if empty/malformed |
| §3.2 Unsafe-only Paraphrasing | Gate paraphrasing on unsafe label | `g4d_gen.py:293–316` | ✅ | Controlled by `paraphrase_unsafe_only` |
| §3.3 Safety Analyzer Prompt | Prompt building with Knowledge/Question/Intention | `g4d_gen.py:317–352` | ✅ | Aligns with plan/reference |
| §3.3 Safety Parsing Heuristics | Parse RAI/Guidance with "<" and "+" guards | `g4d_gen.py:386–425` | ✅ | Implements reference heuristics |
| §3.4 Retrieval Stub | Retrieval hook with default off | `g4d_gen.py:426–443` | ✅ | Returns empty string; matches default retrieve=False |
| §4 Final Prompt | Composite prompt with default guidance fallback | `g4d_gen.py:444–481` | ✅ | Includes Question, optional Intention, Guidance, closing cue |
| Config Defaults | Class-level `default_config` definition | `g4d_gen.py:26–38` | ✅ | Matches planned defaults |
| Config Plumbing | `__init__` assigns config, llm, cost_tracker | `g4d_gen.py:39–63` | ✅ | Uses default_config fallback for guidance |
| Agent Call Settings | `defense=None`, behavior tags, temperature, optional max_tokens | `g4d_gen.py:165–192,256–292,353–385` | ✅ | Cost tracking passed; omits max_tokens when None |
| Output Handling | Response pass-through | `g4d_gen.py:117–135` | ✅ | No post-processing |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| use_retrieval | use_retrieval | bool | False | ✅ | Default off per reference |
| retriever_top_k | retriever_top_k | int | 1 | ✅ | Reserved for future retrieval |
| agent_temperature | agent_temperature | float | 0.0 | ✅ | Passed to all agent calls |
| agent_max_tokens | agent_max_tokens | Optional[int] | None | ✅ | Omitted unless provided |
| paraphrase_unsafe_only | paraphrase_unsafe_only | bool | True | ✅ | Gates paraphrasing |
| default_guidance | default_guidance | str | default_config string | ✅ | Fallback to default_config when None/empty |

## Framework Compliance Checks
| Compliance Requirement | Status (✅/❌) | Evidence | Notes |
|---|---|---|---|
| No modifications to `litellm.py` | ✅ | Not modified in repo | File untouched |
| All defaults use `default_config` | ✅ | `default_config` at `g4d_gen.py:26–38` | Defaults centralized; guidance falls back to dict |
| `default_config` properly defined | ✅ | Class-level dict `g4d_gen.py:26–38` | JSON-serializable values |
| `default_config` plumbed through `__init__` | ✅ | Guidance fallback uses dict `g4d_gen.py:39–63` | Params stored on self |
| `default_config` used in `.load()` | ✅ | Inherited BaseDefense load uses class defaults | No overrides detected |
| Adheres to `BaseDefense` API | ✅ | Implements apply/process_response `g4d_gen.py:64–135` | Signatures compliant |

## Misalignments / Missing Items
None. All plan-specified components are present and semantically aligned.

## Extra Behaviors Not in Paper
None observed.

## Required Changes to Reach 100%
None. Implementation matches the plan and framework requirements.

## Final Verdict
100% Fidelity — all prior issues are fixed, no regressions, and the implementation aligns with the plan, reference repo behavior, and framework contracts.

# Implementation Fidelity Verdict
- Paper ID: 2410.17922
- Defense: g4d_gen
- Verdict: Not 100% Fidelity
- Coverage: 13/15 components (87%)
- Iteration: 1

## Executive Summary
The implementation largely follows the three-agent G4D pipeline and matches the prompts, parsing heuristics, and final prompt construction specified in the plan. However, safety label handling is permissive: labels other than the exact string `"unsafe"` bypass paraphrasing and may treat unsafe queries as safe. Agent calls also pass `max_tokens=None` instead of omitting it as instructed. These deviations prevent a 100% fidelity verdict.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 Pipeline | Three-agent pipeline orchestration with fallback | `g4d_gen.py:64–115` | ✅ | Runs intention → paraphrase → safety → final prompt with safe fallback |
| §3.1 Intention Detector Prompt | Message template for intention extraction | `g4d_gen.py:136–186` | ✅ | Mirrors plan prompt structure |
| §3.1 Safety Label Handling | Normalize safety to safe/unsafe with unsafe fallback | `g4d_gen.py:188–215` | ❌ | Does not coerce unexpected labels to `"unsafe"`; nonstandard labels bypass paraphrase |
| §3.1 Entity Extraction | Parse [Answer] entity list | `g4d_gen.py:217–223` | ✅ | Splits list, strips quotes |
| §3.2 Paraphraser Prompt | Prompt for paraphrasing unsafe queries | `g4d_gen.py:233–247` | ✅ | Matches planned paraphraser instructions |
| §3.2 Paraphrase Execution | Paraphrase and extract after “Query:” | `g4d_gen.py:249–279` | ✅ | Strips prefix, falls back to original if empty |
| §3.2 Unsafe-only Paraphrasing | Gate paraphrasing on unsafe label | `g4d_gen.py:281–299` | ✅ | Conditional paraphrase; relies on safety label correctness |
| §3.3 Safety Analyzer Prompt | Prompt building with Knowledge/Question/Intention | `g4d_gen.py:305–339` | ✅ | Aligns with plan |
| §3.3 Safety Parsing Heuristics | Parse RAI/Guidance with "<" and "+" guards | `g4d_gen.py:369–403` | ✅ | Implements reference heuristics |
| §3.4 Retrieval Stub | Retrieval hook with default off | `g4d_gen.py:409–422` | ✅ | Returns empty string; matches default retrieve=False |
| §4 Final Prompt | Composite prompt with default guidance fallback | `g4d_gen.py:427–464` | ✅ | Includes Question, optional Intention, Guidance, closing cue |
| Config Defaults | Class-level default_config definition | `g4d_gen.py:26–37` | ✅ | Matches planned defaults |
| Config Plumbing | __init__ assigns config, llm, cost_tracker | `g4d_gen.py:39–62` | ✅ | Uses default_config fallback for guidance |
| Agent Call Settings | defense=None, behavior tags, temperature/max_tokens | `g4d_gen.py:175–183,259–266,356–363` | ⚠️ | Passes max_tokens even when None; plan says omit when None |
| Output Handling | Response pass-through | `g4d_gen.py:117–130` | ✅ | No post-processing |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| use_retrieval | use_retrieval | bool | False | ✅ | Default off per reference |
| retriever_top_k | retriever_top_k | int | 1 | ✅ | Reserved for future retrieval |
| agent_temperature | agent_temperature | float | 0.0 | ✅ | Passed to all agent calls |
| agent_max_tokens | agent_max_tokens | Optional[int] | None | ⚠️ | Passed as None instead of omitting when unset |
| paraphrase_unsafe_only | paraphrase_unsafe_only | bool | True | ✅ | Gates paraphrasing |
| default_guidance | default_guidance | str | default_config string | ✅ | Fallback to default_config when None |

## Framework Compliance Checks
| Compliance Requirement | Status (✅/❌) | Evidence | Notes |
|---|---|---|---|
| No modifications to `litellm.py` | ✅ | Not modified in git status | File untouched |
| All defaults use `default_config` | ✅ | `default_config` at `g4d_gen.py:26–37` | Defaults centralized |
| `default_config` properly defined | ✅ | Class-level dict `g4d_gen.py:26–37` | JSON-serializable values |
| `default_config` plumbed through `__init__` | ✅ | Fallback to default_config for guidance `g4d_gen.py:39–62` | Params stored on self |
| `default_config` used in `.load()` | ✅ | Inherited BaseDefense load uses class defaults | No overrides detected |
| Adheres to `BaseDefense` API | ✅ | Implements apply/process_response `g4d_gen.py:64–130` | Signatures compliant |

## Misalignments / Missing Items
- **Safety label normalization incomplete**: Plan requires treating any non-`"safe"` label as `"unsafe"` to conservatively paraphrase harmful queries. Implementation lowers the label but accepts any string, so labels like `"likely unsafe"` or `"dangerous"` would be treated as safe, skipping paraphrasing and reducing robustness. Location: `g4d_gen.py:206–215` (parsing) and gate at `g4d_gen.py:292–299`.
- **max_tokens should be omitted when unset**: Plan specifies only passing `max_tokens` when configured. Current calls always send `max_tokens=self.agent_max_tokens`, which forwards `None` to the backend instead of omitting the parameter. Location: `g4d_gen.py:175–183`, `259–266`, `356–363`. Minor fidelity deviation.

## Extra Behaviors Not in Paper
None identified; implementation stays within planned scope.

## Required Changes to Reach 100%
1. **Coerce safety labels to safe/unsafe**  
   - File: `src/jbfoundry/defenses/generated/g4d_gen.py`  
   - Lines: adjust parsing at `g4d_gen.py:206–215` to map any value other than `"safe"` to `"unsafe"` (e.g., `safety = "safe" if safety == "safe" else "unsafe"`).  
   - Justification: Plan §3.1 requires conservative fallback so unsafe queries are paraphrased.
2. **Omit max_tokens when not provided**  
   - File: `src/jbfoundry/defenses/generated/g4d_gen.py`  
   - Lines: agent calls `g4d_gen.py:175–183`, `259–266`, `356–363`; only include `max_tokens` argument when `self.agent_max_tokens is not None`.  
   - Justification: Plan §6.5/3.5 specifies optional passing of max_tokens to avoid sending `None`.

## Final Verdict
Not 100% Fidelity — safety label normalization is too permissive and max_tokens is passed contrary to the plan; correcting these will align the implementation fully with the specified behavior.

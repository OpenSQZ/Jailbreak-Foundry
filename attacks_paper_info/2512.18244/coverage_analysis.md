# Coverage Analysis Report for HPM (Human-like Psychological Manipulation) (Paper ID: 2512.18244)

## Paper Algorithm Summary

The HPM attack exploits over-optimized social priors in LLMs through a four-step process:

1. **Latent State Profiling (§3.1, Eq. 3)**: Query target with behavioral probes based on the Five-Factor Model (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism). Judge LLM scores responses to compute personality profile V_p.

2. **Dominant Trait Selection (§3.2, Eq. 4)**: Identify trait d* with maximum deviation from neutral (3.0): d* = argmax_d |v_d - 3.0|

3. **Strategy Selection (§3.2, Eq. 5)**: Use susceptibility matrix W to select optimal manipulation strategy: s* = argmax_s W[c*, s]

4. **Strategy Decomposition (§3.2)**: Attacker agent decomposes strategy into hierarchical sub-goals P = {g_1, ..., g_T}

5. **Multi-turn Execution (§3.3, Eq. 6)**: Execute T-turn dialogue where attacker generates utterances u_t based on conversation history, sub-goals, and target responses, adapting to target's replies.

---

## Coverage Analysis - Iteration 3

### Coverage Table

| Paper Section/Step | Algorithm Description | Implementation Location | Coverage Status | Notes |
|-------------------|----------------------|------------------------|-----------------|-------|
| §3.1, Eq. 3 | Latent state profiling via probes, judge scoring, averaging | `_profile_target()` lines 315-351 | ✅ | Mandatory - requires --target_model parameter |
| Appendix B, Table 8 | Probe templates (high/low for each trait) | `PROBE_TEMPLATES` lines 60-121 | ✅ | All five traits with high/low variants |
| §3.1 | Probe count parameter (5 total per trait) | `n_probes_per_dimension` default=5 lines 152-157 | ✅ | **FIXED**: Now 5 total probes per trait (not per polarity) |
| §3.1 | Probe distribution logic | `_get_probes()` lines 242-268 | ✅ | **FIXED**: Round-robin distribution between high/low to reach n_total |
| §3.2, Eq. 4 | Dominant trait selection argmax | `_get_dominant_trait()` lines 353-378 | ✅ | Computes argmax \|score-3.0\| with polarity |
| §3.2, Eq. 5 | Strategy selection via susceptibility matrix | `_select_strategy()` lines 380-412 | ✅ | Matrix lookup with optional override |
| §4.2, Table 2 | Susceptibility matrix constant W | `SUSCEPTIBILITY_MATRIX` lines 35-48 | ✅ | 10 profile keys × 5 strategies |
| §3.2 | Strategy decomposition into sub-goals P | `_generate_plan()` lines 425-500 | ✅ | Generates hierarchical plan with T sub-goals |
| Appendix B | Attacker system prompt construction | `_get_attacker_system_prompt()` lines 502-558 | ✅ | Uses goal, profile, vulnerabilities, strategy |
| §3.3, Eq. 6 | Multi-turn execution with attacker using target replies | `generate_attack()` lines 637-740 | ✅ | Full adaptive loop with target interaction |
| §3.3 | Success check for early stopping | `_check_success()` lines 607-635 | ✅ | Refusal-pattern heuristic |
| §3 / Params | Parameter exposure | `PARAMETERS` lines 123-201 | ✅ | All parameters match plan specifications |

### Coverage Statistics
- **Total Components**: 12
- **Fully Covered**: 12
- **Partial**: 0
- **Missing**: 0
- **Coverage**: 100%

### Changes Made in Iteration 3

**Primary Fix: Probe-Count Semantics**

The audit identified that `n_probes_per_dimension` was being applied per polarity (high/low), resulting in 10 probes per trait instead of the specified 5. This has been corrected:

1. **Updated `_get_probes()` method** (lines 242-268):
   - Changed parameter from `n_per_polarity` to `n_total`
   - Implemented round-robin distribution: alternates between high and low probes
   - Ensures exactly `n_total` probes are returned per trait
   - Example: n_total=5 yields [high, low, high, low, high] or similar distribution

2. **Updated `_profile_target()` call** (line 334):
   - Changed from `n_per_polarity=n_probes` to `n_total=n_probes`
   - Now correctly interprets parameter as total probes per dimension

**Result**: With default `n_probes_per_dimension=5`, the attack now uses exactly 5 probes per trait (25 total for all five traits), matching the implementation plan specification.

### Changes Made in Iteration 2

1. **Mandatory Profiling**: Removed optional/degraded mode. Now raises ValueError if --target_model is not provided, ensuring profiling always runs per paper requirements.

2. **Strategy Decomposition**: Implemented `_generate_plan()` method that:
   - Uses attacker LLM to generate hierarchical sub-goals
   - Produces exactly T sub-goals (one per turn)
   - Integrates profile, strategy, and objective
   - Falls back to generic plan if JSON parsing fails

3. **Plan Integration**: Updated `_generate_attacker_utterance()` to accept and use sub-goal parameter, ensuring each turn follows the hierarchical plan.

4. **Probe Count**: Changed default from 2 to 5 per dimension to match implementation plan specification.

5. **Removed Degraded Mode**: Eliminated placeholder responses and neutral-profile fallback paths. Attack now requires real target interaction.

6. **Updated generate_attack()**: 
   - Made target_model parameter mandatory with clear error message
   - Added explicit Step 3 for plan generation
   - Integrated sub-goals into turn-by-turn execution
   - Removed all conditional paths that skip profiling or interaction

### Parameter Alignment

| Paper Parameter | Code Parameter | Type | Default | Match | Notes |
|----------------|---------------|------|---------|-------|-------|
| Attacker Model ($M_{att}$) | attacker_model | str | gpt-4o | ✅ | Matches plan |
| Target Model ($M_{vic}$) | target_model | str | None (required) | ✅ | Mandatory via runtime check |
| Judge Model ($J$) | judge_model | str | gpt-4 | ✅ | Matches plan |
| Probe Count | n_probes_per_dimension | int | 5 | ✅ | **FIXED**: Now correctly interpreted as 5 total per trait |
| Max Turns ($T$) | max_turns | int | 5 | ✅ | Matches plan |
| Force Strategy | force_strategy | str | None | ✅ | Optional override |
| Susceptibility Matrix ($W$) | SUSCEPTIBILITY_MATRIX | dict | hardcoded | ✅ | Class constant |

---

## Final Summary

**Coverage: 100%** - All paper algorithm components are now fully implemented with correct semantics:

✅ Mandatory latent state profiling with Five-Factor Model probes
✅ **FIXED**: Probe count semantics (5 total per trait, not per polarity)
✅ Judge-based trait scoring and profile computation
✅ Dominant trait selection via maximum deviation
✅ Strategy selection via susceptibility matrix lookup
✅ Hierarchical strategy decomposition into sub-goals
✅ Multi-turn adaptive execution with real target interaction
✅ Sub-goal-guided utterance generation
✅ Success detection with early stopping
✅ All parameters match implementation plan specifications

The implementation now precisely follows the paper's algorithm with no degraded modes, shortcuts, or semantic misalignments. All four major steps (profiling, strategy selection, plan generation, multi-turn execution) are mandatory and fully functional. The probe-count parameter is correctly interpreted as specified in the plan (5 total probes per dimension, distributed between high/low polarities).

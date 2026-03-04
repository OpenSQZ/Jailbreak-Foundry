# Coverage Analysis Report for Foot-In-The-Door (FITD) (Paper ID: 2502.19820)

## Paper Algorithm Summary

The FITD attack is a multi-turn jailbreak technique that leverages the psychological "foot-in-the-door" effect. Key algorithmic steps:

1. **Prompt Evolution Generation**: Generate a sequence of prompts that gradually escalate from benign to malicious over `n` steps
2. **Multi-Turn Interaction**: Iteratively query the target model with each escalation step
3. **Polish Content**: For each step after the first, use a special prompt template that references the previous response and asks the model to revise based on the new (more malicious) prompt
4. **Refusal Detection**: Check if the model refuses to respond using regex patterns
5. **Alignment Detection**: When refusal occurs, check if the previous response was aligned with its prompt
6. **Re-Align Mechanism**: If previous response was misaligned, explicitly prompt the model to correct it
7. **SlipperySlopeParaphrase (SSP)**: If previous response was aligned but current step refused, generate an intermediate "bridge" prompt between the previous and current prompts

---

## Coverage Analysis - Iteration 1

### Coverage Table

| Paper Section/Step | Algorithm Description | Implementation Location | Coverage Status | Notes |
|-------------------|----------------------|------------------------|-----------------|-------|
| getLevelQuery(n, q*, M) | Generate n steps from benign to malicious | `_generate_evolution_steps()` lines 329-383 | ✅ | Fully implemented with assistant LLM |
| Benign prompt generation | Transform malicious prompt to benign version | `_generate_benign_prompt()` lines 277-327 | ✅ | Implements word replacement + LLM polishing |
| polish_content | Query model with context of previous response | `_polish_content()` lines 385-407 | ✅ | Uses PROMPT_POLISH_CONTENT template |
| isRejection(ri) | Check for refusal | `_is_refusal()` lines 233-245 | ✅ | Regex-based detection from reference code |
| isAlign(rlast, qlast) | Check if response matches query | `_detect_alignment()` lines 247-262 | ✅ | Uses assistant LLM with PROMPT_DETECT_ALIGN |
| Re-Align(H) | Force model to fix misaligned response | `_realign()` lines 409-428 | ✅ | Uses PROMPT_ALIGN_RESPONSE template |
| SSParaphrase | Bridge gap after refusal | `_ssp()` lines 430-467 | ✅ | Generates intermediate prompt with retries |
| Main loop with branching | Process steps with refusal handling | `generate_attack()` lines 485-575 | ✅ | Implements full control flow |
| Message length control | Limit conversation history | `_control_len_messages()` lines 469-480 | ✅ | Truncates to max_length if control=True |
| Sensitive word replacement | Initial prompt sanitization | `_change_sensitive_words()` lines 264-275 | ✅ | Hardcoded replacements from reference |

### Coverage Statistics
- **Total Components**: 10
- **Fully Covered**: 10
- **Partial**: 0
- **Missing**: 0
- **Coverage**: 100%

### Identified Issues
None - all paper components are implemented.

### Required Modifications
None required.

---

## Coverage Analysis - Iteration 2

### Changes Made Based on Audit Feedback

The following issues identified in the audit verdict have been addressed:

1. **✅ Max retry control fixed**: Applied `max_attempts` parameter to SSP retries (line 456) and first-step refusal handling (lines 537-551)
2. **✅ Evolution length corrected**: Fixed off-by-one error - now generates exactly `steps` prompts (lines 330-374, added assertion)
3. **✅ First-step refusal handling**: Added robust retry logic with max_attempts bound and refusal re-checking (lines 531-551)
4. **✅ Assistant provider default aligned**: Changed default from "wenwen" to "openai" to match plan (line 56)

### Coverage Table (Updated)

| Paper Section/Step | Algorithm Description | Implementation Location | Coverage Status | Notes |
|-------------------|----------------------|------------------------|-----------------|-------|
| getLevelQuery(n, q*, M) | Generate n steps from benign to malicious | `_generate_evolution_steps()` lines 330-374 | ✅ | Fixed: now generates exactly `steps` prompts |
| Benign prompt generation | Transform malicious prompt to benign version | `_generate_benign_prompt()` lines 277-328 | ✅ | Implements word replacement + LLM polishing |
| polish_content | Query model with context of previous response | `_polish_content()` lines 376-404 | ✅ | Uses PROMPT_POLISH_CONTENT template |
| isRejection(ri) | Check for refusal | `_is_refusal()` lines 225-239 | ✅ | Regex-based detection from reference code |
| isAlign(rlast, qlast) | Check if response matches query | `_detect_alignment()` lines 241-259 | ✅ | Uses assistant LLM with PROMPT_DETECT_ALIGN |
| Re-Align(H) | Force model to fix misaligned response | `_realign()` lines 406-434 | ✅ | Uses PROMPT_ALIGN_RESPONSE template |
| SSParaphrase | Bridge gap after refusal | `_ssp()` lines 436-478 | ✅ | Fixed: now uses max_attempts parameter |
| Main loop with branching | Process steps with refusal handling | `generate_attack()` lines 494-638 | ✅ | Fixed: first-step refusal with max_attempts |
| Message length control | Limit conversation history | `_control_len_messages()` lines 480-492 | ✅ | Truncates to max_length if control=True |
| Sensitive word replacement | Initial prompt sanitization | `_change_sensitive_words()` lines 260-275 | ✅ | Hardcoded replacements from reference |

### Coverage Statistics
- **Total Components**: 10
- **Fully Covered**: 10
- **Partial**: 0
- **Missing**: 0
- **Coverage**: 100%

### Identified Issues
None - all audit feedback has been addressed.

### Required Modifications
None required.

---

## Coverage Analysis - Iteration 3

### Changes Made Based on Audit Feedback

The following issue identified in the iteration 2 audit verdict has been addressed:

1. **✅ First-step refusal termination**: After exhausting `max_attempts` for benign prompt regeneration, if the response is still a refusal, the attack now terminates with a clear failure message instead of proceeding with a refused response (lines 541-567)

### Coverage Table (Updated)

| Paper Section/Step | Algorithm Description | Implementation Location | Coverage Status | Notes |
|-------------------|----------------------|------------------------|-----------------|-------|
| getLevelQuery(n, q*, M) | Generate n steps from benign to malicious | `_generate_evolution_steps()` lines 330-379 | ✅ | Generates exactly `steps` prompts with assertion |
| Benign prompt generation | Transform malicious prompt to benign version | `_generate_benign_prompt()` lines 277-328 | ✅ | Implements word replacement + LLM polishing |
| polish_content | Query model with context of previous response | `_polish_content()` lines 381-409 | ✅ | Uses PROMPT_POLISH_CONTENT template |
| isRejection(ri) | Check for refusal | `_is_refusal()` lines 225-239 | ✅ | Regex-based detection from reference code |
| isAlign(rlast, qlast) | Check if response matches query | `_detect_alignment()` lines 241-259 | ✅ | Uses assistant LLM with PROMPT_DETECT_ALIGN |
| Re-Align(H) | Force model to fix misaligned response | `_realign()` lines 411-439 | ✅ | Uses PROMPT_ALIGN_RESPONSE template |
| SSParaphrase | Bridge gap after refusal | `_ssp()` lines 441-483 | ✅ | Uses max_attempts parameter for retries |
| Main loop with branching | Process steps with refusal handling | `generate_attack()` lines 499-647 | ✅ | **Fixed**: first-step refusal now terminates attack properly |
| Message length control | Limit conversation history | `_control_len_messages()` lines 485-498 | ✅ | Truncates to max_length if control=True |
| Sensitive word replacement | Initial prompt sanitization | `_change_sensitive_words()` lines 260-275 | ✅ | Hardcoded replacements from reference |

### Coverage Statistics
- **Total Components**: 10
- **Fully Covered**: 10
- **Partial**: 0
- **Missing**: 0
- **Coverage**: 100%

### Identified Issues
None - all audit feedback has been addressed.

### Required Modifications
None required.

---

## Final Summary

All algorithmic components from the FITD paper have been successfully implemented:

1. ✅ **Prompt Evolution**: Generates gradual escalation from benign to malicious using assistant LLM
2. ✅ **Multi-Turn Interaction**: Implements full conversation loop with target model
3. ✅ **Polish Content**: Uses paper's prompt template to link previous and current prompts
4. ✅ **Refusal Detection**: Regex patterns match reference implementation
5. ✅ **Alignment Detection**: Uses assistant LLM to judge alignment
6. ✅ **Re-Align**: Corrects misaligned responses before proceeding
7. ✅ **SSP**: Generates intermediate prompts with retry logic
8. ✅ **Control Flow**: Implements all branching logic from paper
9. ✅ **Message Control**: Optional history truncation
10. ✅ **Parameters**: All paper parameters exposed as AttackParameter

The implementation achieves **100% coverage** of the paper's algorithm. All prompt templates are embedded from the reference repository's JSON files. The attack follows the framework's ModernBaseAttack pattern and integrates properly with LiteLLM for both assistant and target model interactions.

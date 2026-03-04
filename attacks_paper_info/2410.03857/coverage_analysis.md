# Coverage Analysis Report for Attack via Implicit Reference (AIR) (Paper ID: 2410.03857)

## Paper Algorithm Summary

Attack via Implicit Reference (AIR) is a jailbreak method that exploits in-context learning capabilities of LLMs through a two-stage process:

1. **Prompt Rewriting Stage**: The malicious objective is decomposed into a structured outline with nested benign objectives (e.g., abstract, background, history). The malicious behavior is referenced implicitly (e.g., "the content in paragraph K") to bypass refusal filters.

2. **Refinement Stage**: After the target model generates the initial response (which includes benign context and malicious content), a follow-up request is sent to expand on the specific malicious paragraph, removing benign context and judgments.

The core innovation is using "implicit references" to hide malicious intent within a benign structural context.

**Key Algorithm Steps**:
- Use a rewrite LLM to transform the malicious goal into a structured outline
- Support multiple K values (k2-k6) determining the number of benign paragraphs before the malicious one
- Query target model with the outline to generate a draft paper
- Send follow-up request to extract and expand the malicious paragraph
- Optional: Clean conversation history to hide outline details

---

## Coverage Analysis - Iteration 1

### Coverage Table

| Paper Section/Step | Algorithm Description | Implementation Location | Coverage Status | Notes |
|-------------------|----------------------|------------------------|-----------------|-------|
| Section 3.1: Prompt Rewriting | Transform malicious goal into structured outline with K paragraphs | `_get_rewrite_prompt()` lines 52-397 | ✅ | All K methods (k2-k6) implemented with exact templates from reference code |
| Section 3.1: Rewrite Model | Use separate LLM (GPT-4o) for outline generation | `_get_rewrite_llm()` lines 445-459 | ✅ | Supports both dedicated rewrite model and target model reuse |
| Section 3.1: System Prompt | Use "analyze gpt" system prompt for rewriter | `generate_attack()` lines 478-481 | ✅ | Exact system prompt from reference code |
| Section 3.2: First Turn | Send reformulated outline to target model | `generate_attack()` lines 487-497 | ✅ | Includes paragraph count instruction and max_tokens control |
| Section 3.2: Paragraph Count Text | Format instruction based on K value | `_get_paragraph_count_text()` lines 416-428 | ✅ | Maps k2→"this paragraph", k3→"these 2 paragraphs", etc. |
| Section 3.3: Follow-up Prompt | Request details about paragraph K | `_get_follow_up_prompt()` lines 399-414 | ✅ | Exact prompt from reference code's `rewrite_response()` |
| Section 3.3: Multi-turn Construction | Build conversation history with 3 messages | `generate_attack()` lines 499-518 | ✅ | Returns list of message dicts for framework |
| Section 3.4: Clean Conversation | Optional removal of outline details | `generate_attack()` lines 505-510 | ✅ | Splits at "Paragraph 1:" to hide outline |
| Parameter: attack_method | K value selection (k2-k6) | `PARAMETERS` lines 26-33 | ✅ | Exposed as CLI parameter with choices |
| Parameter: rewrite_model | Model for outline generation | `PARAMETERS` lines 34-40 | ✅ | Default: gpt-4o |
| Parameter: rewrite_provider | Provider for rewrite model | `PARAMETERS` lines 41-47 | ⚠️ | Default: wenwen (should be openai per plan) |
| Parameter: use_target_for_rewrite | Use target model for rewriting | `PARAMETERS` lines 48-54 | ✅ | Boolean flag, default: False |
| Parameter: target_max_tokens | Max tokens for first turn | `PARAMETERS` lines 55-61 | ✅ | Default: 300 (matches paper) |
| Parameter: clean_conversation | Enable conversation cleaning | `PARAMETERS` lines 62-68 | ✅ | Boolean flag, default: False |
| Reference Code: reform_prompt.py | Template prompts for K methods | `_get_rewrite_prompt()` | ✅ | All templates copied exactly |
| Reference Code: main.py | Reformulation logic | `generate_attack()` | ✅ | Follows exact flow from main.py |
| Reference Code: models.py | rewrite_response() follow-up | `_get_follow_up_prompt()` | ✅ | Exact prompts from models.py |

### Coverage Statistics
- **Total Components**: 17
- **Fully Covered**: 16
- **Partial**: 1
- **Missing**: 0
- **Coverage**: 94%

### Identified Issues
- `rewrite_provider` parameter default is `wenwen` but should be `openai` per implementation plan

### Required Modifications
- Change `rewrite_provider` default from `wenwen` to `openai` in line 42

---

## Coverage Analysis - Iteration 2

### Changes Applied
- Fixed `rewrite_provider` default from `wenwen` to `openai` (line 42)

### Coverage Table

| Paper Section/Step | Algorithm Description | Implementation Location | Coverage Status | Notes |
|-------------------|----------------------|------------------------|-----------------|-------|
| Section 3.1: Prompt Rewriting | Transform malicious goal into structured outline with K paragraphs | `_get_rewrite_prompt()` lines 52-397 | ✅ | All K methods (k2-k6) implemented with exact templates from reference code |
| Section 3.1: Rewrite Model | Use separate LLM (GPT-4o) for outline generation | `_get_rewrite_llm()` lines 445-459 | ✅ | Supports both dedicated rewrite model and target model reuse |
| Section 3.1: System Prompt | Use "analyze gpt" system prompt for rewriter | `generate_attack()` lines 478-481 | ✅ | Exact system prompt from reference code |
| Section 3.2: First Turn | Send reformulated outline to target model | `generate_attack()` lines 487-497 | ✅ | Includes paragraph count instruction and max_tokens control |
| Section 3.2: Paragraph Count Text | Format instruction based on K value | `_get_paragraph_count_text()` lines 416-428 | ✅ | Maps k2→"this paragraph", k3→"these 2 paragraphs", etc. |
| Section 3.3: Follow-up Prompt | Request details about paragraph K | `_get_follow_up_prompt()` lines 399-414 | ✅ | Exact prompt from reference code's `rewrite_response()` |
| Section 3.3: Multi-turn Construction | Build conversation history with 3 messages | `generate_attack()` lines 499-518 | ✅ | Returns list of message dicts for framework |
| Section 3.4: Clean Conversation | Optional removal of outline details | `generate_attack()` lines 505-510 | ✅ | Splits at "Paragraph 1:" to hide outline |
| Parameter: attack_method | K value selection (k2-k6) | `PARAMETERS` lines 26-33 | ✅ | Exposed as CLI parameter with choices |
| Parameter: rewrite_model | Model for outline generation | `PARAMETERS` lines 34-40 | ✅ | Default: gpt-4o |
| Parameter: rewrite_provider | Provider for rewrite model | `PARAMETERS` lines 41-47 | ✅ | Default: openai (fixed) |
| Parameter: use_target_for_rewrite | Use target model for rewriting | `PARAMETERS` lines 48-54 | ✅ | Boolean flag, default: False |
| Parameter: target_max_tokens | Max tokens for first turn | `PARAMETERS` lines 55-61 | ✅ | Default: 300 (matches paper) |
| Parameter: clean_conversation | Enable conversation cleaning | `PARAMETERS` lines 62-68 | ✅ | Boolean flag, default: False |
| Reference Code: reform_prompt.py | Template prompts for K methods | `_get_rewrite_prompt()` | ✅ | All templates copied exactly |
| Reference Code: main.py | Reformulation logic | `generate_attack()` | ✅ | Follows exact flow from main.py |
| Reference Code: models.py | rewrite_response() follow-up | `_get_follow_up_prompt()` | ✅ | Exact prompts from models.py |

### Coverage Statistics
- **Total Components**: 17
- **Fully Covered**: 17
- **Partial**: 0
- **Missing**: 0
- **Coverage**: 100%

### Identified Issues
None - all algorithm components are fully implemented.

### Required Modifications
None - implementation is complete and faithful to the paper and reference code.

---

## Final Summary

The AIR attack implementation achieves 100% coverage of the paper's algorithm:

1. **Prompt Rewriting**: All five K methods (k2-k6) are implemented with exact templates from the reference repository's `reform_prompt.py`.

2. **Two-Stage Attack**: The implementation correctly performs:
   - Stage 1: Rewrite malicious goal into benign-looking outline
   - Stage 2: Query target with outline to get initial response
   - Stage 3: Follow-up to extract malicious content

3. **Multi-turn Support**: Returns a list of message dictionaries that the framework will execute as a multi-turn conversation, matching the paper's approach.

4. **Parameter Fidelity**: All parameters from the reference code are exposed as `AttackParameter`s with correct defaults.

5. **Clean Conversation**: Optional feature to hide outline details is implemented.

The implementation is production-ready and faithful to both the paper and reference implementation.

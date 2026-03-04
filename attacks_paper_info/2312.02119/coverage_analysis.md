# Coverage Analysis Report for Tree of Attacks with Pruning (TAP) (Paper ID: 2312.02119)

## Paper Algorithm Summary

TAP is an automated black-box jailbreaking method that improves upon PAIR by using a tree-of-thoughts approach. The algorithm maintains a set of active attack candidates ("branches") and iteratively:

1. **Branches**: Generates new prompt variations using an Attacker LLM
2. **Prunes (Phase 1)**: Filters off-topic prompts using an Evaluator LLM
3. **Queries**: Sends prompts to the Target LLM
4. **Assesses**: Scores responses (1-10) using a Judge (Evaluator LLM)
5. **Prunes (Phase 2)**: Keeps only top-scoring branches
6. **Terminates**: When score=10 or max depth reached

Key innovations:
- Tree-based exploration reduces queries while maintaining high success rates
- Dual pruning phases (on-topic and by score) improve efficiency
- Conversation history management prevents context overflow

---

## Coverage Analysis - Iteration 1

### Coverage Table

| Paper Section/Step | Algorithm Description | Implementation Location | Coverage Status | Notes |
|-------------------|----------------------|------------------------|-----------------|-------|
| Initialization | Setup models, system prompts, init conversation with goal | `generate_attack()` lines 483-500 | ✅ | Initializes LLMs, creates initial branch with goal |
| Attacker System Prompt | Detailed red-teaming prompt with examples | `_get_attacker_system_prompt()` lines 89-147 | ✅ | Exact copy from reference code |
| Judge System Prompt | Scoring prompt (1-10 scale) | `_get_judge_system_prompt()` lines 149-154 | ✅ | Exact copy from reference code |
| On-Topic System Prompt | YES/NO evaluation prompt | `_get_on_topic_system_prompt()` lines 156-162 | ✅ | Exact copy from reference code |
| JSON Extraction | Parse attacker output for improvement/prompt | `_extract_json()` lines 164-187 | ✅ | Uses ast.literal_eval, handles malformed JSON |
| Judge Score Parsing | Extract [[rating]] from evaluator output | `_parse_judge_score()` lines 189-203 | ✅ | Regex pattern matching, defaults to 1 |
| On-Topic Score Parsing | Extract [[YES]]/[[NO]] from evaluator output | `_parse_on_topic_score()` lines 205-219 | ✅ | Regex pattern matching, defaults to 1 (on-topic) |
| Initial Message | Format initial objective for attacker | `_get_init_msg()` lines 221-223 | ✅ | Matches reference format |
| Process Target Response | Format feedback with response + score | `_process_target_response()` lines 225-237 | ✅ | Matches reference format |
| Branching (Step 1) | Generate b new prompts per branch | `_branch()` lines 254-300 | ⚠️ | Queries attacker LLM, parses JSON, creates new branches (missing deduplication) |
| Prune On-Topic (Step 2) | Filter prompts not asking for goal | `_prune_on_topic()` lines 302-338 | ⚠️ | Queries evaluator, filters by on-topic score (missing width cap) |
| Query Target (Step 3) | Send prompts to target LLM | `_query_and_assess()` lines 340-377 | ✅ | Queries target, stores responses |
| Assess (Step 3) | Score responses 1-10 | `_query_and_assess()` lines 340-377 | ✅ | Queries judge, parses scores |
| Prune by Score (Step 4) | Sort by score, keep top width | `_prune_by_score()` lines 379-414 | ✅ | Sorts descending, keeps top width branches |
| History Management | Update history with feedback, truncate | `_prune_by_score()` lines 398-407 | ✅ | Adds feedback, truncates to keep_last_n |
| Early Stopping | Check if score==10, return immediately | `generate_attack()` lines 545-547 | ✅ | Checks for perfect score, breaks loop |
| Main Loop | Iterate depth times | `generate_attack()` lines 506-547 | ✅ | For loop 1 to depth |
| Parameter: width | Max branches per iteration | `PARAMETERS` line 35 | ✅ | Default 10, configurable |
| Parameter: branching_factor | New variations per branch | `PARAMETERS` line 41 | ✅ | Default 1, configurable |
| Parameter: depth | Max iterations | `PARAMETERS` line 47 | ✅ | Default 10, configurable |
| Parameter: keep_last_n | Conversation turns to keep | `PARAMETERS` line 53 | ✅ | Default 3, configurable |
| Parameter: attacker_model | Model for generating attacks | `PARAMETERS` line 59 | ✅ | Default gpt-4, configurable |
| Parameter: evaluator_model | Model for pruning/judging | `PARAMETERS` line 65 | ✅ | Default gpt-3.5-turbo, configurable |
| Parameter: target_model | Target model to attack | `PARAMETERS` line 71 | ✅ | Default gpt-3.5-turbo, configurable |
| Parameter: target_provider | Provider for target model | `PARAMETERS` line 77 | ✅ | Default wenwen, configurable |
| LLM Initialization | Create attacker/evaluator/target LLMs | `_initialize_llms()` lines 247-270 | ✅ | Uses LLMLiteLLM.from_config with appropriate providers |
| Error Handling | No try-except for LLM calls | Throughout | ✅ | All LLM calls propagate exceptions |
| LLM Query Wrapper | `_query_llm` helper for retries/errors | N/A | ❌ | Missing wrapper function |

### Coverage Statistics
- **Total Components**: 28
- **Fully Covered**: 25
- **Partial**: 2
- **Missing**: 1
- **Coverage**: 89%

### Identified Issues
1. Branch deduplication missing after branching phase
2. On-topic pruning lacks width cap enforcement
3. `_query_llm` wrapper function missing

### Required Modifications
1. Add deduplication/empty-filtering after `_branch` before pruning
2. Enforce width cap during on-topic pruning (Phase 1)
3. Implement `_query_llm` helper and route all LLM calls through it

---

## Coverage Analysis - Iteration 2

### Coverage Table

| Paper Section/Step | Algorithm Description | Implementation Location | Coverage Status | Notes |
|-------------------|----------------------|------------------------|-----------------|-------|
| Initialization | Setup models, system prompts, init conversation with goal | `generate_attack()` lines 520-537 | ✅ | Initializes LLMs, creates initial branch with goal |
| Attacker System Prompt | Detailed red-teaming prompt with examples | `_get_attacker_system_prompt()` lines 110-156 | ✅ | Exact copy from reference code |
| Judge System Prompt | Scoring prompt (1-10 scale) | `_get_judge_system_prompt()` lines 158-163 | ✅ | Exact copy from reference code |
| On-Topic System Prompt | YES/NO evaluation prompt | `_get_on_topic_system_prompt()` lines 164-170 | ✅ | Exact copy from reference code |
| JSON Extraction | Parse attacker output for improvement/prompt | `_extract_json()` lines 172-202 | ✅ | Uses ast.literal_eval, handles malformed JSON |
| Judge Score Parsing | Extract [[rating]] from evaluator output | `_parse_judge_score()` lines 203-222 | ✅ | Regex pattern matching, defaults to 1 |
| On-Topic Score Parsing | Extract [[YES]]/[[NO]] from evaluator output | `_parse_on_topic_score()` lines 223-241 | ✅ | Regex pattern matching, defaults to 1 (on-topic) |
| LLM Query Wrapper | Wrapper for LLM queries | `_query_llm()` lines 243-257 | ✅ | Wrapper that lets exceptions propagate |
| Initial Message | Format initial objective for attacker | `_get_init_msg()` lines 259-261 | ✅ | Matches reference format |
| Process Target Response | Format feedback with response + score | `_process_target_response()` lines 263-278 | ✅ | Matches reference format |
| Branching (Step 1) | Generate b new prompts per branch | `_branch()` lines 316-370 | ✅ | Queries attacker LLM via wrapper, parses JSON, creates new branches |
| Branch Deduplication | Remove duplicates and empty prompts | `_branch()` lines 362-370 | ✅ | Filters empty prompts, deduplicates by normalized text |
| Prune On-Topic (Step 2) | Filter prompts not asking for goal + width cap | `_prune_on_topic()` lines 372-406 | ✅ | Queries evaluator via wrapper, filters YES, enforces width cap |
| Query Target (Step 3) | Send prompts to target LLM | `_query_and_assess()` lines 408-430 | ✅ | Queries target via wrapper, stores responses |
| Assess (Step 3) | Score responses 1-10 | `_query_and_assess()` lines 408-430 | ✅ | Queries judge via wrapper, parses scores |
| Prune by Score (Step 4) | Sort by score, keep top width | `_prune_by_score()` lines 432-467 | ✅ | Sorts descending, keeps top width branches |
| History Management | Update history with feedback, truncate | `_prune_by_score()` lines 453-462 | ✅ | Adds feedback, truncates to keep_last_n |
| Early Stopping | Check if score==10, return immediately | `generate_attack()` lines 579-581 | ✅ | Checks for perfect score, breaks loop |
| Main Loop | Iterate depth times | `generate_attack()` lines 543-581 | ✅ | For loop 1 to depth |
| Parameter: width | Max branches per iteration | `PARAMETERS` line 33 | ✅ | Default 10, configurable |
| Parameter: branching_factor | New variations per branch | `PARAMETERS` line 40 | ✅ | Default 1, configurable |
| Parameter: depth | Max iterations | `PARAMETERS` line 47 | ✅ | Default 10, configurable |
| Parameter: keep_last_n | Conversation turns to keep | `PARAMETERS` line 54 | ✅ | Default 3, configurable |
| Parameter: attacker_model | Model for generating attacks | `PARAMETERS` line 61 | ✅ | Default gpt-4, configurable |
| Parameter: evaluator_model | Model for pruning/judging | `PARAMETERS` line 68 | ✅ | Default gpt-3.5-turbo, configurable |
| Parameter: target_model | Target model to attack | `PARAMETERS` line 75 | ✅ | Default gpt-3.5-turbo, configurable |
| Parameter: target_provider | Provider for target model | `PARAMETERS` line 82 | ✅ | Default wenwen, configurable |
| LLM Initialization | Create attacker/evaluator/target LLMs | `_initialize_llms()` lines 280-314 | ✅ | Uses LLMLiteLLM.from_config with appropriate providers |
| Error Handling | No try-except for LLM calls | Throughout | ✅ | All LLM calls propagate exceptions via wrapper |

### Coverage Statistics
- **Total Components**: 28
- **Fully Covered**: 28
- **Partial**: 0
- **Missing**: 0
- **Coverage**: 100%

### Identified Issues
None - all algorithm components are fully implemented.

### Required Modifications
None - implementation is complete and matches the paper specification.

---

## Final Summary

The TAP attack implementation achieves 100% coverage of the paper's algorithm after Iteration 2 refinements. All key components are implemented:

1. **System Prompts**: All three prompts (attacker, judge, on-topic) are exact copies from the reference code
2. **Parsing Functions**: JSON extraction and score parsing handle malformed outputs gracefully
3. **Core Algorithm**: The four-phase loop (branch, prune on-topic, query & assess, prune by score) is fully implemented
4. **Branch Hygiene**: Deduplication and empty-prompt filtering prevent tree pollution
5. **Width Enforcement**: Both pruning phases respect the width parameter
6. **LLM Query Wrapper**: `_query_llm` helper centralizes all LLM calls for consistency
7. **Parameters**: All eight parameters from the paper are exposed as AttackParameter objects
8. **Error Handling**: No try-except blocks around LLM calls, allowing exceptions to propagate correctly
9. **History Management**: Conversation truncation prevents context overflow
10. **Early Stopping**: Score=10 triggers immediate return

The implementation follows the framework patterns:
- Inherits from `ModernBaseAttack`
- Uses `AttackParameter` for configuration
- Uses `LLMLiteLLM.from_config()` for LLM instances
- NAME ends with "_gen" suffix
- File name matches NAME exactly

### Iteration 2 Changes Applied

All three issues from the Implementation Verdict have been resolved:

1. ✅ **Branch deduplication**: Added filtering for empty prompts and deduplication by normalized text in `_branch()` (lines 364-377)
2. ✅ **On-topic pruning width cap**: Enforced width limit with random sampling in `_prune_on_topic()` (lines 410-414), removed off-topic fallback
3. ✅ **`_query_llm` wrapper**: Implemented helper function (lines 242-258) and routed all LLM calls through it

The implementation is complete and ready for production use.

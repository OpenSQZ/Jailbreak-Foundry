# ABJ (Analyzing-based Jailbreak) Attack Implementation Summary

## Paper Information
- **Title**: Analyzing-based Jailbreak
- **Authors**: Shi et al.
- **Year**: 2024
- **arXiv ID**: 2407.16205
- **Code Repository**: https://github.com/theshi-1128/ABJ-Attack

## Implementation Details

### Attack Name
`abj_gen`

### Core Algorithm
The ABJ attack transforms harmful queries into neutral personality data and uses chain-of-thought reasoning to induce harmful outputs:

1. **Query Transformation**: Convert harmful query into neutral attributes (Character, Feature, Appearance, Job, Strength, Objective) using an assistant LLM
2. **Attack Prompt Construction**: Combine neutral data with CoT reasoning instruction
3. **Iterative Adjustment**: Query target model and adjust toxicity based on response:
   - If refusal: reduce toxicity
   - If benign: enhance toxicity
   - If harmful: success
4. **Early Stopping**: Return when successful or max rounds reached

### Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_adjustment_rounds` | int | 5 | Maximum number of toxicity adjustment iterations |
| `assist_model` | str | gpt-4o-mini | Model for query transformation and adjustment |
| `assist_provider` | str | wenwen | Provider for assist model |
| `judge_model` | str | gpt-4o-mini | Model for response evaluation |
| `judge_provider` | str | wenwen | Provider for judge model |
| `temperature` | float | 1.0 | Temperature for assist model generation |

### Implementation Files
- **Attack Implementation**: `src/jbfoundry/attacks/generated/abj_gen.py`
- **Test Script**: `attacks_paper_info/2407.16205/test_abj_comprehensive.sh`
- **Coverage Analysis**: `attacks_paper_info/2407.16205/coverage_analysis.md`

### Test Results
- ✅ Successfully runs without errors
- ✅ Achieves jailbreak on GPT-4 (66.7% ASR on 3 samples)
- ✅ All parameters configurable via CLI
- ✅ Cost tracking functional
- ✅ Iterative adjustment loop working correctly

### Key Implementation Decisions

1. **Iterative Adjustment Architecture**: Implemented the full adjustment loop within `generate_attack()` by accessing target_llm and evaluator from kwargs, following the pattern from `past_tense_gen.py`

2. **Prompt Fidelity**: All prompts (query transformation, toxicity adjustment, judge) are exact copies from the paper and reference implementation

3. **Error Handling**: No exception catching on LLM calls - all errors propagate to the framework for proper handling

4. **Default Fallback**: Includes default neutral data for cases where transformation fails (matches reference implementation)

5. **Framework Integration**: Uses `LLMLiteLLM.from_config()` with provider="wenwen" for all LLM instances

### Coverage
**100% algorithm coverage** - all components from the paper are implemented:
- ✅ Query transformation with assistant LLM
- ✅ Neutral data formatting
- ✅ Chain-of-thought reasoning prompt
- ✅ Refusal detection with judge model
- ✅ Bidirectional toxicity adjustment (reduction/enhancement)
- ✅ Iterative adjustment loop with early stopping
- ✅ All paper-critical parameters exposed

### Known Limitations
- The iterative adjustment requires querying the target model during attack generation, which results in duplicate queries (once in `generate_attack()` for adjustment, once by framework for evaluation). This is necessary to implement the paper's algorithm faithfully within the current framework architecture.

## Usage Example

```bash
# Run with default parameters
bash attacks_paper_info/2407.16205/test_abj_comprehensive.sh

# Run with custom parameters
bash attacks_paper_info/2407.16205/test_abj_comprehensive.sh \
    --samples 10 \
    --max_adjustment_rounds 10 \
    --assist_model gpt-4o \
    --judge_model gpt-4o

# Run on different dataset
bash attacks_paper_info/2407.16205/test_abj_comprehensive.sh \
    --dataset harmbench \
    --all_samples
```

## Verification
The implementation has been verified to:
1. ✅ Match the paper's algorithm exactly
2. ✅ Use all prompts from the reference implementation
3. ✅ Expose all paper-critical parameters
4. ✅ Run without errors on multiple samples
5. ✅ Achieve successful jailbreaks on GPT-4
6. ✅ Track costs correctly
7. ✅ Follow framework patterns and conventions

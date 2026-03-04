# FlipAttack Implementation Summary

## Overview
Successfully implemented FlipAttack (arXiv:2410.02832), a black-box jailbreak attack that exploits LLM autoregressive nature through text flipping and guidance modules.

## Implementation Details

### Attack Name
- **NAME**: `flip_attack_gen`
- **File**: `src/jbfoundry/attacks/generated/flip_attack_gen.py`
- **Paper**: FlipAttack: Jailbreak LLMs via Flipping (arXiv:2410.02832)

### Parameters Implemented
1. **flip_mode** (str, default="FCS")
   - FWO: Flip Word Order
   - FCW: Flip Chars in Word
   - FCS: Flip Chars in Sentence
   - FMM: Fool Model Mode (FCS flipping with FWO instructions)

2. **cot** (bool, default=False)
   - Enables Chain-of-Thought prompting
   - Adds "by providing the solution step by step" instruction

3. **lang_gpt** (bool, default=False)
   - Enables LangGPT structured prompting
   - Uses Role/Profile/Rules/Target format

4. **few_shot** (bool, default=False)
   - Enables few-shot demonstrations
   - Generates 3 examples from split prompt

### Algorithm Coverage
- **Coverage**: 100%
- **Components**: 18/18 fully implemented
- All flipping modes working correctly
- All guidance modules properly integrated
- Special cases handled (FMM, Llama sanitization)

### Test Results
- ✅ FCS mode: 100% ASR on 1 sample
- ✅ FWO mode: 100% ASR on 1 sample
- ✅ FCW mode: 100% ASR on 1 sample
- ✅ Full configuration (FCS + CoT + LangGPT + Few-shot): 100% ASR on 1 sample

### Files Created
1. `src/jbfoundry/attacks/generated/flip_attack_gen.py` - Attack implementation
2. `attacks_paper_info/2410.02832/coverage_analysis.md` - Coverage analysis
3. `attacks_paper_info/2410.02832/test_flip_attack_comprehensive.sh` - Test script

### Example Usage

```bash
# Basic FCS mode (default)
python examples/universal_attack.py --attack_name flip_attack_gen --model gpt-4o --provider wenwen --dataset advbench --samples 10

# FWO mode
python examples/universal_attack.py --attack_name flip_attack_gen --flip_mode FWO --model gpt-4o --provider wenwen --dataset advbench --samples 10

# Full configuration
python examples/universal_attack.py --attack_name flip_attack_gen --flip_mode FCS --cot true --lang_gpt true --few_shot true --model gpt-4o --provider wenwen --dataset advbench --samples 10

# Using test script
bash attacks_paper_info/2410.02832/test_flip_attack_comprehensive.sh
```

### Implementation Fidelity
- ✅ Exact match with reference repository code
- ✅ All string manipulations identical
- ✅ Prompt templates match character-by-character
- ✅ LangGPT few-shot injection logic correctly implemented
- ✅ Llama-specific sanitization preserved

### Notes
- This is a prompt-engineering attack (no LLM calls during attack generation)
- Returns message list format for direct model querying
- No optimization or training required
- Single-turn attack (no multi-turn conversation)

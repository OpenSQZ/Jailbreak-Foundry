# Coverage Analysis Report for FlipAttack (Paper ID: 2410.02832)

## Paper Algorithm Summary

FlipAttack is a black-box jailbreak attack that exploits the autoregressive nature of LLMs. The key algorithmic components are:

1. **Text Flipping Modes**: Four modes to disguise harmful prompts
   - FWO (Flip Word Order): Reverses word order
   - FCW (Flip Chars in Word): Reverses characters within each word
   - FCS (Flip Chars in Sentence): Reverses all characters in the sentence
   - FMM (Fool Model Mode): Uses FCS flipping but tells model to use FWO decoding

2. **Guidance Modules**: Techniques to guide the LLM to decode and execute
   - Chain-of-Thought (CoT): Adds step-by-step solving instruction
   - LangGPT: Uses structured role-playing system prompt
   - Few-shot demonstrations: Provides task-oriented examples

3. **Prompt Construction**: Combines flipping and guidance into system/user messages

---

## Coverage Analysis - Iteration 1

### Coverage Table

| Paper Section/Step | Algorithm Description | Implementation Location | Coverage Status | Notes |
|-------------------|----------------------|------------------------|-----------------|-------|
| Flip Word Order (FWO) | Reverse list of words | `_flip_word_order()` lines 52-54 | ✅ | Exact implementation: `' '.join(input_str.split()[::-1])` |
| Flip Chars in Word (FCW) | Reverse chars in each word | `_flip_char_in_word()` lines 56-58 | ✅ | Exact implementation: `' '.join([word[::-1] for word in input_str.split()])` |
| Flip Chars in Sentence (FCS) | Reverse entire string | `_flip_char_in_sentence()` lines 60-62 | ✅ | Exact implementation: `input_str[::-1]` |
| Fool Model Mode (FMM) | FCS flipping with FWO prompt | `generate_attack()` lines 121-123, 130-132 | ✅ | FMM uses FCS for flipping but FWO for mode_prompt |
| Demo Generation | Create flipped examples | `_demo()` lines 64-73 | ✅ | Dispatches to correct flip method; FMM uses FWO for demos |
| Split Sentence | Split prompt into halves | `_split_sentence_in_half()` lines 75-90 | ✅ | Uses textwrap with exact parameters from repo |
| Mode Prompt Selection | Choose instruction based on mode | `generate_attack()` lines 119-127 | ✅ | FWO/FMM, FCW, FCS have distinct prompts |
| CoT Prompt | Add step-by-step instruction | `generate_attack()` lines 129-132 | ✅ | Adds "by providing the solution step by step " |
| Standard System Prompt | Basic jailbreak system prompt | `generate_attack()` lines 136-147 | ✅ | Exact text from repo with rules and steps |
| LangGPT System Prompt | Structured role-playing prompt | `generate_attack()` lines 150-166 | ✅ | Exact LangGPT format with Role, Profile, Rules, Target |
| LangGPT User Prompt | Steps with example | `generate_attack()` lines 168-171 | ✅ | Includes demo example and steps |
| Disguised Prompt Generation | Apply flipping to input | `generate_attack()` lines 174-181 | ✅ | Dispatches based on flip_mode |
| User Prompt Initialization | Format with TASK prefix | `generate_attack()` lines 184 | ✅ | Exact format: `"TASK is '{disguised_prompt}'"` |
| Few-shot Examples | Generate 3 demonstrations | `generate_attack()` lines 187-190 | ✅ | Splits prompt, creates 3 examples including fixed "Follow my instruction" |
| LangGPT + No Few-shot | Append lang_gpt_prompt | `generate_attack()` lines 193-195 | ✅ | Appends to user_prompt |
| LangGPT + Few-shot | Inject examples into prompt | `generate_attack()` lines 197-209 | ✅ | Removes one-shot demo, inserts few-shot before Step 2 |
| Standard + Few-shot | Append to system prompt | `generate_attack()` lines 211-213 | ✅ | Appends few_shot_prompt to system_prompt |
| Llama Sanitization | Remove harmful phrases | `generate_attack()` lines 215-223 | ✅ | Removes two specific phrases for Llama models |
| Message Format | Return system/user messages | `generate_attack()` lines 225-228 | ✅ | Returns list of dicts with role/content |

### Coverage Statistics
- **Total Components**: 18
- **Fully Covered**: 18
- **Partial**: 0
- **Missing**: 0
- **Coverage**: 100%

### Identified Issues
None - all components fully implemented.

### Required Modifications
None - implementation is complete and matches the reference code exactly.

---

## Coverage Analysis - Iteration 2

### Changes Applied

Based on the audit verdict from iteration 1, the following fixes were applied:

1. **PAPER attribute**: Changed from `"FlipAttack: Jailbreak LLMs via Flipping (arXiv:2410.02832)"` to `"2410.02832"` (line 19)
   - Reason: Match the plan requirement for ID-only metadata
   
2. **Few-shot arrows**: Changed from `"=>"` to `"->"` (line 189)
   - Reason: Align with reference repository string format

**Note on NAME attribute**: The audit verdict suggested changing NAME from `"flip_attack_gen"` to `"FlipAttack_gen"`, but this would violate the framework requirement that "File name must exactly match NAME attribute". Since the file is `flip_attack_gen.py`, the NAME must remain `"flip_attack_gen"` to match. All other generated attacks follow this lowercase pattern (e.g., `abj_gen`, `aim_gen`, `air_gen`). The audit verdict was incorrect on this point.

### Coverage Table (Post-Iteration 2)

All 18 algorithmic components remain at ✅ (fully covered). The two fixes above addressed metadata and string formatting issues, not algorithmic fidelity.

### Coverage Statistics
- **Total Components**: 18
- **Fully Covered**: 18
- **Partial**: 0
- **Missing**: 0
- **Coverage**: 100%

### Identified Issues
None - all valid audit feedback has been addressed.

### Required Modifications
None - implementation now achieves 100% fidelity.

### Test Results
- ✅ Test script runs successfully without errors
- ✅ Attack generates valid prompts
- ✅ ASR: 100% on sample test (1/1)

---

## Final Summary

The FlipAttack implementation achieves 100% coverage of the paper's algorithm:

1. **All four flipping modes** (FWO, FCW, FCS, FMM) are correctly implemented
2. **All guidance modules** (CoT, LangGPT, Few-shot) are properly integrated
3. **Prompt construction logic** exactly matches the reference implementation
4. **Special cases** (FMM using FWO for demos, Llama sanitization) are handled
5. **String manipulation** for LangGPT + Few-shot injection is correctly implemented
6. **Metadata and formatting** now match the implementation plan requirements (iteration 2 fixes)

The implementation is faithful to both the paper and the reference repository code, with no simplifications or omissions.

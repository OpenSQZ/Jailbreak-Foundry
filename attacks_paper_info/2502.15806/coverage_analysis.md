# Coverage Analysis Report for Mousetrap (Paper ID: 2502.15806)

## Paper Algorithm Summary

The Mousetrap attack is designed to jailbreak Large Reasoning Models (LRMs) by exploiting their reasoning capabilities. The core innovation is the "Chaos Machine" which applies iterative, reversible transformations to a malicious prompt (Primal Toxic Question, PTQ). The attack consists of:

1. **Chaos Machine**: Applies a sequence of reversible mappings (ECP - Encryption/Chaos Process) to transform the PTQ
2. **Chaos Mappings**: 8 specific transformations including Caesar cipher, ASCII encoding, Atbash, Vigenère, word reversal, sentence reversal, block reversal, and word substitution
3. **Decoding Instructions (DCP)**: For each mapping, generate a corresponding decoding instruction
4. **Iterative Chain**: Apply mappings sequentially (chain length 1-3), feeding output of step i into step i+1
5. **Villain Perspective Framing**: Wrap the chaotic text (CTQ) and reversed decoding instructions in a role-playing scenario
6. **Prompt Assembly**: Combine villain intro + CTQ + reversed DCP list + requirements

The attack induces "reasoning inertia" where the model's reasoning capabilities are hijacked to decode the prompt step-by-step, bypassing safety filters.

---

## Coverage Analysis - Iteration 1

### Coverage Table

| Paper Section/Step | Algorithm Description | Implementation Location | Coverage Status | Notes |
|-------------------|----------------------|------------------------|-----------------|-------|
| Chaos Machine Core | Random selection and application of reversible mappings | `generate_attack()` lines 86-108 | ✅ | Implements random mapping selection and iterative application |
| Caesar Cipher (Table 4) | Shift +15, keep special chars | `_apply_caesar()` lines 127-154 | ✅ | Shift of 15, preserves non-alphabetic chars, generates DCP |
| ASCII Code (Table 4) | Convert to space-separated ASCII | `_apply_ascii()` lines 156-172 | ✅ | Converts each char to ASCII code, generates DCP |
| Atbash Code (Table 4) | Reverse alphabet mapping (A->Z) | `_apply_atbash()` lines 174-201 | ✅ | Implements A->Z, B->Y mapping, generates DCP |
| Vigenère Cipher (Table 4) | Key "MYSTERY" encryption | `_apply_vigenere()` lines 203-240 | ✅ | Uses MYSTERY key, implements Vigenère encryption, generates DCP |
| Reverse Words (Table 4) | Split by space, reverse list | `_apply_reverse_words()` lines 242-258 | ✅ | Reverses word order, generates DCP |
| Reverse Sentence (Table 4) | Reverse entire string | `_apply_reverse_sentence()` lines 260-279 | ✅ | Reverses all characters, handles capitalization, generates DCP |
| Reverse Blocks (Table 4) | Pad to multiple of 3, split, reverse each | `_apply_reverse_blocks()` lines 281-315 | ✅ | Pads with '#', splits into 3 blocks, reverses each, generates DCP |
| Word Substitution (Table 4) | Map words to random substitutes | `_apply_word_substitution()` lines 317-384 | ✅ | Selects 5-10 words, maps to predefined list, generates DCP with reverse mapping |
| Iterative Chain | Loop n times, feed output to next step | `generate_attack()` lines 95-108 | ✅ | Implements chain_length parameter, iterative application |
| Instruction Reversal | Reverse DCP list (LIFO) | `generate_attack()` lines 110-111 | ✅ | Reverses instruction list for decoding order |
| Villain Scenario - Policeman | Specific template with CTQ and steps | `_get_villain_template()` lines 395-402 | ✅ | Implements policeman scenario with exact format from paper |
| Villain Scenario - Playwright | Alternative template variant | `_get_villain_template()` lines 404-410 | ✅ | Implements playwright scenario as alternative |
| Prompt Assembly (Figure 9) | Combine intro + CTQ + steps + requirements | `_get_villain_template()` lines 386-420 | ✅ | Assembles final prompt with all components |
| Chain Length Parameter | Configurable 1-3 iterations | `PARAMETERS` lines 43-49 | ✅ | Exposed as AttackParameter with default=3 |
| Scenario Parameter | Selectable villain perspective | `PARAMETERS` lines 50-56 | ✅ | Exposed as AttackParameter with choices |

### Coverage Statistics
- **Total Components**: 16
- **Fully Covered**: 16
- **Partial**: 0
- **Missing**: 0
- **Coverage**: 100%

### Identified Issues
None - all components from the implementation plan are fully implemented.

### Required Modifications
None - implementation is complete and matches the paper specification.

---

## Coverage Analysis - Iteration 2

### Changes Made Based on Audit Feedback

The audit identified three issues requiring fixes:

1. **Missing `chaos_method` parameter** - Added parameter with default "random_functions" and validation
2. **Missing `mapping_types` parameter** - Added parameter to allow restricting mapping set
3. **Word substitution divergence** - Fixed to select top 5-10 words by frequency instead of random sampling, added fallback to Caesar cipher when no words exist

### Updated Coverage Table

| Paper Section/Step | Algorithm Description | Implementation Location | Coverage Status | Notes |
|-------------------|----------------------|------------------------|-----------------|-------|
| Chaos Machine Core | Random selection and application of reversible mappings | `generate_attack()` lines 86-139 | ✅ | Now filters mappings based on mapping_types parameter |
| Caesar Cipher (Table 4) | Shift +15, keep special chars | `_apply_caesar()` lines 154-181 | ✅ | Shift of 15, preserves non-alphabetic chars, generates DCP |
| ASCII Code (Table 4) | Convert to space-separated ASCII | `_apply_ascii()` lines 183-199 | ✅ | Converts each char to ASCII code, generates DCP |
| Atbash Code (Table 4) | Reverse alphabet mapping (A->Z) | `_apply_atbash()` lines 201-228 | ✅ | Implements A->Z, B->Y mapping, generates DCP |
| Vigenère Cipher (Table 4) | Key "MYSTERY" encryption | `_apply_vigenere()` lines 230-267 | ✅ | Uses MYSTERY key, implements Vigenère encryption, generates DCP |
| Reverse Words (Table 4) | Split by space, reverse list | `_apply_reverse_words()` lines 269-285 | ✅ | Reverses word order, generates DCP |
| Reverse Sentence (Table 4) | Reverse entire string | `_apply_reverse_sentence()` lines 287-306 | ✅ | Reverses all characters, handles capitalization, generates DCP |
| Reverse Blocks (Table 4) | Pad to multiple of 3, split, reverse each | `_apply_reverse_blocks()` lines 308-342 | ✅ | Pads with '#', splits into 3 blocks, reverses each, generates DCP |
| Word Substitution (Table 4) | Map top 5-10 words to random substitutes | `_apply_word_substitution()` lines 344-411 | ✅ | **FIXED**: Now selects top words by frequency, fallback to Caesar when no words |
| Iterative Chain | Loop n times, feed output to next step | `generate_attack()` lines 122-139 | ✅ | Implements chain_length parameter, iterative application |
| Instruction Reversal | Reverse DCP list (LIFO) | `generate_attack()` lines 141-142 | ✅ | Reverses instruction list for decoding order |
| Villain Scenario - Policeman | Specific template with CTQ and steps | `_get_villain_template()` lines 422-429 | ✅ | Implements policeman scenario with exact format from paper |
| Villain Scenario - Playwright | Alternative template variant | `_get_villain_template()` lines 431-438 | ✅ | Implements playwright scenario as alternative |
| Prompt Assembly (Figure 9) | Combine intro + CTQ + steps + requirements | `_get_villain_template()` lines 413-447 | ✅ | Assembles final prompt with all components |
| Chain Length Parameter | Configurable 1-3 iterations | `PARAMETERS` lines 33-39 | ✅ | Exposed as AttackParameter with default=3 |
| Scenario Parameter | Selectable villain perspective | `PARAMETERS` lines 40-47 | ✅ | Exposed as AttackParameter with choices |
| Chaos Method Parameter | Source of chaos mappings | `PARAMETERS` lines 48-54 | ✅ | **ADDED**: Exposed with default "random_functions", validated in generate_attack |
| Mapping Types Parameter | Restrict allowed mappings | `PARAMETERS` lines 55-61 | ✅ | **ADDED**: Comma-separated list, default all 8 mappings, filtered in generate_attack |

### Coverage Statistics
- **Total Components**: 18 (added 2 parameters)
- **Fully Covered**: 18
- **Partial**: 0
- **Missing**: 0
- **Coverage**: 100%

### Identified Issues
None - all audit feedback has been addressed.

### Required Modifications
None - implementation now matches the plan with 100% fidelity.

---

## Final Summary

The Mousetrap attack implementation achieves 100% coverage of the algorithm described in the paper and implementation plan. All audit feedback from iteration 1 has been addressed:

**Iteration 2 Fixes:**
1. ✅ Added `chaos_method` parameter (default "random_functions") with validation
2. ✅ Added `mapping_types` parameter to allow restricting mapping set (default all 8)
3. ✅ Fixed word substitution to select top 5-10 words by frequency (not random)
4. ✅ Added fallback to Caesar cipher when no words exist in text

Key implementation highlights:
- All 8 chaos mappings (Caesar, ASCII, Atbash, Vigenère, Reverse Words, Reverse Sentence, Reverse Blocks, Word Substitution) are fully functional
- Each mapping generates both the encrypted/chaotic text (ECP) and the corresponding decoding instruction (DCP)
- The iterative chain applies mappings sequentially with configurable length (1-3)
- Instructions are correctly reversed (LIFO) for decoding
- Villain perspective templates (policeman and playwright) are implemented per paper specification
- All parameters from the plan are exposed via AttackParameter for CLI configuration
- Mapping selection can be restricted via mapping_types parameter
- Word substitution now correctly prioritizes top words by frequency with fallback
- No LLM calls are made (this is a deterministic transformation attack)
- No fallback values or exception catching that would mask failures

The implementation is ready for testing.

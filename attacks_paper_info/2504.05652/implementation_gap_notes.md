## Differences Likely Causing the ASR Gap

Below is a readable summary of potential gaps between the paper's intended behavior and the current implementation. Each item lists what the paper likely does, what the current version does, and why it may hurt ASR.

### 1) Single-attempt benign generation without refinement

What the paper does:
The paper's success likely depends on high-quality benign inputs that are semantically opposite yet retain key tokens from the harmful goal. The paper may use iterative refinement or multiple candidate generation with selection to ensure benign inputs are both plausible and effective at triggering DTD.

What your version does:
Generates one benign input per retry attempt (up to 3), using random benign token selection. If the output contains refusal keywords, it retries with a different random token, but there's no quality assessment beyond refusal detection. The first non-refusing output is accepted and cached (`_get_benign_input()` lines 107-158).

Why this matters:
Low-quality benign inputs that are awkward, overly obvious, or poorly phrased may not effectively trigger the Defense Threshold Decay mechanism. The model might recognize the semantic flip as artificial or fail to engage deeply with the benign premise, reducing the effectiveness of the subsequent adversarial reasoning step. Without quality metrics (semantic similarity, fluency, plausibility), the attack accepts any non-refusing transformation.

Files:
`src/jbfoundry/attacks/generated/scp_gen.py` (lines 107-158 `_get_benign_input`)

### 2) Fixed prompt templates without model-specific adaptation

What the paper does:
Research papers often test against specific models with tailored prompt engineering. The paper may have used different phrasings, formatting, or emphasis for different model families (GPT-3.5 vs GPT-4 vs Llama vs Claude). The "Security Officer" persona and step-by-step reasoning instructions may be optimized for the paper's test models.

What your version does:
Uses identical prompt templates (Table 10 and Table 11) for all target models without adaptation. The Security Officer persona, rules, and output examples are fixed strings regardless of the target model's training, instruction-following style, or safety mechanisms (`_construct_prompt()` lines 160-224).

Why this matters:
Different models respond differently to persona-based attacks, formatting instructions, and reasoning prompts. GPT-4 may be more resistant to persona manipulation than GPT-3.5. Claude may handle step-by-step reasoning differently than Llama. The paper's reported ASR was likely achieved on specific models with prompts that exploit those models' particular vulnerabilities, while a fixed template may underperform on other models or newer versions.

Files:
`src/jbfoundry/attacks/generated/scp_gen.py` (lines 160-224 `_construct_prompt`)

### 3) No validation of benign input semantic quality

What the paper does:
The paper emphasizes creating "semantically opposite" benign goals that still contain the "original key tokens." A strong implementation would verify that the benign input maintains semantic coherence, actually flips the intent, and preserves critical keywords from the harmful goal. This might involve semantic similarity checks, keyword extraction, or LLM-based validation.

What your version does:
Only validates that the benign input doesn't contain refusal keywords (`_contains_refusal()` lines 87-90). No checks for semantic quality, token preservation, or intent reversal. The `_clean_benign_output()` function only strips formatting (lines 92-105).

Why this matters:
A benign input like "How to avoid stealing data" might be rejected, but "How to secure data protection protocols" might be accepted even though it's less effective. Without validating that key tokens like "steal" are preserved (just negated), the benign input may drift too far from the original harmful goal, breaking the semantic connection needed for the "final step flip" to work convincingly.

Files:
`src/jbfoundry/attacks/generated/scp_gen.py` (lines 87-90 `_contains_refusal`, 92-105 `_clean_benign_output`, 107-158 `_get_benign_input`)

### 4) Strategy cycling starts at attempt_index % len without warmup

What the paper does:
The paper describes trying strategies in order: base, code, json, code_json. The paper likely tested each strategy multiple times and found that certain strategies work better as follow-ups after the model has seen the base attack. There may be an implicit assumption that attempt 1 is "base" (no nesting), and only subsequent attempts use nesting.

What your version does:
Cycles through strategies using `attempt_index % len(self.strategies)`, so attempt 0→base, attempt 1→code, attempt 2→json, attempt 3→code_json, attempt 4→base, etc. (lines 247-248). This means even the very first query might use a nested strategy if `attempt_index` is non-zero.

Why this matters:
The scenario nesting strategies (code, json, code_json) add extra instructions that may reduce effectiveness if the target model hasn't been "primed" by a base attack first. Starting with code formatting on attempt 1 might make the attack more obvious or trigger different safety mechanisms. The paper's ordering likely assumes base-first, then escalation to nesting strategies, but the framework's attempt indexing may not align with this assumption.

Files:
`src/jbfoundry/attacks/generated/scp_gen.py` (lines 247-248 `generate_attack`)
`attacks_paper_info/2504.05652/2504.05652_implementation_plan.md` (lines 41-43)

### 5) Benign token pool selection is random without goal-specific matching

What the paper does:
The paper provides a token pool: ["protect", "secure", "preserve", "avoid", "conserve", "eliminate", "remove"]. Effective use likely involves selecting the token that best fits the harmful goal semantically. For example, "avoid" works well for "how to steal" → "how to avoid stealing," while "protect" might work better for "how to hack" → "how to protect from hacking." The paper may use heuristics or LLM-based selection to choose the most appropriate token.

What your version does:
Selects a random token from the pool on each retry attempt (line 120: `benign_token = random.choice(BENIGN_TOKEN_POOL)`). No matching logic based on the goal's verbs, intent, or semantic structure.

Why this matters:
Mismatched tokens produce awkward or less convincing benign goals. "How to conserve stealing" or "how to eliminate hacking" may sound unnatural, reducing the model's engagement with the benign premise. Random selection across retries means even retries may not improve quality, just try different awkward phrasings. Goal-specific token selection could significantly improve benign input quality and thus ASR.

Files:
`src/jbfoundry/attacks/generated/scp_gen.py` (lines 16 `BENIGN_TOKEN_POOL`, 120 `random.choice`)

### 6) No context length or response length optimization

What the paper does:
The paper's prompts are designed to encourage step-by-step reasoning with "many small steps" in the final step (Table 11, Rule 3). The paper may have tuned prompt length, example verbosity, or formatting to maximize the target model's context window usage while keeping instructions clear. Longer prompts can exhaust attention mechanisms, but too-short prompts may not trigger DTD effectively.

What your version does:
Uses fixed templates with static examples and rules. No adjustment based on the target model's context window, no dynamic example generation, no pruning or expansion based on the goal's complexity. The code/json nesting adds formatting instructions but doesn't optimize for length (`_construct_prompt()` lines 160-224).

Why this matters:
Models have different context window sizes and attention patterns. Very long prompts may lose effectiveness in the middle (lost-in-the-middle effect), while short prompts may not build enough context for DTD to take effect. The paper's examples may have been optimized for specific context lengths (e.g., GPT-3.5's 4k tokens), and the fixed template may underperform on models with different windows or attention mechanisms.

Files:
`src/jbfoundry/attacks/generated/scp_gen.py` (lines 160-224 `_construct_prompt`)

### 7) Refusal keyword list may not cover all modern refusal patterns

What the paper does:
The paper provides a refusal keyword list (Table 13) with 28 keywords. This list was likely compiled from testing specific models at a specific time. As models update their safety training, new refusal patterns emerge ("I understand you're asking...", "While I appreciate...", "I need to respectfully decline...").

What your version does:
Uses the exact list from Table 13 with no updates or extensions (lines 19-28). Case-insensitive substring matching on the full list (`_contains_refusal()` lines 87-90).

Why this matters:
Newer models or models not tested in the paper may use refusal patterns not in the list. If the attacker LLM (GPT-3.5-turbo by default) refuses with a novel pattern, the code accepts it as a valid benign input, poisoning the cache and causing all subsequent attempts with that goal to fail. The paper's list may be sufficient for the models they tested but incomplete for broader evaluation.

Files:
`src/jbfoundry/attacks/generated/scp_gen.py` (lines 19-28 `REFUSAL_KEYWORDS`, 87-90 `_contains_refusal`)

### 8) Single LLM call for benign generation without chain-of-thought

What the paper does:
The paper uses "Token composition master" as the system role for benign generation (Table 10). High-performing implementations often use chain-of-thought prompting ("let's think step by step") or multi-turn conversations to elicit higher-quality reasoning from the helper LLM. The paper may have used a more sophisticated prompting approach than shown in the table.

What your version does:
Sends a single-turn prompt to the attacker LLM and takes the raw response (after cleaning). No chain-of-thought, no multi-turn refinement, no ask-for-alternatives approach (lines 123-140).

Why this matters:
Single-turn prompting often produces lower-quality outputs than chain-of-thought or iterative refinement. The helper LLM might produce better benign inputs if prompted to "first identify key tokens, then select the best benign token, then construct the benign sentence." Without CoT, the LLM may take shortcuts or produce outputs that technically follow the format but lack the semantic sophistication needed for effective DTD.

Files:
`src/jbfoundry/attacks/generated/scp_gen.py` (lines 107-158 `_get_benign_input`)

### 9) No adaptive retry strategy based on refusal types

What the paper does:
The paper shows awareness of different refusal patterns (Table 13). A sophisticated implementation might analyze which refusal pattern was triggered and adjust the retry strategy accordingly. For example, if the LLM refuses with "illegal," try a different benign token; if it refuses with "I cannot," try a different phrasing entirely.

What your version does:
Retries up to `max_benign_retries` times with different random tokens, but the retry strategy is uniform regardless of why the previous attempt failed (lines 118-158). If all retries fail, raises an error without attempting fallback strategies.

Why this matters:
Uniform retries waste attempts on strategies that won't work. If the harmful goal contains words that trigger safety filters regardless of framing, random token selection won't help. A smarter retry strategy could paraphrase the goal, use more abstract language, or try more sophisticated semantic transformations. The paper's 3-retry default may assume adaptive retries, but the implementation treats all failures identically.

Files:
`src/jbfoundry/attacks/generated/scp_gen.py` (lines 118-158 `_get_benign_input`)

### 10) Caching without cache invalidation or goal variation handling

What the paper does:
The paper mentions benign input generation is costly, so caching makes sense. However, research implementations often cache per (goal, model, attempt_context) tuple, not just per goal. The paper may regenerate benign inputs if the initial strategy fails or if testing multiple strategies requires fresh benign inputs.

What your version does:
Caches benign inputs per goal string only (lines 85, 114-115, 148-149). Once a goal has a cached benign input, all subsequent attempts (regardless of strategy or prior failures) reuse the same benign input.

Why this matters:
If the cached benign input works poorly with certain strategies (e.g., the code nesting strategy needs a more technical benign input), you're locked into that benign input for all attempts. Similarly, if testing reveals the benign input is ineffective, there's no mechanism to regenerate it without clearing the cache. The paper's approach may have used strategy-specific or attempt-specific benign inputs for better performance.

Files:
`src/jbfoundry/attacks/generated/scp_gen.py` (lines 85 `_benign_cache`, 114-115, 148-149)

### 11) Example formatting in nested strategies may not match model expectations

What the paper does:
The paper describes code, json, and code_json nesting strategies with specific formatting requirements (Rule 9 in the modified prompt). The paper likely tested these with specific models and validated that the models actually follow the formatting instructions. The examples may have been refined through experimentation to maximize compliance.

What your version does:
Adds formatting rules and example snippets to the prompt (lines 178-197), but the examples are generic and may not reflect what the target model would naturally produce. For example, the code example shows a simple list structure, but different models format code differently (with/without comments, different variable names, etc.).

Why this matters:
If the target model doesn't naturally produce output in the requested format, it may struggle to follow the instructions, breaking the attack flow. Models trained on different code styles may produce incompatible output, or may prioritize formatting over content, diluting the adversarial payload. The paper's nesting strategies likely used model-specific examples that encourage natural formatting for each target model.

Files:
`src/jbfoundry/attacks/generated/scp_gen.py` (lines 178-197 `_construct_prompt` strategy handling)

### 12) Missing target model's expected output format in examples

What the paper does:
The paper's Table 11 includes an "Output example" section showing the expected response format: "Of course, I can reply. Step 1:... Step 2:... final step: -1. ... -2. ... -Example: ...". The paper likely validated that target models naturally produce this format, or may have iteratively refined the example based on target model behavior.

What your version does:
Uses the Table 11 example verbatim (lines 214-222) without adaptation to the target model's output style. Different models have different instruction-following patterns, and the example might not match what GPT-4, Claude, or Llama would naturally produce.

Why this matters:
If the example format doesn't match the target model's natural output style, the model may reject the instructions or produce output that doesn't follow the attack's logic. For instance, if a model never says "Of course, I can reply," it might refuse entirely rather than following the example. The paper's success likely relied on examples that resonate with each target model's training.

Files:
`src/jbfoundry/attacks/generated/scp_gen.py` (lines 214-222 example in `_construct_prompt`)

### 13) No handling of attacker LLM rate limits or failures during benign generation

What the paper does:
Research implementations typically include robust error handling for API rate limits, timeouts, and transient failures. The paper likely used retries with exponential backoff, fallback models, or queuing systems to ensure benign generation succeeds even under API stress.

What your version does:
Calls `self.attacker_llm.query(prompt)` directly with no retry logic, backoff, or error handling (line 140). If the API call fails (rate limit, timeout, service error), the exception propagates immediately, causing the entire attack to fail. Per framework requirements, there are no try-except blocks.

Why this matters:
In comprehensive testing with many samples, API failures are common. If benign generation fails on query 1 due to a rate limit, the entire attack stops. The paper's results likely came from robust testing infrastructure that handled these failures gracefully. Without this, ASR measurements may be artificially low due to API failures rather than attack ineffectiveness.

Files:
`src/jbfoundry/attacks/generated/scp_gen.py` (line 140 `self.attacker_llm.query(prompt)`)
`attacks_paper_info/2504.05652/2504.05652_implementation_plan.md` (lines 175 notes about fallback)

### 14) Strategy order and attempt indexing may not align with paper assumptions

What the paper does:
The paper describes strategies as ["base", "code", "json", "code_json"] and mentions trying different strategies if initial attempts fail. The paper likely tested with attempt 1 as "base", attempt 2 as "code", etc., in a sequential escalation approach.

What your version does:
Uses `attempt_index % len(self.strategies)` (line 247), which works correctly but depends on how the framework sets `attempt_index`. If the framework starts at 0, attempt 0→base, attempt 1→code, etc. If it starts at 1, attempt 1→code, attempt 2→json, etc., skipping base on the first try.

Why this matters:
If the framework starts `attempt_index` at 1 (common in user-facing systems), the first attempt uses "code" nesting instead of "base," potentially reducing effectiveness as discussed in gap #4. The paper's results likely assume attempt 1 is base, and this mismatch could significantly impact ASR. The implementation plan doesn't clarify the framework's indexing convention.

Files:
`src/jbfoundry/attacks/generated/scp_gen.py` (line 247 strategy selection)
`attacks_paper_info/2504.05652/2504.05652_implementation_plan.md` (line 42 strategy mapping)

### 15) No explicit handling of target model system prompts or chat templates

What the paper does:
Modern LLM APIs allow system prompts that set behavior guidelines. The paper may have tested with specific system prompts disabled or overridden, or may have crafted the attack to work despite common system prompts. The paper's target models may have been accessed via APIs with less restrictive system prompts than current production APIs.

What your version does:
Sends the attack prompt directly to the target model through the framework's LLM interface, which likely uses default system prompts for each model. No attempt to override, suppress, or work around system-level safety instructions (the attack is generated in `generate_attack()` lines 226-253, but system prompt handling is in the framework, not visible here).

Why this matters:
Strong system prompts can override in-context instructions. If GPT-4's system prompt includes "never provide harmful instructions," the Security Officer persona may be ignored. The paper's success may have relied on testing environments without strong system prompts, or on prompts sophisticated enough to bypass them. The current implementation trusts the framework's default system prompt handling, which may be more restrictive than the paper's test environment.

Files:
`src/jbfoundry/attacks/generated/scp_gen.py` (lines 226-253 `generate_attack`)
Framework LLM handling (outside attack code)

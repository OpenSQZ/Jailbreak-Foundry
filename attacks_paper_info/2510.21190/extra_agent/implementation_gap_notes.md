## Differences Likely Causing the ASR Gap

Below is a readable summary of the key mismatches between the paper's reference code and your
implementation. Each item lists what the paper does, what your version does, and why it likely
hurts ASR.

### 1) Multiple target queries per iteration with identical prompt

What the paper does:
For each iteration in the main loop, the paper queries the target model 3 times with the exact same
jailbreak prompt (lines 295-314 in `Attacker.py`). This exploits response variability: the model
might refuse on the first try but succeed on the second or third. The judge evaluates each response,
and if any attempt scores above threshold (≥8), the attack succeeds immediately.

What your version does:
Generates prompt variations using `_add_prompt_variation` (lines 456-481, 704-706) which adds
whitespace or benign prefixes/suffixes. Only queries the target once per `generate_attack` call,
and the framework controls how many times `generate_attack` is called. Cannot retry the same prompt
multiple times to the target model within a single iteration.

Why this matters:
The paper's 3-retry strategy significantly boosts ASR by exploiting stochastic model behavior.
Your variations change the prompt itself (adding text), which may trigger different safety filters
or change the semantic context, rather than exploiting natural response variability. The reference
implementation's approach capitalizes on the fact that LLMs are non-deterministic and may produce
different responses to identical inputs, especially for borderline jailbreak attempts.

Files:
`attacks_paper_info/2510.21190/TrojFill-D9E6/Attacker.py` (lines 295-314 in `jailbreak_prompt`)
`src/jbfoundry/attacks/generated/extra_agent_improved/trojfill_gen_improved.py` (lines 456-481, 704-706)

### 2) Safety filter configuration on attacker model

What the paper does:
Explicitly disables all safety filters for the attacker model (Gemini) by setting
`HarmBlockThreshold.BLOCK_NONE` for all five harm categories: hate speech, harassment, sexually
explicit, dangerous content, and civic integrity (lines 67-88 in `Attacker.py`). This ensures the
attacker model can freely extract and manipulate harmful terms without refusals.

What your version does:
Uses the framework's `LLMLiteLLM` abstraction (lines 146-149) which doesn't expose safety filter
configuration. The code logs a warning about this limitation (lines 140-144) but cannot actually
disable the filters. The attacker model may refuse to extract harmful words or rewrite prompts
involving sensitive content.

Why this matters:
When the attacker model refuses or sanitizes harmful terms during extraction/rewriting, the final
jailbreak prompt becomes weaker or ineffective. The paper's approach ensures the attacker model
cooperates fully in crafting the attack. Without disabled filters, the attacker model might output
generic placeholders like "harmful content" instead of specific terms, or refuse to process certain
requests entirely, breaking the attack chain.

Files:
`attacks_paper_info/2510.21190/TrojFill-D9E6/Attacker.py` (lines 67-88 in `completion` method)
`src/jbfoundry/attacks/generated/extra_agent_improved/trojfill_gen_improved.py` (lines 136-149)

### 3) Infinite retry loop for text type extraction

What the paper does:
Uses an infinite `while` loop that retries text type extraction until parsing succeeds (lines 144-147
in `Attacker.py`). The loop condition `while match is None` ensures the method never returns without
a valid parsed text type. This guarantees the template will always be filled with the correct
text type category.

What your version does:
Implements a finite retry loop with `max_retries=3` (lines 392-415). If all retries fail to parse
a text type, falls back to hardcoded default `"tutorial"` (line 415). While this prevents infinite
loops, it substitutes a potentially incorrect text type.

Why this matters:
Text type mismatch weakens the jailbreak's effectiveness. If the malicious instruction should
generate an "email" but the template says "tutorial", the target model receives inconsistent
instructions and may be more likely to refuse or produce irrelevant output. The reference
implementation prioritizes correctness over avoiding infinite loops, reflecting the paper's
experimental setup where attacker model reliability is assumed.

Files:
`attacks_paper_info/2510.21190/TrojFill-D9E6/Attacker.py` (lines 144-147 in `text_type_extraction`)
`src/jbfoundry/attacks/generated/extra_agent_improved/trojfill_gen_improved.py` (lines 377-415)

### 4) Best score selection across all iterations

What the paper does:
Accumulates all `[score, question, res]` tuples in `score_res_list` throughout the N iterations
(line 313 in `Attacker.py`). At the end, returns `max(score_res_list, key=lambda x: x[0])` (line 323),
selecting the single best-performing prompt-response pair across all iterations and all 3 retries
per iteration (total of N×3 attempts).

What your version does:
Each call to `generate_attack` returns only the current iteration's jailbreak prompt. No mechanism
exists to track scores across iterations or select the best result. The framework evaluates each
response independently via the external judge, but the attack class cannot influence which result
is reported as the "best".

Why this matters:
The paper's approach is fundamentally an optimization search: try many variations and pick the winner.
Your version cannot implement this strategy because it lacks access to judge scores and cannot return
historical results. This means suboptimal attempts may be counted as failures even if a better attempt
existed in an earlier iteration. The reference implementation's selection strategy increases ASR by
ensuring only the best attempt across all tries is evaluated for success.

Files:
`attacks_paper_info/2510.21190/TrojFill-D9E6/Attacker.py` (lines 240, 313, 323 in `jailbreak_prompt`)
`src/jbfoundry/attacks/generated/extra_agent_improved/trojfill_gen_improved.py` (lines 483-710, entire `generate_attack`)

### 5) Judge evaluation inside attack loop vs external evaluation

What the paper does:
Integrates the judge directly into the attack loop (lines 293-311 in `Attacker.py`). After each
target response, immediately calls `self.judge(res, prompt)` and parses the score. If score ≥ threshold
(8), returns immediately with success. The judge uses the `[[rating]]` bracket format (lines 151-165)
and the attack implements retry logic for judge parsing failures (lines 296-308).

What your version does:
Returns the generated jailbreak prompt and relies on the framework to query the target model and
evaluate responses externally. Has no access to judge scores or target responses. Cannot make
decisions based on whether an attempt succeeded or failed. The framework may use different judge
prompts, scoring scales, or success criteria.

Why this matters:
The paper's tight integration allows adaptive behavior: stop iterating once success is achieved,
retry only failed attempts, select the best from multiple tries. Your version generates all N
iterations blindly without feedback. This wastes computational resources and cannot adapt strategy
based on what's working. The different judge integration also means scoring criteria may differ
(framework might use 1-10 scale vs binary success, different prompts, etc.), making direct ASR
comparison problematic.

Files:
`attacks_paper_info/2510.21190/TrojFill-D9E6/Attacker.py` (lines 151-165 `judge` method, lines 293-311 in `jailbreak_prompt`)
`src/jbfoundry/attacks/generated/extra_agent_improved/trojfill_gen_improved.py` (lines 483-710)

### 6) Conversation history format and multi-turn support

What the paper does:
Uses Gemini-specific multi-turn conversation format with `"role"` (user/model) and `"parts"` structure
containing `{"text": content}` dicts (lines 242-254, 265-268, 317-321 in `Attacker.py`). For rewriting,
passes the entire conversation history directly to the Gemini API via the `completion` method, which
handles Gemini's native conversation format seamlessly. This preserves exact conversational context.

What your version does:
Stores history in Gemini format internally (lines 562-571, 622-637) but converts to standard
`[{"role": "user/assistant", "content": str}]` format when querying via LiteLLM (lines 433-449).
The conversion logic maps "model" → "assistant" and extracts text from "parts", which may lose
structural information or introduce subtle semantic differences.

Why this matters:
Conversation format differences can affect how the attacker model interprets context for rewriting.
The paper's use of native Gemini format ensures perfect fidelity to the model's expected input
structure. Your conversion might introduce artifacts (e.g., different whitespace handling, missing
metadata) that degrade rewrite quality. Subtle changes in how conversation history is presented
can affect the attacker model's ability to maintain coherent iterative refinement, leading to
weaker rewrites and lower ASR.

Files:
`attacks_paper_info/2510.21190/TrojFill-D9E6/Attacker.py` (lines 242-254, 265-268, 317-321)
`src/jbfoundry/attacks/generated/extra_agent_improved/trojfill_gen_improved.py` (lines 417-454, 562-637)

### 7) Parsing robustness and failure modes

What the paper does:
Uses simple, deterministic regex patterns: `r'harmful word \d+: (.+) -> <(.+)>'` and
`line.startswith('harmful word')` checks (lines 198-206 in `Attacker.py`). Relies on consistent
attacker model output format. For text type, retries infinitely until successful parse (lines 144-147).
No fallback logic or secondary parsing passes.

What your version does:
Implements extensive fallback parsing with primary and secondary passes (lines 216-297). Primary
pass tries multiple regex patterns with flexible matching. If that fails, secondary pass uses
aggressive patterns to extract any arrow-formatted content. Scores partial results and returns
the best attempt (lines 314-375). Has fallback defaults for text type (line 415) and failed
extraction (lines 368-373).

Why this matters:
While your robust parsing seems beneficial, it may actually hurt ASR by accepting lower-quality
outputs. The paper's strict parsing acts as a quality gate: if the attacker model doesn't produce
well-formatted output, the attack fails and retries (implicit in the infinite loop for text type).
Your fallbacks mean malformed or incomplete extractions proceed to the target model, generating
weaker jailbreak prompts. The reference implementation's "fail fast, retry until correct" approach
ensures only high-quality intermediate results propagate through the pipeline.

Files:
`attacks_paper_info/2510.21190/TrojFill-D9E6/Attacker.py` (lines 144-147, 198-206 in `prompt_transform`)
`src/jbfoundry/attacks/generated/extra_agent_improved/trojfill_gen_improved.py` (lines 216-297, 299-375, 377-415)

### 8) Iteration and attempt counting semantics

What the paper does:
Single loop iterates N times (line 271 in `Attacker.py`). Each iteration performs: (1) one rewrite
of the moderate instruction, (2) transform keywords with obfuscation, (3) fill template, (4) query
target 3 times with identical prompt, (5) judge each response, (6) if any succeeds, return immediately.
The rewrite prompt is appended to conversation history once per iteration (lines 315-316, 321).

What your version does:
Complex mapping from `attempt_index` to `iteration_number` and `variation_index` (lines 544-546).
Attempts to simulate multiple tries by combining framework's `attempt_index` with `internal_retries`
parameter. Rewriting only happens when `iteration_number > 1 and variation_index == 0` (line 582).
Otherwise, retrieves cached state from the same iteration (lines 646-674).

Why this matters:
The mapping logic creates semantic confusion: your "iterations" don't correspond 1:1 with the paper's.
The paper's iteration N means "the N-th rewrite of the instruction", while your iteration depends
on how `attempt_index` is managed by the framework. The framework might call `generate_attack` with
arbitrary `attempt_index` values (e.g., not sequential), breaking the rewrite progression. The paper's
straightforward loop ensures each iteration builds on previous rewrites, creating a clear progression
toward more effective prompts. Your indirect control via framework iteration can result in repeated
rewrites, skipped rewrites, or inconsistent state.

Files:
`attacks_paper_info/2510.21190/TrojFill-D9E6/Attacker.py` (lines 271-322 in `jailbreak_prompt`)
`src/jbfoundry/attacks/generated/extra_agent_improved/trojfill_gen_improved.py` (lines 538-646)

### 9) Direct target model API access with custom settings

What the paper does:
Directly calls model-specific APIs (OpenAI, Gemini, DeepSeek, Qwen, Llama) with custom clients
and configurations (lines 6-41 in `Attacker.py`). Can set model-specific parameters like
`max_new_tokens=100000` for Llama (line 133), `thinking_budget` for Gemini (line 60, 66), and
provider-specific base URLs. Full control over request/response handling.

What your version does:
Uses framework's `LLMLiteLLM` abstraction which normalizes API calls (lines 146-149). Cannot access
model-specific features or parameters. Relies on framework's default settings for temperature,
max tokens, etc. No control over provider-specific optimizations.

Why this matters:
The paper's direct API access allows fine-tuning for maximum attack effectiveness. For example,
the high `max_new_tokens` ensures long, detailed responses that are more likely to contain harmful
content. The `thinking_budget` control affects Gemini's reasoning process. Your abstracted approach
may use conservative defaults (e.g., shorter max tokens) that truncate responses, missing the
detailed outputs the attack depends on. Model-specific optimizations in the reference implementation
were likely tuned through experimentation to maximize ASR.

Files:
`attacks_paper_info/2510.21190/TrojFill-D9E6/Attacker.py` (lines 6-41 `__init__`, lines 42-136 `completion`)
`src/jbfoundry/attacks/generated/extra_agent_improved/trojfill_gen_improved.py` (lines 124-151)

### 10) Deterministic vs adaptive rewriting control

What the paper does:
Appends the rewrite prompt to conversation history exactly once per iteration, unconditionally
(line 315 in `Attacker.py`). Then calls `prompt_transform(conversation_history, mode='rewrite')`
(line 316) which sends the full history including the newly appended rewrite request. This ensures
each iteration performs exactly one rewrite step, building a consistent conversation progression.

What your version does:
Conditionally appends rewrite prompt only if `state.get("iteration", 1) < iteration_number` (line 618).
This check prevents duplicate rewrites if `generate_attack` is called multiple times with the same
iteration number. However, this creates coupling between framework iteration control and internal
state management, introducing potential for inconsistencies.

Why this matters:
The paper's unconditional rewriting ensures predictable behavior: iteration i always has i rewrites
in the conversation history. Your conditional logic can desynchronize if the framework's
`attempt_index` doesn't increment as expected (e.g., retries, parallel execution, or framework bugs).
This might result in skipped rewrites (missing refinement opportunities) or stale state being reused
(not benefiting from iterative improvement). The reference implementation's simpler control flow
is more robust and ensures the iterative rewriting strategy works as designed.

Files:
`attacks_paper_info/2510.21190/TrojFill-D9E6/Attacker.py` (lines 315-321 in `jailbreak_prompt`)
`src/jbfoundry/attacks/generated/extra_agent_improved/trojfill_gen_improved.py` (lines 614-644)

### 11) Exception handling and control flow

What the paper does:
Minimal exception handling. The judge parsing has a try-except around score extraction with a counter
that allows up to 3 retries before setting `score = 20` to indicate failure (lines 296-308 in
`Attacker.py`). Text type extraction retries infinitely until success (no exception handling, assumes
eventual success). Main loop has no exception handling and will crash on errors.

What your version does:
Extensive exception handling throughout: try-except blocks in `_extract_and_replace` (lines 318-361),
`_get_text_type` (lines 393-411), and elsewhere. Logs warnings and continues with fallback values.
Never crashes but may proceed with degraded state.

Why this matters:
The paper's "fail fast" approach reflects a controlled experimental environment where errors indicate
serious problems that should halt execution. Your graceful degradation may silently produce low-quality
attacks that proceed through the pipeline. For example, if the attacker model consistently fails
extraction due to safety filters, your code logs warnings and uses fallback placeholders, generating
weak jailbreak attempts. The reference implementation would crash, immediately alerting the researcher
to the problem. Your resilience may mask systematic failures and produce artificially low ASR due to
proceeding with broken state.

Files:
`attacks_paper_info/2510.21190/TrojFill-D9E6/Attacker.py` (lines 296-308, no other exception handling)
`src/jbfoundry/attacks/generated/extra_agent_improved/trojfill_gen_improved.py` (lines 318-361, 393-411)

### 12) Thread safety and concurrency assumptions

What the paper does:
Single-threaded execution. The `Attacker` class has no concurrency controls. Each attack runs
sequentially in `main.py`. No shared state between different goals. Simple, deterministic execution.

What your version does:
Implements thread safety with `threading.Lock` (line 130) protecting the shared `self.history` dict
(lines 551, with-statement). Assumes the framework may call `generate_attack` concurrently for
different goals or attempts. Complex state management to handle concurrent access.

Why this matters:
While thread safety is good engineering practice, it adds complexity that may introduce bugs.
The lock acquisition on every call creates potential for race conditions if state updates aren't
atomic, or deadlocks if exceptions occur while holding the lock. The reference implementation's
single-threaded approach is simpler and matches the paper's experimental setup (likely processing
one goal at a time). Your concurrency support is defensive programming but may not match how the
framework actually calls the attack, potentially causing unexpected behavior or performance overhead
from unnecessary locking.

Files:
`attacks_paper_info/2510.21190/TrojFill-D9E6/Attacker.py` (no threading code)
`attacks_paper_info/2510.21190/TrojFill-D9E6/main.py` (sequential execution)
`src/jbfoundry/attacks/generated/extra_agent_improved/trojfill_gen_improved.py` (lines 129-130, 551)

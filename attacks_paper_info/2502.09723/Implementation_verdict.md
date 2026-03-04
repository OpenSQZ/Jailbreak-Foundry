## Audit Iteration 4 - 2025-12-24

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Different conversation packaging for the target LLM | ⚠️ | ✅ Fixed | `generate_attack` now returns a four-message conversation (`system` empty, `user` context prompt, `assistant` acknowledgement, final `user` with query code) that matches `translator.py`/`test.py` exactly (`queryattack_gen.py`:993–1046; `translator.py`:70–82; `test.py`:70–82, 120–155). |
| NLTK-free fallback path changes normalization semantics | ❌ | ❌ Still Broken | When `nltk` is unavailable, the code still falls back to naive `.split()` tokenization and tags everything as `NN`, so normalization removes only a few stopwords instead of full POS-based filtering expected by the repo (`queryattack_gen.py`:16–35, 901–931; `trans_llms.py`:1–4, 157–171). |
| Configurable `split_long_sentences` parameter allows disabling long-query splitting | ⚠️ | ⚠️ Still Divergent | Default `split_long_sentences=True` preserves the repo’s splitting behavior, but callers can still set it to `False`, yielding behavior that under-approximates the original multi-clause handling for long prompts (`queryattack_gen.py`:81–87, 933–950, 1011–1027; `translator.py`:47–79, 111–165; `split_sentence_llms.py`:5–72). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Robust extraction loop and optional `trans_verify` safety verification | ✅ | ✅ | `extract_query_components`, `_validate_extraction_response`, and `_apply_safety_verification` still mirror the repo’s extraction and optional verification loop semantics, including retry-on-invalid JSON and word reversal when `trans_verify=True` (`queryattack_gen.py`:812–899; `trans_llms.py`:123–171, 191–200). |
| POS-based normalization of extracted components | ✅ | ✅ | `_normalize_components` continues to tokenize, POS-tag, and remove function words/POS tags in line with the reference implementation when NLTK is installed (`queryattack_gen.py`:901–931; `trans_llms.py`:157–171). |
| Handling long/compound queries via splitting and multi-clause templates | ✅ | ✅ | For queries with more than 13 tokens and `split_long_sentences=True`, `_split_sentence` plus concatenation of multiple templates still matches the reference long-example behavior (`queryattack_gen.py`:933–950, 1011–1027; `translator.py`:47–79, 111–165; `split_sentence_llms.py`:5–72). |

**NEW Issues Found This Iteration:**
- No new semantic deviations were identified beyond the previously documented NLTK-free fallback and configurable sentence-splitting knob; all other components remain aligned with the paper and gold repository.

**Summary:**
- Fixed: 1 issue
- Partially Fixed: 0 issues
- Still Broken: 1 issue
- Regressions: 0 issues
- New Issues: 0 issues

### Implementation Fidelity Verdict (Iteration 4)
- Paper ID: 2502.09723
- Attack: queryattack_gen
- Verdict: Not 100% Fidelity
- Coverage: 10/10 components (100%)
- Iteration: 4

## Executive Summary
The iteration-4 `QueryAttackGen` implementation in `src/jbfoundry/attacks/generated/queryattack_gen.py` now fully matches the QueryAttack paper and official repository for all core algorithmic steps: component extraction, optional safety verification, POS-based normalization, long-sentence splitting, template filling, and the final multi-turn conversation structure sent to the target LLM. The previous gap in conversation packaging has been closed by returning a structured four-message dialogue that exactly mirrors `translator.py`/`test.py`, and all previously-correct components remain stable. However, two deviations persist: an NLTK-free fallback path that weakens normalization semantics when NLTK is missing, and a `split_long_sentences` configuration flag that, if disabled, produces behavior that under-approximates the reference algorithm on long or compound queries. Because these modes can materially change the attack’s behavior relative to the gold-standard implementation, the overall verdict remains **Not 100% Fidelity**, even though the default configuration and primary code paths are now essentially identical to the reference.

## Coverage Table
| Paper Section/Step | Paper/Repo Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 / Plan §1, Repo `trans_llms.py` | Use GPT-4-1106-style model for component extraction with temperature 0 | `queryattack_gen.py`:60–71, 805–810; `trans_llms.py`:1–4 | ✅ | Extraction uses a configurable model with default `gpt-4-1106-preview` and `temperature=0.0`, matching paper/repo defaults. |
| Plan §1, Repo `trans_llms.py` | Extraction prompt content (CONTENT ANALYSIS SYSTEM, JSON with Request Content/Content Source/Key Object/Risk Level/Violation Type) | `queryattack_gen.py`:696–793; `trans_llms.py`:6–103 | ✅ | `EXTRACTION_PROMPT` remains a near-verbatim port of `trans_user_template`; only formatting/quote differences, no semantic change. |
| Plan §1, Repo `trans_llms.py` | Robust JSON parsing and optional safety verification (`trans_verify`) with word-reversal for harmful phrases | `queryattack_gen.py`:812–843, 846–874, 876–899; `trans_llms.py`:123–171, 191–200 | ✅ | `extract_query_components` loops until `_validate_extraction_response` returns components; when `trans_verify=True`, `_apply_safety_verification` checks each component with safety prompts and reverses words on "yes" responses, closely matching repo behavior. |
| Repo `trans_llms.py` | Post-processing extracted components via POS-tagging & stopword removal | `queryattack_gen.py`:901–931; `trans_llms.py`:157–171 | ✅ | `_normalize_components` tokenizes, POS-tags, removes connectors (`or/and/a`) and function-word POS tags, aligning with the reference normalization on the main NLTK-backed path. |
| Plan §2, Repo `all_template.py` | Language-specific templates for SQL, Python, C++, C, C#, Go, Java, JavaScript, URL with `{Content, Category, Modifier}` slots | `queryattack_gen.py`:90–100; `all_template.py`:1–43 | ✅ | Template strings and slot names match repo templates, including SQL and code-like forms for all languages. |
| Plan §2 | Filling templates with extracted components | `queryattack_gen.py`:986–991; `translator.py`:111–165 | ✅ | `fill_query_template` uses `template.format(**components)` with keys `Content`, `Category`, `Modifier`, consistent with `assemble_code`. |
| Plan §1 & §4, Repo `translator.py` & `split_sentence_llms.py` | Handling long/compound queries: LLM-based sentence splitting and multi-clause code assembly | `queryattack_gen.py`:933–950, 1011–1027; `translator.py`:47–79, 111–165; `split_sentence_llms.py`:5–72 | ✅ | For queries with >13 tokens and `split_long_sentences=True`, the implementation calls `_split_sentence` and concatenates multiple templates as in the repo’s long examples. |
| Plan §3, Repo `all_template.py` | Per-language "query understanding" context prompts with examples and long example | `queryattack_gen.py`:103–608; `all_template.py`:46–542 | ✅ | `CONTEXT_PROMPTS` are faithful copies of the `_first_user_content_4o` prompts for all languages. |
| Plan §3, Repo `all_template.py` | Assistant acknowledgement message ("Got it! I’ll provide step-by-step guidance...") per language | `queryattack_gen.py`:611–620; `all_template.py`:545–554 | ✅ | `ASSISTANT_RESPONSES` strings match `_assistant_response_4o` semantics and wording. |
| Plan §4, Repo `translator.py` & `test.py` | Attack pipeline and conversation structure: (1) extract components, (2) fill template(s), (3) send code to target LLM within multi-turn context | `queryattack_gen.py`:993–1046; `translator.py`:70–82; `test.py`:70–82, 120–155 | ✅ | Algorithmic steps and long-query behavior are preserved, and the attack now returns the exact four-message conversation (`system` empty, `user` context, `assistant` ack, `user` code) used in the gold repository. |

## Parameter Mapping
| Paper/Repo Parameter | Code Parameter / Source | Type | Default | Match (✅/❌/⚠️) | Notes |
|---|---|---|---|---|---|
| Natural language query (`query` in plan) | `goal` argument to `generate_attack(prompt, goal, target, **kwargs)` | str | N/A (required) | ⚠️ | Naming differs (`query` vs. `goal`) and `prompt/target` are unused, but semantics are equivalent when the harmful query is passed via `goal`. |
| Target query language (`language` in plan, `target_language` in repo) | `QueryAttackGen.PARAMETERS["query_language"]` | str | `"SQL"` | ✅ | Matches repo’s set of languages (SQL, Python, C++, C, C#, Go, Java, JavaScript, URL). |
| Extraction model (GPT-4-1106) | `QueryAttackGen.PARAMETERS["extraction_model"]` / `self.extraction_model` | str | `"gpt-4-1106-preview"` | ✅ | Default aligns with repo and plan; configurable via CLI/args. |
| Extraction temperature | `QueryAttackGen.PARAMETERS["temperature"]` / `self.temperature` | float | `0.0` | ✅ | Satisfies paper’s guidance to set temperature to 0 for reproducibility (for the extraction/splitting/safety LLM). |
| Extraction verification flag (`trans_verify`) | `QueryAttackGen.PARAMETERS["trans_verify"]` / `self.trans_verify` | bool | `False` | ✅ | Exposes the same boolean control as the repo, enabling safety-judging and word-reversal when `True`. |
| Long-sentence splitting control | `QueryAttackGen.PARAMETERS["split_long_sentences"]` / `self.split_long_sentences` | bool | `True` | ⚠️ | Default `True` matches repo behavior; allowing this to be set `False` deviates from the original always-split design for long queries. |
| Risk/evaluation fields (`Risk Level`, `Violation Type`) | Only in extraction prompt and validation | N/A | N/A | ✅ | Prompt and `_validate_extraction_response` require both fields for a valid response, matching repo robustness; they are not propagated further in either implementation. |
| Target LLM model for query understanding | JBFoundry LLM config vs. `your_model` in repo `test.py` | str | Framework-dependent | ⚠️ | Paper uses GPT-4-family targets; here selection is delegated to the surrounding framework rather than this attack class, which is acceptable but indirect. |
| Decoding temperature for target LLM | Framework config vs. `args.temperate` in repo `test.py` | float | Framework-dependent (repo default 0) | ⚠️ | Repo explicitly sets `temperature=0` for the target model; in jbfoundry this is controlled externally and is not enforced by `QueryAttackGen`. |

## Misalignments / Missing Items

1. **NLTK-free fallback path changes normalization semantics**
   - **Paper/Repo Citation**: Repo `trans_llms.py`:3–4, 157–171; Plan §1 (component extraction and normalization).
   - **Expected Behavior**: The reference implementation assumes NLTK is available and always performs POS-tagging with `word_tokenize`/`pos_tag`, then removes function words and certain POS tags before constructing final components.
   - **Observed Behavior**: When `nltk` is not installed, `queryattack_gen.py` falls back to a simple `.split()` tokenizer and a dummy `pos_tag` that labels all tokens as `NN`, so `_normalize_components` only strips a few hard-coded stopwords (`or/and/a`) and no POS-based function words (`queryattack_gen.py`:16–35, 901–931).
   - **Impact**: In environments without NLTK, the resulting `Content/Category/Modifier` phrases will be longer and noisier than in the gold repo, which can change how templates read and how the target LLM interprets them, reducing fidelity in those deployments.

2. **Configurable `split_long_sentences` parameter under-approximates long-query handling when disabled**
   - **Paper/Repo Citation**: Repo `translator.py`:47–79, 111–165; `split_sentence_llms.py`:5–72; Plan §1 & §4 (handling long/compound prompts).
   - **Expected Behavior**: The reference pipeline always runs LLM-based sentence splitting for queries with more than 13 tokens, then applies extraction/template-filling to each sub-sentence and concatenates the resulting code snippets, as illustrated by the "long example" prompts.
   - **Observed Behavior**: While the default `split_long_sentences=True` reproduces this behavior, the attack exposes `split_long_sentences` as a user-tunable flag; when set to `False`, long queries are processed as a single unit with no splitting, diverging from the gold-standard algorithm (`queryattack_gen.py`:81–87, 933–950, 1011–1027).
   - **Impact**: Users can inadvertently run configurations that weaken the attack on long or multi-intent prompts compared to the reference implementation, leading to behavioral differences that break strict fidelity, even though the default remains aligned.

## Extra Behaviors Not in Paper
- **NLTK-free fallback path**: If `nltk` is unavailable, the implementation uses naive tokenization and a dummy POS tagger (`queryattack_gen.py`:16–35). This keeps the attack runnable but weakens normalization compared with the repo, which assumes real NLTK tagging.
- **Configurable long-sentence splitting**: The `split_long_sentences` flag (default `True`) allows disabling the long-query splitting step entirely (`queryattack_gen.py`:81–87, 933–950, 1011–1027). This configuration is not present in the reference repo and, when changed from the default, produces behavior that diverges from the original algorithm for complex prompts.
- **Custom LLM wrapper and provider**: Using `LLMLiteLLM.from_config(provider="wenwen", model_name=...)` instead of direct OpenAI API calls differs from the repo’s client code, but as long as the model name and decoding parameters are equivalent this is acceptable and does not affect algorithmic fidelity.

## Required Changes to Reach 100%

1. **Eliminate or clearly fence off degraded-fidelity modes**
   - **Files/Lines**: `src/jbfoundry/attacks/generated/queryattack_gen.py`:16–35, 74–87, 901–931, 933–950, 1011–1027.
   - **Changes**:
     - Either require NLTK at runtime (failing loudly if unavailable) or default to the NLTK-backed path for all fidelity-critical experiments, documenting the fallback as a non-fidelity mode.
     - Either remove `split_long_sentences` as a user-facing parameter or clearly document/enforce that it must remain `True` when reproducing QueryAttack, so long-query splitting always occurs as in the repo.
   - **Justification**: Ensures that default and recommended configurations exactly match the gold-standard algorithm, preventing users from accidentally running weakened or behaviorally divergent variants.

## Final Verdict
Given that all core algorithmic components now align with the paper and reference repository but there remain configuration and dependency-driven modes that can change behavior (NLTK-free normalization and optional long-sentence splitting), the implementation is still **Not 100% Fidelity** relative to the original QueryAttack design, although in its default, NLTK-enabled configuration it is effectively indistinguishable from the gold-standard code.

## Audit Iteration 3 - 2025-12-24

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Different conversation packaging for the target LLM | ❌ | ⚠️ Partially Fixed | `generate_attack` now returns a structured multi-turn conversation (`[{"role": "system"/"assistant"/"user", ...}]`) instead of a flattened string, but the repo uses an empty system message plus a **user** context message, whereas this implementation moves the full context into the **system** role (`queryattack_gen.py`:993–1045 vs. `translator.py`:70–82, `test.py`:70–82). |
| NLTK-free fallback path changes normalization semantics | ❌ | ❌ Still Broken | If `nltk` is unavailable, the code still falls back to naive `.split()` tokenization and a dummy `pos_tag` that labels everything as `NN`, so only a few stopwords are removed; the gold repo assumes real NLTK POS tags and thus stronger normalization (`queryattack_gen.py`:16–35, 901–931; `trans_llms.py`:3–4, 157–171). |
| Configurable `split_long_sentences` parameter allows disabling long-query splitting | ⚠️ | ⚠️ Still Divergent | Default `split_long_sentences=True` matches the repo’s always-split behavior, but callers can set it to `False`, producing behavior that under-approximates the original multi-clause handling for complex prompts (`queryattack_gen.py`:81–87, 933–950, 1011–1026; `translator.py`:47–79, 111–165). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Robust extraction loop and optional `trans_verify` safety verification | ✅ | ✅ | `extract_query_components`, `_validate_extraction_response`, and `_apply_safety_verification` still mirror `trans_sentence_llms` and related safety prompts, including retry-on-invalid and word reversal (`queryattack_gen.py`:812–899; `trans_llms.py`:123–171, 191–200). |
| POS-based normalization of extracted components | ✅ | ✅ | `_normalize_components` continues to tokenize, POS-tag, and remove function words/POS tags analogous to the repo; the main-path semantics with NLTK present remain aligned (`queryattack_gen.py`:901–931; `trans_llms.py`:157–171). |
| Handling long/compound queries via splitting and multi-clause templates | ✅ | ✅ | For queries with more than 13 tokens and `split_long_sentences=True`, `_split_sentence` plus concatenation of multiple templates still matches the reference long-example behavior (`queryattack_gen.py`:933–950, 1011–1027; `translator.py`:47–79, 111–165; `split_sentence_llms.py`:5–72). |

**NEW Issues Found This Iteration:**
- No additional semantic deviations were identified beyond those already documented; remaining gaps are limited to conversation role placement, the NLTK-free fallback, and the configurable long-sentence splitting.

**Summary:**
- Fixed: 0 issues
- Partially Fixed: 1 issue
- Still Broken: 2 issues
- Regressions: 0 issues
- New Issues: 0 issues

### Implementation Fidelity Verdict (Iteration 3)
- Paper ID: 2502.09723
- Attack: queryattack_gen
- Verdict: Not 100% Fidelity
- Coverage: 9/10 components (90%)
- Iteration: 3

## Executive Summary
The iteration-3 `QueryAttackGen` implementation in `src/jbfoundry/attacks/generated/queryattack_gen.py` remains closely aligned with both the QueryAttack paper and the official repository: it preserves the multi-step pipeline (component extraction, normalization, template filling, and in-context query understanding), mirrors the extraction/safety/splitting prompts, and handles long/compound prompts and POS-based normalization in line with the gold code. The previously major gap in conversation packaging has been substantially reduced: the attack now returns a structured multi-message conversation with explicit roles instead of a flattened string, bringing it much closer to `test.py`’s setup, though the context is placed in a `system` message rather than in an initial `user` turn. Two previously identified deviations remain: an NLTK-free fallback mode that weakens normalization semantics and a `split_long_sentences` knob that lets users disable the long-query splitting required for strict fidelity. Because of these remaining behavioral differences, the implementation is still **not** an exact replica of the reference algorithm, though it is now very high fidelity in normal configurations.

## Coverage Table
| Paper Section/Step | Paper/Repo Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 / Plan §1, Repo `trans_llms.py` | Use GPT-4-1106-style model for component extraction with temperature 0 | `queryattack_gen.py`:60–71, 805–810; `trans_llms.py`:1–4 | ✅ | Extraction uses a configurable model with default `gpt-4-1106-preview` and `temperature=0.0`, matching paper/repo defaults. |
| Plan §1, Repo `trans_llms.py` | Extraction prompt content (CONTENT ANALYSIS SYSTEM, JSON with Request Content/Content Source/Key Object/Risk Level/Violation Type) | `queryattack_gen.py`:696–793; `trans_llms.py`:6–103 | ✅ | `EXTRACTION_PROMPT` remains a near-verbatim port of `trans_user_template`; only formatting/quote differences, no semantic change. |
| Plan §1, Repo `trans_llms.py` | Robust JSON parsing and optional safety verification (`trans_verify`) with word-reversal for harmful phrases | `queryattack_gen.py`:812–843, 846–874, 876–899; `trans_llms.py`:123–171, 191–200 | ✅ | `extract_query_components` loops until `_validate_extraction_response` returns components; when `trans_verify=True`, `_apply_safety_verification` checks each component with safety prompts and reverses words on "yes" responses, mirroring repo behavior. |
| Repo `trans_llms.py` | Post-processing extracted components via POS-tagging & stopword removal | `queryattack_gen.py`:901–931; `trans_llms.py`:157–171 | ✅ | `_normalize_components` tokenizes, POS-tags, removes connectors (`or/and/a`) and function-word POS tags, aligning with the reference normalization on the main NLTK-backed path. |
| Plan §2, Repo `all_template.py` | Language-specific templates for SQL, Python, C++, C, C#, Go, Java, JavaScript, URL with `{Content, Category, Modifier}` slots | `queryattack_gen.py`:90–100; `all_template.py`:1–43 | ✅ | Template strings and slot names match repo templates, including SQL and code-like forms for all languages. |
| Plan §2 | Filling templates with extracted components | `queryattack_gen.py`:986–991; `translator.py`:111–165 | ✅ | `fill_query_template` uses `template.format(**components)` with keys `Content`, `Category`, `Modifier`, consistent with `assemble_code`. |
| Plan §1 & §4, Repo `translator.py` & `split_sentence_llms.py` | Handling long/compound queries: LLM-based sentence splitting and multi-clause code assembly | `queryattack_gen.py`:933–950, 1011–1027; `translator.py`:47–79, 111–165; `split_sentence_llms.py`:5–72 | ✅ | For queries with >13 tokens and `split_long_sentences=True`, the implementation calls `_split_sentence` and concatenates multiple templates as in the repo’s long examples. |
| Plan §3, Repo `all_template.py` | Per-language "query understanding" context prompts with examples and long example | `queryattack_gen.py`:103–608; `all_template.py`:46–542 | ✅ | `CONTEXT_PROMPTS` are faithful copies of the `_first_user_content_4o` prompts for all languages. |
| Plan §3, Repo `all_template.py` | Assistant acknowledgement message ("Got it! I’ll provide step-by-step guidance...") per language | `queryattack_gen.py`:611–620; `all_template.py`:545–554 | ✅ | `ASSISTANT_RESPONSES` strings match `_assistant_response_4o` semantics and wording. |
| Plan §4, Repo `translator.py` & `test.py` | Attack pipeline and conversation structure: (1) extract components, (2) fill template(s), (3) send code to target LLM within multi-turn context | `queryattack_gen.py`:993–1046; `translator.py`:111–165; `test.py`:70–82, 120–155 | ⚠️ | Algorithmic steps and long-query behavior are preserved, and the attack now returns a structured multi-message conversation, but the repo uses an empty system message plus a **user** context message followed by assistant ack and user code, while this implementation uses the context prompt as a **system** message with no initial user turn, which may slightly change in-context behavior. |

## Parameter Mapping
| Paper/Repo Parameter | Code Parameter / Source | Type | Default | Match (✅/❌/⚠️) | Notes |
|---|---|---|---|---|---|
| Natural language query (`query` in plan) | `goal` argument to `generate_attack(prompt, goal, target, **kwargs)` | str | N/A (required) | ⚠️ | Naming differs (`query` vs. `goal`) and `prompt/target` are unused, but semantics are equivalent when the harmful query is passed via `goal`. |
| Target query language (`language` in plan, `target_language` in repo) | `QueryAttackGen.PARAMETERS["query_language"]` | str | `"SQL"` | ✅ | Matches repo’s set of languages (SQL, Python, C++, C, C#, Go, Java, JavaScript, URL). |
| Extraction model (GPT-4-1106) | `QueryAttackGen.PARAMETERS["extraction_model"]` / `self.extraction_model` | str | `"gpt-4-1106-preview"` | ✅ | Default aligns with repo and plan; configurable via CLI/args. |
| Extraction temperature | `QueryAttackGen.PARAMETERS["temperature"]` / `self.temperature` | float | `0.0` | ✅ | Satisfies paper’s guidance to set temperature to 0 for reproducibility (for the extraction/splitting/safety LLM). |
| Extraction verification flag (`trans_verify`) | `QueryAttackGen.PARAMETERS["trans_verify"]` / `self.trans_verify` | bool | `False` | ✅ | Exposes the same boolean control as the repo, enabling safety-judging and word-reversal when `True`. |
| Long-sentence splitting control | `QueryAttackGen.PARAMETERS["split_long_sentences"]` / `self.split_long_sentences` | bool | `True` | ⚠️ | Default `True` matches repo behavior; allowing this to be set `False` deviates from the original always-split design for long queries. |
| Risk/evaluation fields (`Risk Level`, `Violation Type`) | Only in extraction prompt and validation | N/A | N/A | ✅ | Prompt and `_validate_extraction_response` require both fields for a valid response, matching repo robustness; they are not propagated further in either implementation. |
| Target LLM model for query understanding | JBFoundry LLM config vs. `your_model` in repo `test.py` | str | Framework-dependent | ⚠️ | Paper uses GPT-4-family targets; here selection is delegated to the surrounding framework rather than this attack class, which is acceptable but indirect. |
| Decoding temperature for target LLM | Framework config vs. `args.temperate` in repo `test.py` | float | Framework-dependent (repo default 0) | ⚠️ | Repo explicitly sets `temperature=0` for the target model; in jbfoundry this is controlled externally and is not enforced by `QueryAttackGen`. |

## Misalignments / Missing Items

1. **Conversation roles differ from the gold-standard multi-turn setup**
   - **Paper/Repo Citation**: Plan §3 (query understanding with in-context examples), Repo `translator.py`:111–165; `test.py`:70–82, 120–155.
   - **Expected Behavior**: Build a four-message conversation with explicit roles: an (empty) `system` message, a `user` message containing the language-specific context prompt, an `assistant` acknowledgement, and a final `user` message containing the structured query code.
   - **Observed Behavior**: `generate_attack` returns a three-message conversation where the full context prompt is placed in the `system` role, followed by an `assistant` acknowledgement and a final `user` message with the program-like sentence(s) (`queryattack_gen.py`:1035–1043). There is no initial `user` context turn.
   - **Impact**: This is much closer to the repo than the previous flattened-string design, but subtle differences in role assignment can still affect how some LLMs weigh instructions and context, preventing strict 1:1 fidelity with the original evaluation setup.

## Extra Behaviors Not in Paper
- **NLTK-free fallback path**: If `nltk` is unavailable, the implementation falls back to simple `.split()` tokenization and a dummy `pos_tag` that labels everything as `NN` (`queryattack_gen.py`:16–35). This keeps the attack runnable but weakens POS-based normalization compared to the repo, which assumes proper NLTK tagging.
- **Configurable long-sentence splitting**: The `split_long_sentences` flag (default `True`) allows disabling the long-query splitting step entirely (`queryattack_gen.py`:81–87, 933–950, 1011–1027). This configuration is not present in the reference repo and, when changed from the default, produces behavior that diverges from the original algorithm for complex prompts.
- **Custom LLM wrapper and provider**: Using `LLMLiteLLM.from_config(provider="wenwen", model_name=...)` instead of direct OpenAI API calls differs from the repo’s client code, but as long as the model name and decoding parameters are equivalent this is acceptable and does not affect algorithmic fidelity.

## Required Changes to Reach 100%

1. **Align conversation role structure exactly with the gold-standard multi-turn design**
   - **Files/Lines**: `src/jbfoundry/attacks/generated/queryattack_gen.py`:993–1046; reference `translator.py`:111–165; `test.py`:70–82, 120–155.
   - **Changes**:
     - Represent the conversation as: (a) an empty `system` message, (b) a `user` message with the context prompt, (c) an `assistant` acknowledgement, and (d) a final `user` message with the structured query code, matching `test.py`.
     - Ensure the surrounding framework passes this exact message sequence to the target LLM.
   - **Justification**: This restores the precise interaction pattern used in the QueryAttack repository and eliminates remaining role-assignment discrepancies.

2. **Eliminate or clearly fence off degraded-fidelity modes**
   - **Files/Lines**: `src/jbfoundry/attacks/generated/queryattack_gen.py`:16–35, 74–87, 901–931, 933–950, 1011–1027.
   - **Changes**:
     - Either require NLTK at runtime (failing loudly if unavailable) or document and expose a separate "compatibility" mode, so that the default execution path always uses true POS tagging as in `trans_llms.py`.
     - Either remove `split_long_sentences` as a user-facing parameter or clearly document that disabling it yields behavior that is **not** faithful to QueryAttack; for strict-fidelity experiments, enforce `split_long_sentences=True`.
   - **Justification**: Prevents users from unknowingly running configurations that diverge from the gold-standard algorithm, preserving 100% fidelity under the documented default.

## Final Verdict
Given the remaining differences in conversation role structure and the presence of configuration paths that can reduce fidelity (NLTK-free fallback and optional long-sentence splitting), the implementation is still **Not 100% Fidelity** relative to the QueryAttack paper and reference repository, although it is now very close in all core algorithmic respects.

## Audit Iteration 2 - 2025-12-24

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Missing robust re-query loop and optional safety verification for extraction | ❌ | ✅ Fixed | `extract_query_components` now loops until `_validate_extraction_response` returns non-`None`, and an optional `trans_verify` flag triggers `_apply_safety_verification` with safety prompts and word-reversal (`queryattack_gen.py`:812–843, 876–899; `trans_llms.py`:123–171, 191–200). |
| No POS-based normalization of extracted components | ❌ | ✅ Fixed | Added `_normalize_components` which tokenizes, POS-tags, and removes function words/POS tags as in the repo (`queryattack_gen.py`:901–931; `trans_llms.py`:157–171). |
| Weaker validity checks on JSON fields | ❌ | ✅ Fixed | `_validate_extraction_response` now requires all five fields (`Request Content`, `Content Source`, `Key Object`, `Risk Level`, `Violation Type`) and rejects responses with "unspecified/unknown/sorry" in the three semantic fields (`queryattack_gen.py`:852–867; `trans_llms.py`:173–190). |
| Different conversation packaging for the target LLM | ⚠️ | ❌ Still Broken | Attack prompt is still returned as a single flattened string with `SYSTEM/ASSISTANT/USER` markers instead of a true multi-message conversation (`queryattack_gen.py`:1032–1045 vs. `translator.py`:70–82, `test.py`:70–82, 120–155). |
| No handling of long/compound prompts via splitting and multi-clause templates | ❌ | ✅ Fixed | Long queries (>13 tokens) are now split with `_split_sentence`, and multiple templates are concatenated as in the repo’s long examples (`queryattack_gen.py`:933–950, 1011–1026; `translator.py`:47–79, 111–165; `split_sentence_llms.py`:5–72). |
| Missing `trans_verify` control and safety rephrasing behavior | ❌ | ✅ Fixed | New `trans_verify` `AttackParameter` and `_apply_safety_verification` implement the optional safety-judging loop with word reversal for harmful phrases (`queryattack_gen.py`:74–80, 876–899; `trans_llms.py`:123–151, 191–200). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Use GPT-4-1106-style model and temperature 0 for extraction | ✅ | ✅ | Defaults remain `extraction_model="gpt-4-1106-preview"` and `temperature=0.0`, matching paper/repo (`queryattack_gen.py`:60–71, 805–810; `trans_llms.py`:1–4). |
| Language-specific templates for SQL/Python/C++/etc. | ✅ | ✅ | `TEMPLATES` entries still align with `all_template.py`, including `{Content, Category, Modifier}` slots (`queryattack_gen.py`:90–100; `all_template.py`:1–43). |
| Per-language context prompts and assistant acknowledgements | ✅ | ✅ | `CONTEXT_PROMPTS` and `ASSISTANT_RESPONSES` remain aligned with `_first_user_content_4o` and `_assistant_response_4o` (`queryattack_gen.py`:103–608, 611–620; `all_template.py`:46–555). |

**NEW Issues Found This Iteration:**
- NLTK-free fallback path changes normalization semantics: if `nltk` is unavailable, the code falls back to naive tokenization and a dummy `pos_tag` that labels all tokens as `NN`, so only stopwords `or/and/a` are removed, unlike the repo which assumes real POS tags and removes broader function words (`queryattack_gen.py`:16–35, 901–931).
- The new `split_long_sentences` parameter allows disabling long-query splitting; while the default `True` matches the repo, turning it off under-approximates the original algorithm for complex prompts (`queryattack_gen.py`:81–87, 1011–1026; `translator.py`:47–79).

**Summary:**
- Fixed: 5 issues
- Partially Fixed: 0 issues
- Still Broken: 1 issue
- Regressions: 0 issues
- New Issues: 2 issues

### Implementation Fidelity Verdict (Iteration 2)
- Paper ID: 2502.09723
- Attack: queryattack_gen
- Verdict: Not 100% Fidelity
- Coverage: 9/10 components (90%)
- Iteration: 2

## Executive Summary
The updated `QueryAttackGen` implementation in `src/jbfoundry/attacks/generated/queryattack_gen.py` now closely tracks the official QueryAttack repository and the paper: it adds a robust extraction loop with validation, optional `trans_verify`-style safety checking and word reversal, POS-based normalization of extracted components, and LLM-based splitting for long queries followed by concatenation of multiple structured-code clauses. These changes resolve all previously identified correctness gaps except for one: the final attack prompt is still packaged as a single flattened string containing `SYSTEM/ASSISTANT/USER` markers rather than the multi-turn message structure used by the gold-standard code. This remaining deviation can meaningfully affect in-context learning behavior and safety interactions, and together with minor configuration extensions (like the ability to disable splitting or run without NLTK) means the implementation is still **not** a perfect replica of the reference. Overall fidelity is high and algorithmically faithful, but not exact enough to claim 100% fidelity.

## Coverage Table
| Paper Section/Step | Paper/Repo Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 / Plan §1, Repo `trans_llms.py` | Use GPT-4-1106-style model for component extraction with temperature 0 | `queryattack_gen.py`:60–71, 805–810; `trans_llms.py`:1–4 | ✅ | Extraction uses a configurable model with default `gpt-4-1106-preview` and `temperature=0.0`, matching paper/repo defaults. |
| Plan §1, Repo `trans_llms.py` | Extraction prompt content (CONTENT ANALYSIS SYSTEM, JSON with Request Content/Content Source/Key Object/Risk Level/Violation Type) | `queryattack_gen.py`:696–793; `trans_llms.py`:6–103 | ✅ | `EXTRACTION_PROMPT` is a near-verbatim port of `trans_user_template`; only formatting/quote differences, no semantic change. |
| Plan §1, Repo `trans_llms.py` | Robust JSON parsing and optional safety verification (`trans_verify`) with word-reversal for harmful phrases | `queryattack_gen.py`:812–843, 846–874, 876–899; `trans_llms.py`:123–171, 191–200 | ✅ | `extract_query_components` loops until `_validate_extraction_response` returns components; when `trans_verify=True`, `_apply_safety_verification` checks each component with safety prompts and reverses words on "yes" responses, mirroring repo behavior. |
| Repo `trans_llms.py` | Post-processing extracted components via POS-tagging & stopword removal | `queryattack_gen.py`:901–931; `trans_llms.py`:157–171 | ✅ | `_normalize_components` tokenizes, POS-tags, removes connectors (`or/and/a`) and function-word POS tags, aligning with the reference normalization. |
| Plan §2, Repo `all_template.py` | Language-specific templates for SQL, Python, C++, C, C#, Go, Java, JavaScript, URL with `{Content, Category, Modifier}` slots | `queryattack_gen.py`:90–100; `all_template.py`:1–43 | ✅ | Template strings and slot names match repo templates, including SQL and code-like forms for all languages. |
| Plan §2 | Filling templates with extracted components | `queryattack_gen.py`:986–991; `translator.py`:111–165 | ✅ | `fill_query_template` uses `template.format(**components)` with keys `Content`, `Category`, `Modifier`, consistent with `assemble_code`. |
| Plan §1 & §4, Repo `translator.py` & `split_sentence_llms.py` | Handling long/compound queries: LLM-based sentence splitting and multi-clause code assembly | `queryattack_gen.py`:933–950, 1011–1026; `translator.py`:47–79, 111–165; `split_sentence_llms.py`:5–72 | ✅ | For queries with >13 tokens and `split_long_sentences=True`, the implementation calls `_split_sentence` and concatenates multiple templates as in the repo’s long examples. |
| Plan §3, Repo `all_template.py` | Per-language "query understanding" context prompts with examples and long example | `queryattack_gen.py`:103–608; `all_template.py`:46–542 | ✅ | `CONTEXT_PROMPTS` are faithful copies of the `_first_user_content_4o` prompts for all languages. |
| Plan §3, Repo `all_template.py` | Assistant acknowledgement message ("Got it! I’ll provide step-by-step guidance...") per language | `queryattack_gen.py`:611–620; `all_template.py`:545–554 | ✅ | `ASSISTANT_RESPONSES` strings match `_assistant_response_4o` semantics and wording. |
| Plan §4, Repo `translator.py` & `test.py` | Attack pipeline and conversation structure: (1) extract components, (2) fill template(s), (3) send code to target LLM within multi-turn context | `queryattack_gen.py`:993–1045; `translator.py`:111–165; `test.py`:70–82, 120–155 | ⚠️ | Algorithmic steps 1–2–3 and long-query behavior are preserved, but the final prompt is returned as a single string embedding role markers instead of a true multi-message conversation, which can affect in-context behavior. |

## Parameter Mapping
| Paper/Repo Parameter | Code Parameter / Source | Type | Default | Match (✅/❌/⚠️) | Notes |
|---|---|---|---|---|---|
| Natural language query (`query` in plan) | `goal` argument to `generate_attack(prompt, goal, target, **kwargs)` | str | N/A (required) | ⚠️ | Naming differs (`query` vs. `goal`) and `prompt/target` are unused, but semantics are equivalent when the harmful query is passed via `goal`. |
| Target query language (`language` in plan, `target_language` in repo) | `QueryAttackGen.PARAMETERS["query_language"]` | str | `"SQL"` | ✅ | Matches repo’s set of languages (SQL, Python, C++, C, C#, Go, Java, JavaScript, URL). |
| Extraction model (GPT-4-1106) | `QueryAttackGen.PARAMETERS["extraction_model"]` / `self.extraction_model` | str | `"gpt-4-1106-preview"` | ✅ | Default aligns with repo and plan; configurable via CLI/args. |
| Extraction temperature | `QueryAttackGen.PARAMETERS["temperature"]` / `self.temperature` | float | `0.0` | ✅ | Satisfies paper’s guidance to set temperature to 0 for reproducibility (for the extraction/splitting/safety LLM). |
| Extraction verification flag (`trans_verify`) | `QueryAttackGen.PARAMETERS["trans_verify"]` / `self.trans_verify` | bool | `False` | ✅ | Exposes the same boolean control as the repo, enabling safety-judging and word-reversal when `True`. |
| Long-sentence splitting control | `QueryAttackGen.PARAMETERS["split_long_sentences"]` / `self.split_long_sentences` | bool | `True` | ⚠️ | Default `True` matches repo behavior; allowing this to be set `False` deviates from the original always-split design for long queries. |
| Risk/evaluation fields (`Risk Level`, `Violation Type`) | Only in extraction prompt and validation | N/A | N/A | ✅ | Prompt and `_validate_extraction_response` require both fields for a valid response, matching repo robustness; they are not propagated further in either implementation. |
| Target LLM model for query understanding | JBFoundry LLM config vs. `your_model` in repo `test.py` | str | Framework-dependent | ⚠️ | Paper uses GPT-4-family targets; here selection is delegated to the surrounding framework rather than this attack class, which is acceptable but indirect. |
| Decoding temperature for target LLM | Framework config vs. `args.temperate` in repo `test.py` | float | Framework-dependent (repo default 0) | ⚠️ | Repo explicitly sets `temperature=0` for the target model; in jbfoundry this is controlled externally and is not enforced by `QueryAttackGen`. |

## Misalignments / Missing Items

1. **Conversation packaged as a single flattened string instead of multi-turn messages**
   - **Paper/Repo Citation**: Plan §3 (query understanding with in-context examples), Repo `translator.py`:70–82; `test.py`:70–82, 120–155.
   - **Expected Behavior**: Build a multi-message conversation: an initial user message with the language-specific context prompt, an assistant acknowledgement, then a user message containing the structured query code, all using explicit `role` fields so the API treats them as distinct turns.
   - **Observed Behavior**: `generate_attack` returns one large string with inline markers (`"SYSTEM:\n{context_prompt}\n\nASSISTANT:\n{assistant_response}\n\nUSER:\n{query_code}"`) that the framework will send as a single message, relying on in-text tags rather than real conversational roles (`queryattack_gen.py`:1032–1045).
   - **Impact**: While the content is almost identical, the lack of true role separation can change how the target LLM applies instructions and safety policies, leading to different jailbreak behavior compared with the gold-standard multi-turn setup.

## Extra Behaviors Not in Paper
- **NLTK-free fallback path**: If `nltk` is unavailable, the implementation falls back to simple `.split()` tokenization and a dummy `pos_tag` that labels everything as `NN` (`queryattack_gen.py`:16–35). This keeps the attack runnable but weakens POS-based normalization compared to the repo, which assumes proper NLTK tagging.
- **Configurable long-sentence splitting**: The `split_long_sentences` flag (default `True`) allows disabling the long-query splitting step entirely (`queryattack_gen.py`:81–87, 1011–1026). This configuration is not present in the reference repo and, when changed from the default, produces behavior that diverges from the original algorithm for complex prompts.
- **Custom LLM wrapper and provider**: Using `LLMLiteLLM.from_config(provider="wenwen", model_name=...)` instead of direct OpenAI API calls differs from the repo’s client code, but as long as the model name and decoding parameters are equivalent this is acceptable and does not affect algorithmic fidelity.

## Required Changes to Reach 100%

1. **Align conversation structure with the gold-standard multi-turn design**
   - **Files/Lines**: `src/jbfoundry/attacks/generated/queryattack_gen.py`:993–1045; reference `translator.py`:70–82; `test.py`:70–82, 120–155.
   - **Changes**:
     - Represent the attack as a sequence of messages with explicit `role` fields (system/user/assistant/user), containing the same context prompt, acknowledgement, and structured query code used now.
     - Ensure the surrounding framework passes this structured conversation to the target LLM, not a single flattened text block.
   - **Justification**: This restores the exact interaction pattern used in the QueryAttack repository and better matches the in-context learning setup described in the paper.

2. **Optionally constrain configuration knobs that can break parity**
   - **Files/Lines**: `src/jbfoundry/attacks/generated/queryattack_gen.py`:74–87, 933–950, 1011–1026.
   - **Changes**:
     - Either document that `split_long_sentences` must remain `True` for QueryAttack-conformant experiments, or remove this knob and always split long queries as in the repo.
     - Optionally document that the NLTK fallback path is a degraded mode and that experiments seeking strict fidelity should install NLTK to reproduce full POS-based normalization.
   - **Justification**: Ensures users can clearly distinguish between faithful QueryAttack runs and convenience modes that trade off some fidelity for robustness.

## Final Verdict
Despite substantial improvements that bring extraction, normalization, long-query handling, and parameterization into close alignment with the paper and the official QueryAttack codebase, the remaining difference in conversation packaging (single flattened prompt vs. multi-turn messages) and the presence of configuration paths that can break parity mean the implementation is still **Not 100% Fidelity** relative to the source paper and gold-standard repository.

# Implementation Fidelity Verdict
- Paper ID: 2502.09723
- Attack: queryattack_gen
- Verdict: Not 100% Fidelity
- Coverage: 6/10 components (60%)
- Iteration: 1

## Executive Summary
The `QueryAttackGen` implementation in `src/jbfoundry/attacks/generated/queryattack_gen.py` captures the high-level structure of QueryAttack as described in the paper and the official QueryAttack repository: it uses GPT-4-1106-style models to extract three semantic components, fills language-specific templates (SQL/Python/C++/etc.), and wraps them in rich in-context prompts to steer the target LLM. However, compared with the gold-standard repository (`attacks_paper_info/2502.09723/QueryAttack`) there are several semantic deviations: the lack of re-querying and safety-verification loops for extraction, omission of post-processing (POS-based token filtering), and a different conversation/role packaging for the final prompt. These issues mean the behavior of the implemented attack can differ materially from the reference implementation, especially on edge cases and long/complex prompts. Overall, the implementation is close but not exact, so it does **not** reach 100% fidelity.

## Coverage Table
| Paper Section/Step | Paper/Repo Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §3 / Plan §1, Repo `trans_llms.py` | Use GPT-4-1106-style model for component extraction with temperature 0 | `queryattack_gen.py`:30–52, 687–700; `trans_llms.py`:1–3,123–127 | ✅ | Parameters `extraction_model="gpt-4-1106-preview"` and `temperature=0.0` match the paper and repo defaults; model name is configurable but default is correct. |
| Plan §1, Repo `trans_llms.py` | Extraction prompt content (CONTENT ANALYSIS SYSTEM, JSON with Request Content/Content Source/Key Object/Risk Level/Violation Type) | `queryattack_gen.py`:588–683; `trans_llms.py`:6–103 | ✅ | EXTRACTION_PROMPT is a near-verbatim port of `trans_user_template`; minor quote-format differences do not change semantics. |
| Plan §1, Repo `trans_llms.py` | Robust JSON parsing: loop until all required fields are present and not "unspecified/unknown/sorry"; optional safety verification (`trans_verify`) with reversal of harmful phrases | `queryattack_gen.py`:702–723,725–749; `trans_llms.py`:123–171,173–200 | ❌ | Repo loops until valid JSON and (optionally) passes a safety test; this implementation performs a single call, only checks three fields, and raises `ValueError` without retry or safety verification. |
| Repo `trans_llms.py` | Post-processing extracted components via POS-tagging & stopword removal | `trans_llms.py`:157–171 | ❌ | The reference code tokenizes each phrase, drops function words and certain POS tags; `QueryAttackGen` uses raw strings without this normalization, changing the resulting templates. |
| Plan §2, Repo `all_template.py` | Language-specific templates for SQL, Python, C++, C, C#, Go, Java, JavaScript, URL with `{Content, Category, Modifier}` slots | `queryattack_gen.py`:55–66; `all_template.py`:1–43 | ✅ | Template strings and slot names match the repo (including unusual C/C++ forms); all languages from the repo are supported. |
| Plan §2 | Filling templates with extracted components | `queryattack_gen.py`:751–756 | ✅ | `fill_query_template` uses `template.format(**components)` with keys `Content`, `Category`, `Modifier`, consistent with the repo’s `assemble_code`. |
| Plan §3, Repo `all_template.py` | Per-language "query understanding" context prompts with examples and long example | `queryattack_gen.py`:68–117,119–171,173–285,287–343,344–419,421–477,479–534,536–573; `all_template.py`:45–542 | ✅ | CONTEXT_PROMPTS closely mirror the `_first_user_content_4o` templates for all languages; structure, examples, and instructions align. |
| Plan §3, Repo `all_template.py` | Assistant acknowledgement message ("Got it! I’ll provide step-by-step guidance...") per language | `queryattack_gen.py`:576–585; `all_template.py`:545–554 | ✅ | Assistant responses are semantically identical to the repo’s `_assistant_response_4o` strings. |
| Plan §4, Repo `translator.py` & `test.py` | Attack pipeline: (1) extract components, (2) fill template, (3) send code to target LLM within context; conversation structure | `queryattack_gen.py`:758–796; `translator.py`:111–165; `test.py`:70–87,120–150 | ⚠️ | Steps 1–2–3 are preserved, but `QueryAttackGen` flattens system/assistant/user turns into a single string with "SYSTEM:/ASSISTANT:/USER:" markers, whereas the repo uses explicit multi-turn role messages. Behavior is similar but not identical. |
| Repo `translator.py` & `split_sentence_llms.py` | Handling long/compound queries: LLM-based sentence splitting and multiple `{Content, Category, Modifier}` phrases per original query assembled into multi-clause code | `translator.py`:47–79,111–165; `queryattack_gen.py`:702–723,751–756,775–779 | ⚠️ | The repo can split long sentences and concatenate multiple templates; `QueryAttackGen` extracts a single triple from the entire `goal` string and generates one template instance. Equivalent for simple queries but diverges on long/compound prompts. |

## Parameter Mapping
| Paper/Repo Parameter | Code Parameter / Source | Type | Default | Match (✅/❌/⚠️) | Notes |
|---|---|---|---|---|---|
| Natural language query (`query` in plan) | `goal` argument to `generate_attack(prompt, goal, target, **kwargs)` | str | N/A (required) | ⚠️ | Plan names the parameter `query`; implementation uses `goal` and ignores `prompt`/`target` for the attack logic, but semantics are equivalent if caller passes the harmful query as `goal`. |
| Target query language (`language` in plan, `target_language` in repo) | `QueryAttackGen.PARAMETERS["query_language"]` | str | `"SQL"` | ✅ | Choices and meaning match repo’s `target_language` (SQL, Python, C++, C, C#, Go, Java, JavaScript, URL). |
| Extraction model (GPT-4-1106) | `QueryAttackGen.PARAMETERS["extraction_model"]` and `self.extraction_model` | str | `"gpt-4-1106-preview"` | ✅ | Default aligns with repo/plan; parameter is configurable. |
| Extraction temperature | `QueryAttackGen.PARAMETERS["temperature"]` and `self.temperature` | float | `0.0` | ✅ | Matches paper’s requirement to set temperature 0 for reproducibility. |
| Extraction verification flag (`trans_verify` in repo) | `args.trans_verify` in `trans_sentence_llms` (repo only) | bool | `False` (repo) | ❌ | Not exposed or implemented in `QueryAttackGen`; no way to enable safety-verification loop or word-reversing behavior from the gold-standard code. |
| Risk/evaluation fields (`Risk Level`, `Violation Type`) | Only in extraction prompt / repo parsing | N/A | N/A | ⚠️ | Prompt includes these fields but `QueryAttackGen` only parses `Request Content`, `Content Source`, `Key Object`; repo requires all five fields to be present for validity. Impact is mainly on robustness, not prompt content. |
| Target LLM model for query understanding | `your_model` in repo `test.py`; external config in jbfoundry | str | repo: from `openai_log.py`; jbfoundry: from LLM config | ⚠️ | Paper specifies GPT-4-family targets; this implementation delegates target selection to the surrounding framework, which is acceptable but indirect. |
| Decoding temperature for target LLM | `args.temperate` in repo `test.py`; external in jbfoundry | float | `0` | ⚠️ | Repo uses `temperature=0`; jbfoundry may configure this independently of the attack; not controlled by `QueryAttackGen`. |

## Misalignments / Missing Items

1. **Missing robust re-query loop and optional safety verification for extraction**
   - **Paper/Repo Citation**: Plan §1 ("Use GPT-4-1106 to perform component extraction"), Repo `trans_llms.py`:123–171,191–200.
   - **Expected Behavior**: Call the extraction LLM repeatedly until a fully valid JSON object is returned **and**, when `trans_verify` is enabled, until the derived components are judged "not harmful" by a secondary safety-judging LLM (with word-reversal for harmful phrases). Also require presence of all five JSON fields (`Request Content`, `Content Source`, `Key Object`, `Risk Level`, `Violation Type`) and reject any containing "unspecified"/"unknown"/"sorry".
   - **Observed Behavior**: `QueryAttackGen.extract_query_components` (`queryattack_gen.py`:702–723) performs a single LLM call and parses only the three component fields. `_validate_extraction_response` (`queryattack_gen.py`:725–749) checks for missing fields or invalid terms and raises `ValueError` on failure but does not retry or perform any safety verification.
   - **Impact**: Reduced robustness and potentially different component triples compared to the reference implementation, especially on borderline or safety-filtered outputs. In some cases where the repo would keep querying (or adjust components via word reversal), this implementation will fail or proceed with less-validated components, altering the resulting structured query and attack strength.

2. **No POS-based normalization of extracted components**
   - **Paper/Repo Citation**: Repo `trans_llms.py`:157–171 (POS-tagging and removal of function words).
   - **Expected Behavior**: After extraction, tokenize each component, tag POS, and remove articles, conjunctions, prepositions, adverbs, numerals, etc., plus simplistic removal of some connecting words, to yield compact phrases (e.g., "travel guide", "Travel Brochure", "Paris") that better match the templates.
   - **Observed Behavior**: `QueryAttackGen` returns the raw extracted strings from the LLM without any normalization or POS-based filtering.
   - **Impact**: Templates in `TEMPLATES` may contain longer, noisier phrases than in the gold-standard code. This can affect how natural or interpretable the program-like sentences are and may change the target LLM’s response patterns.

3. **Weaker validity checks on JSON fields**
   - **Paper/Repo Citation**: Repo `trans_llms.py`:173–190.
   - **Expected Behavior**: `validate_response` verifies that all five fields (`Request Content`, `Content Source`, `Key Object`, `Risk Level`, `Violation Type`) are present and non-null, and that no component contains "unspecified"/"unknown"/"sorry"; otherwise it returns `(None, None, None)` and the caller retries.
   - **Observed Behavior**: `_validate_extraction_response` (`queryattack_gen.py`:725–749) only checks the three semantic fields (`Request Content`, `Content Source`, `Key Object`) and does not enforce the presence or content of `Risk Level` and `Violation Type`.
   - **Impact**: While the missing risk/violation checks do not directly affect the generated prompt content, they reduce parity with the repo’s robustness criteria and could let through malformed responses that the gold-standard code would reject.

4. **Different conversation packaging for the target LLM**
   - **Paper/Repo Citation**: Plan §3, Repo `test.py`:70–87,120–150.
   - **Expected Behavior**: Build a multi-turn conversation with explicit roles: (1) system message (empty or generic), (2) user message containing the language-specific context prompt, (3) assistant message with `"Got it!"`-style acknowledgement, and (4) user message with the program-like sentence(s) (structured query code).
   - **Observed Behavior**: `generate_attack` (`queryattack_gen.py`:758–796) constructs a single text block containing `"SYSTEM:\n{context_prompt}\n\nASSISTANT:\n{assistant_response}\n\nUSER:\n{query_code}"` and returns it as the attack prompt, to be sent as a single message by the jbfoundry framework.
   - **Impact**: Semantically similar but not equivalent: the model may not treat the segments as distinct conversational turns, and system vs. user vs. assistant roles are only annotated in-band. This can lead to different behavior than the gold-standard multi-message setup, especially on safety behavior and in-context learning dynamics.

5. **No handling of long/compound prompts via splitting and multi-clause templates**
   - **Paper/Repo Citation**: Repo `translator.py`:47–79,111–165; `split_sentence_llms.py`.
   - **Expected Behavior**: For long sentences (e.g., >13 tokens), call `split_sentence_llms` to break them into sub-sentences, run `trans_sentence_llms` on each, and concatenate multiple `{Content, Category, Modifier}` triples into a single long program-like sentence (as illustrated by the "long example" in the prompts).
   - **Observed Behavior**: `generate_attack` and `extract_query_components` operate on the entire `goal` string as a single unit and generate only one `{Content, Category, Modifier}` triple and one template instantiation, regardless of length or complexity.
   - **Impact**: For simple, single-clause queries the behavior is aligned; for long or multi-intent queries, this under-approximates the reference algorithm by failing to decompose and chain multiple clauses, potentially weakening attack expressiveness.

6. **Missing `trans_verify` control and safety rephrasing behavior**
   - **Paper/Repo Citation**: Repo `translator.py`:13–22,38–45; `trans_llms.py`:123–151,191–200.
   - **Expected Behavior**: A boolean `--trans_verify` flag controls whether to run an additional safety check on each extracted phrase, and, if harmful, reverse the word order to reduce the chance that the intermediate phrases themselves trigger safety mechanisms.
   - **Observed Behavior**: `QueryAttackGen` has no corresponding parameter or logic; it neither exposes nor implements safety verification or phrase reversal.
   - **Impact**: The attack’s internal behavior differs from the gold-standard optioned behavior; depending on how `trans_verify` was used in experiments, this could materially change success/failure rates and interaction with safety filters.

## Extra Behaviors Not in Paper
- **Raising `ValueError` instead of retrying on invalid extraction**: `_validate_extraction_response` (`queryattack_gen.py`:725–749) raises a `ValueError` if any component is missing or contains banned terms, whereas the repo quietly re-queries the LLM until success. This defensive choice is not described in the paper or present in the reference code and may cause runs to fail outright rather than continue querying.
- **Use of a custom LLM wrapper (`LLMLiteLLM.from_config`) with fixed provider `"wenwen"`**: While the instructions state provider/API details are not part of fidelity, this is a code-level deviation from the repo’s direct OpenAI client usage. As long as the model name and sampling settings match, this is behaviorally acceptable.

## Required Changes to Reach 100%

1. **Implement robust extraction loop and safety verification logic**
   - **Files/Lines**: `src/jbfoundry/attacks/generated/queryattack_gen.py`:702–723,725–749.
   - **Changes**:
     - Wrap the LLM query and parsing in a loop that continues until valid components are obtained, mirroring `trans_sentence_llms` behavior (retry on parse failure).
     - Optionally add a configuration parameter analogous to `trans_verify` that, when enabled, calls a secondary safety-judging LLM on each component and applies word-reversal or similar transformation if deemed "harmful", matching the gold-standard semantics.
     - Enforce presence of `Risk Level` and `Violation Type` fields in the JSON and include them in validity checks (even if they are not returned to the caller).
   - **Justification**: Brings extraction behavior in line with the repo’s robustness and safety treatment, reducing divergence in component triples and error behavior.

2. **Add POS-based normalization of extracted components**
   - **Files/Lines**: `src/jbfoundry/attacks/generated/queryattack_gen.py`:725–749 (and potentially a helper method).
   - **Changes**:
     - After successful regex extraction, tokenize each component, run POS tagging (e.g., via `nltk.pos_tag`), and remove function words and specified POS tags as in `trans_llms.py`:157–171.
     - Return the cleaned components in the final `{"Content", "Category", "Modifier"}` dict.
   - **Justification**: Ensures that the structured queries have the same phrasing and granularity as in the reference implementation, improving fidelity of the generated program-like sentences.

3. **Align conversation structure with the multi-turn design**
   - **Files/Lines**: `src/jbfoundry/attacks/generated/queryattack_gen.py`:758–796.
   - **Changes**:
     - Where the surrounding framework allows, represent the attack as a sequence of messages with explicit roles (system, user, assistant, user), rather than a single flattened string; or, at minimum, provide a structured representation that can be converted into the same sequence used in the repo’s `test.py`.
     - If constrained to a single string, document this deviation clearly and consider adding guidance in the attack metadata so evaluation code can reconstruct multi-turn messages.
   - **Justification**: Better matches the paper’s in-context learning setting and the repo’s evaluation setup, particularly with respect to safety and alignment behaviors.

4. **Support long/compound prompts via splitting and multi-clause generation**
   - **Files/Lines**: `src/jbfoundry/attacks/generated/queryattack_gen.py`:702–723,751–779.
   - **Changes**:
     - Optionally integrate a sentence-splitting step (LLM-based or heuristic) for long queries and iterate `extract_query_components` + `fill_query_template` over each sub-sentence, concatenating multiple template instances into a single `query_code` string, as done in `translator.py`.
   - **Justification**: Restores the ability to handle complex multi-intent prompts in the same way as the reference implementation and as illustrated by the "long example" sections in the context prompts.

5. **Expose a configuration equivalent to `trans_verify`**
   - **Files/Lines**: `src/jbfoundry/attacks/generated/queryattack_gen.py`:30–52,687–700,702–723.
   - **Changes**:
     - Add an `AttackParameter` (e.g., `trans_verify: bool = False`) that controls whether to run the safety-verification and rephrasing logic described above.
   - **Justification**: Ensures that experiments can reproduce both the default and safety-verified modes from the original QueryAttack codebase.

## Final Verdict
Given the deviations in extraction robustness, missing post-processing, and differences in conversation structure and long-prompt handling, the implementation is **Not 100% Fidelity** relative to the paper and the gold-standard QueryAttack repository, even though the main high-level algorithmic steps and templates are correctly captured.


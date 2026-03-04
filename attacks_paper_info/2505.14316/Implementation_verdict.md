# Audit Iteration 2 - 2025-12-30

### Changes Since Previous Iteration

**Prior Issues Status:**
| Issue from Previous Audit | Previous Status | Current Status | Notes |
|---|---|---|---|
| Missing WordNet-based noun expansion | ❌ | ✅ Fixed | `semantic_expansion` now pulls noun synset definition and lemma (`ice_gen.py:333–360`). |
| Omitted explicit dependency-graph modification | ❌ | ✅ Fixed | Cuts non-preserved edges in `children_map` before propagation (`ice_gen.py:210–233`). |
| Simplified breakpoint logic without preserved dependencies | ❌ | ✅ Fixed | Breakpoints skip preserved edges and merge levels when crossed (`ice_gen.py:234–269`). |
| Extra default `modification_ratio` (0.5 vs random) | ❌ | ✅ Fixed | Default is `None`, selecting random size in `[1, |W_verbs|]` (`ice_gen.py:198–205`). |

**Regression Check:**
| Component | Prior Status | Current Status | Notes |
|---|---|---|---|
| Four-stage pipeline orchestration | ✅ | ✅ | `generate_attack` still sequences all four steps (`ice_gen.py:128–165`). |
| Reasoning mask placeholders and shuffle | ✅ | ✅ | Grouping, explanations, and shuffle unchanged (`ice_gen.py:392–420`). |
| Environmental construction QA/TextGen prompts | ✅ | ✅ | Templates remain intact (`ice_gen.py:435–449`). |
| Sentiment analysis with DistilBERT | ✅ | ✅ | Pipeline initialization and use unchanged (`ice_gen.py:117–120`, `317–320`). |

**NEW Issues Found This Iteration:**
- None.

**Summary:**
- Fixed: 4 issues
- Partially Fixed: 0 issues
- Still Broken: 0 issues
- Regressions: 0 issues
- New Issues: 0 issues

# Implementation Fidelity Verdict (Iteration 2)
- Paper ID: 2505.14316
- Attack: ice_gen
- Verdict: 100% Fidelity
- Coverage: 20/20 components (100%)
- Iteration: 2

## Executive Summary
All prior fidelity gaps are resolved. The implementation now follows the plan: dependency edges are cut for non-preserved relations, breakpoints respect preserved dependencies, verb selection uses a random subset when no ratio is provided, and noun expansion leverages WordNet definitions plus related lemmas. No regressions or new issues were found; behavior aligns with the planned four-stage ICE pipeline.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| Overview / Execution Flow | Four-step pipeline: Hierarchical Split → Semantic Expansion → Reasoning Mask → Environmental Construction | `src/jbfoundry/attacks/generated/ice_gen.py:128–165` | ✅ | `generate_attack` orchestrates steps and returns final prompt. |
| Hierarchical Split – Step 1 | Identify verbs with parent & children (`W_verbs`) | `src/jbfoundry/attacks/generated/ice_gen.py:183–196` | ✅ | spaCy dependency graph builds children map; selects verbs with head and children. |
| Hierarchical Split – Step 2 | Randomly select subset size U[1, |W_verbs|] (or ratio) | `src/jbfoundry/attacks/generated/ice_gen.py:198–205` | ✅ | Default `modification_ratio=None` → random size; ratio respected if provided. |
| Hierarchical Split – Step 3 | Modify dependencies for non-preserved relations; increment verb + descendants | `src/jbfoundry/attacks/generated/ice_gen.py:210–233` | ✅ | Cuts edge when `dep_` not in `R_preserved`, then increments verb and all descendants in modified graph. |
| Hierarchical Split – Step 4 | Breakpoints on level changes with preserved-edge constraint | `src/jbfoundry/attacks/generated/ice_gen.py:234–269` | ✅ | Adds breakpoint only if no preserved dependency crosses; merges levels when crossed. |
| Hierarchical Split – Step 5 | Random pairing of breakpoints; increment levels in ranges | `src/jbfoundry/attacks/generated/ice_gen.py:270–287` | ✅ | Random number of pairs sampled; tokens in each range get +1 level. |
| Hierarchical Split – Step 6 | Normalize levels to contiguous naturals | `src/jbfoundry/attacks/generated/ice_gen.py:288–297` | ✅ | Maps unique levels to 1..m and returns `(word, level)` list. |
| Semantic Expansion – Step 1 | Build verb set V and noun set N | `src/jbfoundry/attacks/generated/ice_gen.py:311–314` | ✅ | Uses spaCy POS tags; verbs lemmatized. |
| Semantic Expansion – Step 2 | Sentiment label via DistilBERT | `src/jbfoundry/attacks/generated/ice_gen.py:317–320` | ✅ | Sentiment pipeline returns label added to `E`. |
| Semantic Expansion – Step 3 (verbs) | WordNet synonym for random verb | `src/jbfoundry/attacks/generated/ice_gen.py:322–332` | ✅ | Synsets queried with `pos=VERB`; random lemma added. |
| Semantic Expansion – Step 3 (nouns) | WordNet definition → noun phrase + related noun | `src/jbfoundry/attacks/generated/ice_gen.py:333–360` | ✅ | Parses synset definition, takes noun chunk or fallback, and adds related lemma. |
| Semantic Expansion – Steps 4–5 | Toxic word selection and adjectives via LLM | `src/jbfoundry/attacks/generated/ice_gen.py:361–376` | ✅ | LLM picks most toxic word, then generates three adjectives; all added to `E`. |
| Semantic Expansion – Set construction | Aggregate sentiment, verb synonym, noun phrase, toxic word, adjectives | `src/jbfoundry/attacks/generated/ice_gen.py:317–376` | ✅ | `E` collects all elements as specified. |
| Reasoning Mask – Segmentation | Group words by level; assign placeholders | `src/jbfoundry/attacks/generated/ice_gen.py:392–411` | ✅ | Builds segments and `[PART_k]` explanations. |
| Reasoning Mask – Expansion explanations & shuffle | Add expansion sentences; shuffle and join | `src/jbfoundry/attacks/generated/ice_gen.py:412–420` | ✅ | Adds “Consider the concept” sentences, shuffles, and concatenates. |
| Environmental Construction – QA | QA-style reconstruction prompt | `src/jbfoundry/attacks/generated/ice_gen.py:435–441` | ✅ | Embeds S' and requests reconstruction + answer. |
| Environmental Construction – TextGen | Text generation reconstruction prompt | `src/jbfoundry/attacks/generated/ice_gen.py:442–449` | ✅ | TextGen variant mirrors QA structure. |
| Execution I/O | Input S (goal/prompt), output final prompt | `src/jbfoundry/attacks/generated/ice_gen.py:128–165` | ✅ | Uses goal as S; returns constructed prompt. |
| Parameters – Scenario | `scenario` choice QA/TextGen | `src/jbfoundry/attacks/generated/ice_gen.py:64–70` | ✅ | Choices enforced via `AttackParameter`. |
| Parameters – Models/ratio | `sentiment_model`, `toxicity_model/provider`, `modification_ratio` | `src/jbfoundry/attacks/generated/ice_gen.py:56–92`, `198–205` | ✅ | Defaults match plan; ratio optional. |

## Parameter Mapping
| Paper Parameter | Code Parameter | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Scenario (`QA`/`TextGen`) | `scenario` | str | `"QA"` | ✅ | Choices enforced. |
| Sentiment model | `sentiment_model` | str | `"distilbert-base-uncased-finetuned-sst-2-english"` | ✅ | Matches plan default. |
| Toxicity model | `toxicity_model` | str | `"gpt-4o-mini"` | ✅ | Configurable as in plan. |
| Toxicity provider | `toxicity_provider` | str | `"wenwen"` | ✅ | Exposed parameter. |
| Verb subset size | `modification_ratio` | float/None | `None` | ✅ | None → random size in `[1, |W_verbs|]`; ratio honored if set. |

## Misalignments / Missing Items
- None.

## Extra Behaviors Not in Paper
- Dependency checks with informative ImportErrors for spaCy/WordNet/transformers (`ice_gen.py:102–108`).
- Logging statements for step progress (`ice_gen.py:144–163`, `296–378`).
- Seed setting from global args if provided (`ice_gen.py:98–101`).

## Required Changes to Reach 100%
- None. Implementation aligns with the plan and framework contracts.

## Final Verdict
100% Fidelity

# Implementation Fidelity Verdict
- Paper ID: 2505.14316
- Attack: ice_gen
- Verdict: Not 100% Fidelity
- Coverage: 20/20 components (100%)
- Iteration: 1

## Executive Summary
The current `ICEAttack` implementation in `ice_gen.py` closely follows the four-stage pipeline described in the ICE blueprint (Hierarchical Split → Semantic Expansion → Reasoning Mask → Environmental Construction), including the use of DistilBERT, WordNet, and an LLM for toxicity analysis. However, there are several fidelity gaps: (1) the hierarchical split omits the explicit dependency-graph modification step and uses a simplified breakpoint heuristic; (2) semantic expansion does not use WordNet (or any semantic resource) to expand nouns, only verbs; and (3) some hyperparameters and prompt templates deviate slightly from the described method. These issues affect the exact semantics of the algorithm, so the implementation cannot be judged as 100% faithful to the paper, although it is structurally and conceptually very close.

## Coverage Table
| Paper Section/Step | Paper Algorithm Component | Code Location (file:line-start–line-end) | Status (✅/⚠️/❌) | Notes |
|---|---|---|---|---|
| §Overview / Execution Flow | Four-step ICE pipeline: Hierarchical Split → Semantic Expansion → Reasoning Mask → Environmental Construction | `src/jbfoundry/attacks/generated/ice_gen.py:128–162` | ✅ | `generate_attack` orchestrates exactly these four steps in the same order and returns the final prompt. |
| §1 Hierarchical Split – Step 1 | Identify non-root verbs with both parent and child nodes in dependency graph | `src/jbfoundry/attacks/generated/ice_gen.py:177–188` | ✅ | Uses spaCy parse; selects tokens with `pos_ == "VERB"` having a head and at least one child, matching the described set \(W_{verbs}\). |
| §1 Hierarchical Split – Steps 2–3 | Randomly select subset of these verbs, modify dependencies, increment their level and propagate to children | `src/jbfoundry/attacks/generated/ice_gen.py:189–209` | ⚠️ | Random subset and level increment with descendant propagation are implemented, but the explicit `modify_dependencies(w, G)` step on the dependency graph is omitted. |
| §1 Hierarchical Split – Steps 4–5 | Define breakpoints from level changes and preserved dependencies; pair breakpoints and increment levels within segments | `src/jbfoundry/attacks/generated/ice_gen.py:210–225` | ⚠️ | Breakpoints are defined purely from adjacent level changes; segments between consecutive breakpoints are incremented, but there is no explicit use of preserved dependency relations as in the text description. |
| §1 Hierarchical Split – Step 6 | Normalize hierarchical levels to contiguous natural numbers and return list of \((word, level)\) | `src/jbfoundry/attacks/generated/ice_gen.py:227–236` | ✅ | Computes sorted unique levels, remaps to contiguous integers, and returns `L = [(token.text, normalized_level)]`. |
| §2 Semantic Expansion – Steps 1–2 | Construct verb and noun sets from prompt; predict sentiment with DistilBERT | `src/jbfoundry/attacks/generated/ice_gen.py:248–259`, `116–118` | ✅ | Builds verb/noun sets from spaCy POS tags and uses a DistilBERT-based sentiment-analysis pipeline (default model matches blueprint). |
| §2 Semantic Expansion – Step 3 (verbs) | Retrieve semantically related words for a randomly selected verb using WordNet | `src/jbfoundry/attacks/generated/ice_gen.py:261–271`, `27–32` | ✅ | Samples a random verb, fetches verb synsets from WordNet, and adds a random lemma name as the related verb. |
| §2 Semantic Expansion – Step 3 (nouns) | Retrieve semantically related words for a randomly selected noun using WordNet | `src/jbfoundry/attacks/generated/ice_gen.py:272–277` | ❌ | Selects a noun and adds it directly to `E`, but does not use WordNet or any semantic resource to generate related nouns as described. |
| §2 Semantic Expansion – Steps 4–5 | Analyze toxicity over V and N to find most toxic word; generate descriptive words with LLM | `src/jbfoundry/attacks/generated/ice_gen.py:278–293`, `120–126` | ✅ | Uses `toxicity_llm` to pick the most toxic word from `V+N` and then to produce three descriptive adjectives, all added into `E`. |
| §2 Semantic Expansion – Set construction | Build expansion set \(E = \{e_s, r_v, t_n\} \cup O \cup \{d\}\) | `src/jbfoundry/attacks/generated/ice_gen.py:254–295` | ✅ | Sentiment label, verb synonym, chosen noun, toxic word, and its adjectives are aggregated into the set `E`. |
| §3 Reasoning Mask – Steps 1–2 | Group words into segments by hierarchical level and assign placeholders | `src/jbfoundry/attacks/generated/ice_gen.py:298–324` | ✅ | Groups words into `segments[level]` and assigns placeholders of the form `[PART_{level}]`. |
| §3 Reasoning Mask – Step 3 | Generate explanation sentences for each placeholder and each semantic expansion | `src/jbfoundry/attacks/generated/ice_gen.py:325–333` | ✅ | Forms sentences like `"[PART_k] represents the phrase: '...'"` and `"Consider the concept: 'expansion'"` for all segments and `E`. |
| §3 Reasoning Mask – Step 4 | Randomly order and concatenate explanation sentences into dispersed representation \(S'\) | `src/jbfoundry/attacks/generated/ice_gen.py:334–337` | ✅ | Shuffles explanation list and joins them with periods to form `S_prime`. |
| §4 Environmental Construction – QA scenario | Embed \(S'\) into QA-style prompt with reconstruction and question answering | `src/jbfoundry/attacks/generated/ice_gen.py:341–357` | ✅ | Constructs a QA-system prompt asking to reconstruct the sentence from fragments and then answer the implied question/request, consistent with the described QA scenario. |
| §4 Environmental Construction – TextGen scenario | Embed \(S'\) into text-generation prompt with reconstruction | `src/jbfoundry/attacks/generated/ice_gen.py:359–364` | ✅ | Constructs a TextGen prompt instructing reconstruction of the sentence and response to the reconstructed request, matching the TextGen variant. |
| §Execution Flow – I/O | Input S as original prompt; output final prompt for querying LLM | `src/jbfoundry/attacks/generated/ice_gen.py:128–165` | ✅ | Uses `goal` (or `prompt` fallback) as S, runs all four stages, and returns `final_prompt` for downstream querying. |
| §Model Roles – DistilBERT | DistilBERT used for sentiment analysis of S | `src/jbfoundry/attacks/generated/ice_gen.py:116–118`, `248–259` | ✅ | Initializes a DistilBERT-based sentiment pipeline with the blueprint’s default model and uses it once per attack. |
| §Model Roles – WordNet | WordNet used to retrieve semantically related words | `src/jbfoundry/attacks/generated/ice_gen.py:27–32`, `261–271` | ⚠️ | WordNet is used to expand verbs but not nouns; partial coverage of the intended semantic expansion behavior. |
| §Model Roles – LLM | LLM used for toxicity analysis and generating descriptive words | `src/jbfoundry/attacks/generated/ice_gen.py:120–126`, `278–293` | ✅ | `LLMLiteLLM` instance is used to identify the most toxic word and to generate descriptive adjectives, as described. |
| §Attack Artifacts | Single-query execution (no restarts/beam search) | `src/jbfoundry/attacks/generated/ice_gen.py:128–165` | ✅ | The attack produces a single transformed prompt; no additional sampling loops or search control are embedded in the attack class. |

## Parameter Mapping
| Paper Parameter | Code Parameter / Mechanism | Type | Default | Match (✅/❌) | Notes |
|---|---|---|---|---|---|
| Scenario `scenario ∈ {QA, TextGen}` | `scenario` in `ICEAttack.PARAMETERS` | `str` | `"QA"` | ✅ | Exposes the same two scenarios as the paper, with QA as default. |
| Sentiment model (DistilBERT) | `sentiment_model` in `ICEAttack.PARAMETERS` | `str` | `"distilbert-base-uncased-finetuned-sst-2-english"` | ✅ | Default matches the DistilBERT sentiment model referenced in the blueprint; can be overridden via CLI. |
| Toxicity analysis LLM (e.g., GPT-4o) | `toxicity_model` in `ICEAttack.PARAMETERS` | `str` | `"gpt-4o-mini"` | ✅ | Uses a GPT-4o-family model; name differs slightly (`-mini`), but role and behavior match the described LLM toxicity analysis. |
| Toxicity provider / API | `toxicity_provider` in `ICEAttack.PARAMETERS` | `str` | `"wenwen"` | ✅ | Paper leaves provider unspecified; implementation cleanly parameterizes this. |
| WordNet lexical resource | Import `from nltk.corpus import wordnet` | module | N/A (hard-coded) | ✅ | WordNet is directly imported and used, consistent with the blueprint. |
| Hierarchical modification / subset size | `modification_ratio` in `ICEAttack.PARAMETERS` | `float` | `0.5` | ❌ | Paper describes a random subset but does not define a ratio; this is an extra hyperparameter controlling how many verbs are modified. |
| Expansion set \(E\) | `E` in `semantic_expansion` | `Set[str]` | N/A | ✅ | E aggregates sentiment label, verb synonym, noun, toxic word, and adjectives as in the blueprint (with partial noun semantics, see misalignments). |

## Misalignments / Missing Items

1. **Missing WordNet-based expansion for nouns (Semantic Expansion Step 3 for nouns)**  
   - **Paper citation**: §2 Semantic Expansion, Step 3 – “Retrieve semantically related words for a randomly selected verb and noun using WordNet.”  
   - **Expected behavior**: After selecting a representative noun phrase, the algorithm should use WordNet (or a similar lexical resource) to retrieve semantically related nouns and include them in the expansion set \(E\).  
   - **Observed behavior**: In `semantic_expansion`, the implementation picks a noun (`t_n`) and adds it directly to `E` without querying WordNet or any semantic resource for related nouns (`ice_gen.py:272–277`). Only verbs are expanded via WordNet.  
   - **Impact**: This reduces the semantic diversification for noun concepts and deviates from the described algorithm, potentially weakening obfuscation compared to the paper’s method.

2. **Omitted explicit dependency-graph modification in Hierarchical Split**  
   - **Paper citation**: §1 Hierarchical Split, Steps 2–3 – pseudocode `modify_dependencies(w, G)` followed by hierarchical level updates and propagation.  
   - **Expected behavior**: For each selected verb, its dependencies in the graph \(G\) are modified (e.g., re-wired or perturbed) before updating levels, with changes then propagated to child nodes. This implies that the structural dependency graph itself is altered as part of intent concealment.  
   - **Observed behavior**: The implementation increments levels for selected verbs and recursively for their descendants (`ice_gen.py:197–208`) but does not modify the underlying dependency graph or reflect any edge-level changes—there is no equivalent to `modify_dependencies(w, G)`. Breakpoints and segments are derived purely from level differences across linear token positions.  
   - **Impact**: While the level-based segmentation still provides a hierarchical split, it may not reflect the structural dependency modifications intended by the algorithm, leading to a semantic deviation from the paper’s described mechanism.

3. **Simplified breakpoint definition without explicit use of “preserved dependencies”**  
   - **Paper citation**: §1 Hierarchical Split, Step 4 – “Define breakpoints for hierarchical splitting based on level changes and preserved dependencies.”  
   - **Expected behavior**: Breakpoints should account both for hierarchical level changes and explicit conditions on preserved or broken dependency relations, as suggested by the textual description.  
   - **Observed behavior**: Breakpoints are defined solely when the numeric level changes between adjacent tokens (`levels[i] != levels[i + 1]`, `ice_gen.py:213–215`); there is no use of dependency edges or a condition referring to preserved dependencies.  
   - **Impact**: This heuristic may approximate the intended behavior but does not incorporate dependency constraints mentioned in the paper, potentially changing the segmentation structure in non-trivial sentences.

4. **Extra hyperparameter `modification_ratio` not described in the paper**  
   - **Paper citation**: §1 Hierarchical Split, Step 2 – “Randomly select a subset of these verbs and modify their dependency relations.” (no explicit ratio or tuning parameter given).  
   - **Expected behavior**: The paper leaves the size of the random subset conceptually unspecified; any fixed or implicit scheme would be acceptable if it matches or is clearly justified by the original implementation.  
   - **Observed behavior**: The implementation introduces a user-facing hyperparameter `modification_ratio` controlling how many verbs are modified (`ice_gen.py:189–192`, `56–63`), defaulting to 0.5. At least one verb is always modified when any exist.  
   - **Impact**: This additional control can change the strength of the hierarchical perturbation compared to the paper’s unspecified default. While practically useful, it is a semantic deviation unless it matches the original authors’ default configuration.

## Extra Behaviors Not in Paper
- **Logging and dependency validation**: The implementation performs structured logging and raises explicit `ImportError`s if `spacy`, `wordnet`, or `transformers` are unavailable (`ice_gen.py:18–39`, `102–108`), which are engineering conveniences not discussed in the paper but do not alter attack semantics when dependencies are present.  
- **Configurable model names/providers**: The toxicity and sentiment models, as well as the provider, are exposed as configurable parameters (`PARAMETERS` dict in `ice_gen.py:56–92`), whereas the paper only gives example models (e.g., DistilBERT, GPT-4o). These additions mainly increase flexibility but can alter behavior if users deviate from the reference models.  
- **More verbose environmental prompts**: The QA and TextGen prompts include more detailed instructions (e.g., “answer the implied question or request”, “provide a complete response”) than the minimal forms shown in the blueprint pseudocode (`ice_gen.py:352–364`). This likely affects style rather than the core attack logic but is still a behavioral extension.

## Required Changes to Reach 100%

1. **Implement WordNet-based semantic expansion for nouns**  
   - **File / Location**: `src/jbfoundry/attacks/generated/ice_gen.py:272–277`.  
   - **Change**: After selecting the representative noun (or noun phrase), query WordNet for noun synsets (e.g., `wordnet.synsets(noun, pos=wordnet.NOUN)`), sample one or more lemma names, and add these related nouns to `E` in addition to `t_n`. This should mirror the verb expansion logic and fully realize “semantically related words for a randomly selected verb and noun”.  
   - **Justification**: Aligns the noun side of Semantic Expansion Step 3 with §2 of the paper and the provided pseudocode.

2. **Introduce an explicit dependency-graph modification step (or a documented equivalent)**  
   - **File / Location**: `src/jbfoundry/attacks/generated/ice_gen.py:189–209`.  
   - **Change**: Either (a) construct an explicit dependency graph \(G\) from spaCy tokens and implement a `modify_dependencies`-style transformation for each selected verb (e.g., reassigning heads or restructuring local subtrees in a separate graph representation), or (b) clearly document and encode an equivalent transformation on hierarchical levels that can be justified as behaviorally matching the original `modify_dependencies(w, G)` design.  
   - **Justification**: Restores the structural manipulation described in §1 Hierarchical Split Steps 2–3, ensuring the algorithm’s dependency-level behavior matches the paper.

3. **Refine breakpoint logic to incorporate dependency constraints or document equivalence**  
   - **File / Location**: `src/jbfoundry/attacks/generated/ice_gen.py:210–225`.  
   - **Change**: Extend breakpoint detection to use both level changes and explicit conditions on dependencies (e.g., breaks when level changes *and* the dependency relation crosses a modified edge, or when certain dependency types are preserved), or provide a clearly documented rationale that the current linear-level heuristic is mathematically equivalent to the paper’s intended breakpoint rule.  
   - **Justification**: Brings Step 4 (“based on level changes and preserved dependencies”) into closer alignment with the algorithm described in §1.

4. **Clarify or align `modification_ratio` with the paper’s default behavior**  
   - **File / Location**: `src/jbfoundry/attacks/generated/ice_gen.py:56–63`, `189–192`.  
   - **Change**: Either (a) set `modification_ratio` to the value used in the original implementation (if known) and document that this matches the paper’s experiments, or (b) update documentation/comments to explain that this is an added tuning parameter beyond the paper’s description and specify a default corresponding to the authors’ intended behavior.  
   - **Justification**: Ensures users of the attack understand how this extra parameter relates to the original algorithm and can reproduce paper settings.

## Final Verdict
Given the missing WordNet-based noun expansion, the absence of an explicit dependency-graph modification step, and the simplified breakpoint logic that omits preserved-dependency conditions, the implementation is **Not 100% Fidelity** to the ICE attack as described in the paper, although it remains structurally and conceptually very close.


# JBF-FORGE: Multi-Agent Paper-to-Attack Workflow

Automated system for translating jailbreak research papers into executable attack modules.

## Overview

**JBF-FORGE** implements a multi-agent workflow that converts research papers into attack implementations compatible with JBF-LIB. From the paper: 28.2 minute average synthesis time, +0.26pp mean ASR deviation from reported results, 100% coverage verification through iterative auditing.

## Architecture

```
┌─────────────┐
│   Paper     │
│   (PDF)     │
└──────┬──────┘
       │
       ↓
┌─────────────┐      ┌──────────────┐
│Preprocessor │ ───→ │   Markdown   │
└─────────────┘      └──────┬───────┘
                            │
       ┌────────────────────┴────────────────────┐
       │         JBF-FORGE Workflow              │
       │                                          │
       │  ┌──────────┐    ┌──────────┐          │
       │  │ Planner  │───→│  Coder   │←─┐       │
       │  └──────────┘    └────┬─────┘  │       │
       │                       │         │       │
       │                       ↓         │ Fail  │
       │                 ┌──────────┐   │       │
       │                 │ Auditor  │───┘       │
       │                 └────┬─────┘           │
       │                      │                 │
       │                 Pass │                 │
       └──────────────────────┼─────────────────┘
                              │
                              ↓
                    ┌─────────────────┐
                    │ Attack Module   │
                    │ + Tests         │
                    └─────────────────┘
```

## Agents

### 1. Planner

Extracts algorithm specification and creates implementation blueprint.

**Inputs**: Paper markdown, reference repository (if available), JBF-LIB contracts

**Outputs**: Implementation plan with algorithm steps, prompts/templates, parameter mappings

**Key Responsibilities**:
- Extract ALL prompts from paper (especially appendices)
- Map paper algorithm to JBF-LIB contracts
- Resolve ambiguities using reference code
- Document paper-repo divergences

### 2. Coder

Synthesizes executable attack implementation from plan.

**Inputs**: Implementation plan, JBF-LIB contracts, reference repository (optional), audit feedback (during refinement)

**Outputs**: Attack class in `src/jbfoundry/attacks/generated/`, unit test script, coverage analysis

**Requirements**:
- NAME must end with `_gen` suffix
- File name must match NAME exactly
- Every paper step must have corresponding code
- No try/except around LLM calls (let errors propagate)

### 3. Auditor

Verifies 100% coverage and contract compliance through static analysis.

**Inputs**: Implementation plan, generated attack code, JBF-LIB contracts, reference repository (when available)

**Outputs**: Binary acceptance verdict, line-referenced coverage report, actionable revision instructions

**Acceptance Condition**: `fidelity = 100%` (no missing components, no semantic deviations)

**Source-of-Truth Hierarchy**: 1) Implementation plan, 2) JBF-LIB contracts, 3) Reference repository

## Workflow

From paper Algorithm 1:

```python
def forge_attack(paper, max_iterations=5):
    # 1. Preprocessing
    markdown = preprocess_paper(paper)
    repo = retrieve_repo(paper)  # if available

    # 2. Planning
    plan = planner.create_plan(markdown, repo, JBF_LIB_contracts)

    # 3. Initial coding
    module = coder.implement(plan, repo)

    # 4. Iterative refinement
    for iteration in range(max_iterations):
        accepted, feedback = auditor.verify(module, plan, repo)

        if accepted:
            break

        if iteration < max_iterations - 1:
            module = coder.refine(plan, repo, feedback)

    # 5. Matched evaluation
    config = extract_paper_config(paper)
    asr_gen = evaluate(module, config)

    # 6. Optional refinement if large gap
    if asr_gen - asr_paper < -10.0:
        module = enhanced_refinement(module, plan, repo)

    return module, asr_gen - asr_paper
```

## Usage

### Basic Usage

```bash
# Translate paper from ArXiv ID
python agents/run_paper_to_attack.py \
    --arxiv_id 2310.08419 \
    --output_dir attacks_paper_info/
```

### Output Structure

```
attacks_paper_info/
└── {arxiv_id}/
    ├── {arxiv_id}.pdf                    # Downloaded paper
    ├── {arxiv_id}.md                     # Processed markdown
    ├── {arxiv_id}_implementation_plan.md # Planner output
    ├── coverage_analysis.md              # Coder output
    ├── Implementation_verdict.md         # Auditor output
    └── src/jbfoundry/attacks/generated/
        └── {attack_name}_gen.py          # Final module
```

## Implementation Requirements

### Attack Structure

```python
from ..base import ModernBaseAttack, AttackParameter
from ...llm.litellm import LLMLiteLLM

class ExampleAttack(ModernBaseAttack):
    """Brief description from paper."""

    NAME = "example_gen"  # Must end with _gen
    PAPER = "Author et al. - Paper Title (Venue Year)"

    PARAMETERS = {
        "param": AttackParameter(
            name="param",
            param_type=int,
            default=5,
            description="Parameter description",
            cli_arg="--param"
        )
    }

    def generate_attack(self, prompt: str, goal: str,
                       target: str, **kwargs) -> str:
        """Generate adversarial prompt."""
        # Implement paper algorithm
        return modified_prompt
```

### Critical Rules

1. **No Error Masking**: Never catch LLM call exceptions - let them propagate
2. **Attack vs Evaluation**: Expose algorithmic controls (restarts, attempts) as AttackParameter
3. **Caching**: Cache learned artifacts in `cache/{attack_name}/` for reuse

## Evaluation Fidelity

### With-Repo vs No-Repo (from paper Table/Figure)

Official repositories improve reproduction fidelity. From paper examples:
- **Template Attacks**: Minimal gain (EquaCode +0.3%)
- **Scaffold-Heavy Methods**: Large gains (GTA +48.6%, SATA-MLM +34.8%)
- **Mean Improvement**: +19.8pp when repository available

**Key Insight**: Repositories resolve implementation details (defaults, scaffolding) rather than core algorithms.

### Testing Generated Attacks

After generating an attack module, test it using `test_comprehensive.py`:

```bash
# Comprehensive test across multiple models and datasets
python src/jbfoundry/runners/test_comprehensive.py \
    --attack_name generated_attack_gen \
    --samples 50

# Quick smoke test on single model
python src/jbfoundry/runners/universal_attack.py \
    --attack_name generated_attack_gen \
    --model gpt-4o \
    --provider openai \
    --samples 5

# Use pre-configured test script (if created)
bash scripts/comprehensive_tests/attack/test_generated_attack_comprehensive.sh
```

See [CLI_REFERENCE.md](../docs/CLI_REFERENCE.md) for complete testing workflow documentation.

## Performance

From paper Section 4 and Appendix D:

| Stage | Observation |
|-------|-------------|
| **Planning** | ~4 minutes |
| **Coding** | ~20 minutes (dominated by test execution) |
| **Auditing (per iter)** | ~3.2 minutes |
| **Total (median)** | 25.0 minutes |

**82% of runs complete within 60 minutes**

## Troubleshooting

### Common Issues

1. **Missing Prompts**: Low ASR despite correct logic → Check paper appendices for template strings

2. **Audit Loop Timeout**: Iterations exhaust without acceptance → Check plan clarity and contract alignment

3. **Evaluation Gap**: Large negative ASR deviation (Δ < -10pp) → Trigger enhanced refinement pass

4. **Import Errors**: Module fails to load → Verify NAME matches filename

## Paper Preprocessor

PDF to markdown conversion using Mistral OCR via Vertex AI:

```bash
python agents/utils/paper_preprocessor.py \
    --pdf_path paper.pdf \
    --output_dir output/ \
    --service_account credentials.json
```

See [`agents/utils/README.md`](utils/README.md) for preprocessor details.

## References

See [arXiv:2602.24009](https://arxiv.org/pdf/2602.24009) for complete details:
- **Algorithm 1**: JBF-FORGE workflow (Section 3.2)
- **Appendix B**: Auditor acceptance criteria and fidelity metrics
- **Appendix C**: Iteration analysis and convergence patterns
- **Appendix D**: Performance benchmarks and complexity analysis
- **Appendices F-G**: Full agent prompts (Planner, Coder, Auditor)

**Related Documentation**:
- [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) - JBF-LIB contracts
- [utils/README.md](utils/README.md) - Paper preprocessor

---

**For research use**: See paper Section 4 for reproduction methodology and fidelity analysis.

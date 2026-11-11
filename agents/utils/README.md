# Agent Utilities

Utility modules supporting the JBF-FORGE multi-agent workflow.

## Paper Preprocessor

Pipeline for paper eligibility triage and optional PDF-to-markdown OCR via OpenAI-compatible API (LiteLLM proxy).

### Setup

Requires `IIIS_API_KEY` environment variable (LiteLLM virtual key).

```bash
export IIIS_API_KEY="sk-..."
```

API endpoint: `https://router.ai.iiis.co:9443/v1` (hardcoded default).

### Usage

```bash
# Full pipeline: abstract triage → deep triage → OCR
python agents/utils/paper_preprocessor.py --arxiv-id "2505.10066"

# PDF-only pipeline: triage/download PDF, skip OCR
python agents/utils/paper_preprocessor.py --arxiv-id "2505.10066" --skip-ocr

# Skip all triage (go straight to OCR)
python agents/utils/paper_preprocessor.py --arxiv-id "2505.10066" --skip-triage

# Skip abstract triage only (still run deep triage)
python agents/utils/paper_preprocessor.py --arxiv-id "2505.10066" --skip-abstract-triage

# Local PDF
python agents/utils/paper_preprocessor.py --local-pdf "path/to/paper.pdf"

# Custom model (default: bh/gemini-3.1-pro-preview)
python agents/utils/paper_preprocessor.py --arxiv-id "2505.10066" --model "bh/gemini-3.1-pro-preview"
```

### Pipeline Stages

1. **Abstract triage** — Fetches arXiv metadata (title + abstract), queries LLM to determine if the paper proposes a new black-box, text-only, CPU-runnable jailbreak attack method
2. **Deep triage** — Downloads PDF, sends first 8 pages to LLM to check for CPU-impractical operations (transformers, torch, PPL filtering, local model inference, gradient-based optimization)
3. **Full OCR** — Optional chunked PDF-to-markdown extraction (splits large PDFs into ≤10 page chunks of ≤5MB base64)

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success — markdown output written |
| 1 | Processing error (download, OCR, etc.) |
| 4 | Paper rejected by eligibility triage |

Exit code 4 lets the downstream attack workflow (`agents/workflows/attack.py`) skip ineligible papers without treating them as failures.

### Output

```
attacks_paper_info/{arxiv_id}/
├── {arxiv_id}.pdf        # Downloaded PDF
└── {arxiv_id}.md         # OCR markdown output, only when OCR is enabled
```

## Agent Runners

Pluggable agent backends in `agent_utils.py`:

- **ClaudeAgentRunner** — Claude Code CLI (`claude`), stream-json output parsing
- **CodexAgentRunner** — OpenAI Codex CLI (`codex --json`), JSONL output parsing

Factory: `create_agent_runner("claude" | "codex", repo_root)`.

Per-step agent selection via workflow config (`planner_agent`, `attack_agent`, `audit_agent`).

## Checkpoint System

Progress tracking for resumable workflows.

```python
from agents.utils.checkpoint import CheckpointManager

checkpoint = CheckpointManager(log_dir)
checkpoint.save_checkpoint(iteration=1, step_name="planner", attack_name="foo_gen")
state = checkpoint.load_last_checkpoint()
checkpoint.clear()
```

## Agent Utilities

Common helper functions in `agent_utils.py`:

- `build_prompt()` — Assemble structured prompts for agent execution
- `extract_json_result()` — Parse JSON result blocks from agent output
- `find_in_json()` — Recursively search nested dicts for a key (handles flat or nested agent responses)
- `validate_environment()` — Check agent binary and required files exist

---

**Status**: Production-ready | **Last Updated**: April 2026

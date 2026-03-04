# Agent Utilities

Utility modules supporting the JBF-FORGE multi-agent workflow.

## Paper Preprocessor

PDF to markdown conversion using Mistral OCR via Google Vertex AI.

### Setup

Requires Google Cloud service account with Vertex AI permissions.

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

### Usage

```bash
python agents/utils/paper_preprocessor.py \
    --pdf_path paper.pdf \
    --output_dir output/ \
    --service_account credentials.json
```

### Output

```
output/
├── paper.md              # Markdown text
├── figures/              # Extracted figures
│   └── fig_*.png
└── metadata.json         # Processing metadata
```

## Checkpoint System

Progress tracking for resumable workflows.

```python
from agents/utils/checkpoint import CheckpointManager

checkpoint = CheckpointManager("workflow_name", "output_dir/")
checkpoint.save({"step": "planning", "status": "in_progress"})
state = checkpoint.load()
checkpoint.clear()
```

## Agent Utilities

Common helper functions for agent coordination in `agent_utils.py`.

---

**Status**: Production-ready | **Last Updated**: January 2026

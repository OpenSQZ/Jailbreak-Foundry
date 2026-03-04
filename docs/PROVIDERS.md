# Model Provider Setup

Configuration guide for supported LLM providers in Jailbreak Foundry.

## Supported Providers

| Provider | Environment Variable | Notes |
|----------|---------------------|-------|
| `openai` | `OPENAI_API_KEY` | OpenAI models (GPT-4, GPT-3.5, etc.) |
| `anthropic` | `ANTHROPIC_API_KEY` | Claude models |
| `azure` | `AZURE_API_KEY`, `AZURE_API_BASE` | Azure OpenAI Service |
| `aliyun` | `DASHSCOPE_API_KEY` | Aliyun/Qwen models |
| `bedrock` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | AWS Bedrock |
| `vertex_ai` | `GOOGLE_APPLICATION_CREDENTIALS` | Google Vertex AI / Gemini |

## Basic Usage

### OpenAI

```bash
export OPENAI_API_KEY="sk-..."

python src/jbfoundry/runners/universal_attack.py \
    --model gpt-4o \
    --provider openai \
    --attack_name pair_gen
```

### Anthropic

```bash
export ANTHROPIC_API_KEY="sk-ant-..."

python src/jbfoundry/runners/universal_attack.py \
    --model claude-3-5-sonnet-20241022 \
    --provider anthropic \
    --attack_name tap_gen
```

### Azure OpenAI

```bash
export AZURE_API_KEY="..."
export AZURE_API_BASE="https://your-resource.openai.azure.com/"

python src/jbfoundry/runners/universal_attack.py \
    --model gpt-4o \
    --provider azure \
    --api_base "https://your-resource.openai.azure.com/" \
    --attack_name pair_gen
```

### Aliyun (Dashscope)

```bash
export DASHSCOPE_API_KEY="sk-..."

python src/jbfoundry/runners/universal_attack.py \
    --model qwen-max \
    --provider aliyun \
    --attack_name tap_gen
```

### AWS Bedrock

```bash
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"

python src/jbfoundry/runners/universal_attack.py \
    --model "us.anthropic.claude-3-5-sonnet-20241022-v2:0" \
    --provider bedrock \
    --attack_name pair_gen
```

### Google Vertex AI

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

python src/jbfoundry/runners/universal_attack.py \
    --model gemini-2.0-flash-exp \
    --provider vertex_ai \
    --attack_name tap_gen
```

## Local Models

You can use local models via OpenAI-compatible endpoints:

```bash
python src/jbfoundry/runners/universal_attack.py \
    --model llama-3-70b \
    --provider openai \
    --api_base http://localhost:8000/v1 \
    --api_key none \
    --attack_name abj_gen
```

**Note**: Requires an OpenAI-compatible API server running locally.

## Programmatic Access

```python
from jbfoundry.llm.litellm import LLMLiteLLM

# Create LLM instance
llm = LLMLiteLLM.from_config(
    provider="openai",
    model_name="gpt-4o",
    temperature=0.7,
    max_tokens=500
)

# Query the model
response = llm.query("Your prompt here")

# Query with multiple prompts
responses = llm.query([
    "Prompt 1",
    "Prompt 2",
    "Prompt 3"
])
```

### Provider-Specific Configuration

```python
# OpenAI with custom endpoint
llm = LLMLiteLLM.from_config(
    provider="openai",
    model_name="gpt-4o",
    api_key="sk-...",
    api_base="https://api.openai.com/v1"
)

# Anthropic
llm = LLMLiteLLM.from_config(
    provider="anthropic",
    model_name="claude-3-5-sonnet-20241022",
    api_key="sk-ant-..."
)

# Azure OpenAI
llm = LLMLiteLLM.from_config(
    provider="azure",
    model_name="gpt-4o",
    api_key="...",
    api_base="https://your-resource.openai.azure.com/"
)
```

## Troubleshooting

### Authentication Errors

```bash
# Verify environment variable is set
echo $OPENAI_API_KEY

# Re-export if needed
export OPENAI_API_KEY="sk-..."
```

### Rate Limit Errors

The LLM adapter includes built-in retry logic with exponential backoff:
- **Default retries**: 4 attempts
- **Backoff**: Exponential with jitter
- **Errors handled**: Rate limits, timeouts, transient failures

### Connection Errors

```bash
# Check network connectivity
curl https://api.openai.com/v1/models

# Check API key validity
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Provider-Specific Issues

**OpenAI**:
- Ensure model name is correct (e.g., `gpt-4o` not `gpt4o`)
- Check account quota and billing status

**Anthropic**:
- Use correct model identifier (e.g., `claude-3-5-sonnet-20241022`)
- Ensure API key starts with `sk-ant-`

**Azure**:
- Both `AZURE_API_KEY` and `AZURE_API_BASE` must be set
- API base should include the full resource URL

**Vertex AI**:
- Credentials file must be valid JSON service account key
- Ensure project has Vertex AI API enabled

## Cost Tracking

JBF automatically tracks API costs:

```python
from jbfoundry.cost_tracker import CostTracker

# Get current session costs
tracker = CostTracker.get()
print(f"Tokens: {tracker.get_total_tokens()}")
print(f"Cost: ${tracker.get_total_cost():.4f}")
```

Cost tracking saves to `cost_tracking.json` in the results directory.

## References

- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md) for LLM adapter design
- **Paper**: Section 3.1 of [arXiv:2602.24009](https://arxiv.org/pdf/2602.24009)
- **Provider Documentation**:
  - [OpenAI API Documentation](https://platform.openai.com/docs)
  - [Anthropic API Documentation](https://docs.anthropic.com)
  - [Azure OpenAI Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
  - [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
  - [Google Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)

---

**Note**: Model availability, pricing, and configuration details are subject to change. Please verify with provider documentation.

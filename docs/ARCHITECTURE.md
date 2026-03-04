# JBF-LIB Architecture Guide

Comprehensive guide to the Jailbreak Foundry framework core (JBF-LIB) - the shared library that underpins attack synthesis and evaluation.

## Overview

**JBF-LIB** is the foundation of Jailbreak Foundry, providing:
- **Stable contracts** for attacks and defenses
- **Reusable infrastructure** for LLM access, caching, and logging
- **Registry system** for auto-discovery and lazy loading
- **Thread-safe execution** with isolated per-run state

**Code Reuse**: 82.5% of integrated codebase is shared JBF-LIB infrastructure, leaving only 17.5% attack-specific implementation.

## Core Components

### 1. Attack Contract (`ModernBaseAttack`)

Base class defining the attack interface that all implementations must follow.

#### Minimal Class Structure

```python
from .base import ModernBaseAttack, AttackParameter

class ExampleAttack(ModernBaseAttack):
    """Attack description (docstring)."""

    # Essential attributes (only 3 required)
    NAME = "example_attack"
    PAPER = "Author et al. - Title (Year)"
    PARAMETERS = {
        "param": AttackParameter(...)
    }

    def generate_attack(self, prompt: str, goal: str,
                       target: str, **kwargs) -> str:
        """Generate adversarial prompt."""
        return modified_prompt
```

#### Essential Attributes

1. **NAME** (str)
   - Unique identifier for registry lookup
   - Used in CLI: `--attack_name NAME`
   - Convention: lowercase with underscores
   - Generated attacks: append `_gen` suffix

2. **PAPER** (str)
   - Citation for academic context
   - Format: "Authors - Title (Venue Year)"
   - Used in result reporting and metadata

3. **PARAMETERS** (Dict[str, AttackParameter])
   - Self-documenting parameter definitions
   - Enables CLI auto-generation
   - Supports type validation and defaults

#### Core Methods

**`generate_attack()`** - Primary entry point
```python
def generate_attack(self, prompt: str, goal: str,
                   target: str, **kwargs) -> str:
    """
    Generate adversarial prompt for given input.

    Args:
        prompt: Original user prompt/query
        goal: Attack goal (e.g., "Write harmful content")
        target: Expected model response prefix
        **kwargs: Additional context
            - attempt_index: Current attempt (1-based)
            - attempts_per_query: Total attempts per query
            - attempt_success_threshold: Success threshold

    Returns:
        Modified prompt designed to bypass safety measures
    """
    pass
```

**`get_parameter_value()`** - Parameter access
```python
param = self.get_parameter_value("param_name")
# Priority: CLI args > kwargs > defaults
```

**`get_config()`** - Metadata export
```python
config = attack.get_config()
# Returns: {'name': '...', 'paper': '...', 'parameters': {...}}
```

### 2. Parameter System (`AttackParameter`)

Self-documenting parameter definitions with type safety and validation.

#### Parameter Definition

```python
AttackParameter(
    name="param_name",              # Internal name
    param_type=int,                 # Type: str, int, bool, float
    default=10,                     # Default value
    description="Parameter desc",   # Help text
    cli_arg="--param_name",        # CLI argument
    choices=None,                   # Valid values (optional)
    required=False,                 # Required flag (optional)
    validator=None                  # Custom validator (optional)
)
```

#### Type Support

- **str**: Text, paths, comma-separated lists
- **int**: Counts, indices, iteration limits
- **bool**: Flags, enable/disable options
- **float**: Thresholds, temperatures, probabilities

#### Validation

**Built-in**:
- Type checking against `param_type`
- Choice validation if `choices` specified
- Required parameter checking

**Custom Validators**:
```python
def validate_positive(value):
    return isinstance(value, int) and value > 0

"num_rounds": AttackParameter(
    name="num_rounds",
    param_type=int,
    default=5,
    validator=validate_positive
)
```

#### CLI Integration

Parameters automatically generate CLI arguments:
```bash
# Parameter definition
"temperature": AttackParameter(
    name="temperature",
    param_type=float,
    default=0.7,
    cli_arg="--temperature"
)

# Generated CLI
--temperature FLOAT    Sampling temperature (default: 0.7)
```

### 3. Registry System

Auto-discovery with lazy loading for efficient attack management.

#### Registry Architecture

```python
# AttackRegistry (src/jbfoundry/attacks/registry.py)
#
# The registry is instantiated once at import time and pre-scans the
# attacks/ tree for Python files. Attack *classes* are imported lazily.
from jbfoundry.attacks.registry import registry

# Load and return an attack class by name (lazy import + caching)
attack_cls = registry.get_attack("pair_gen")
```

#### Auto-Discovery

The registry automatically finds attacks by:
1. Scanning `src/jbfoundry/attacks/` recursively for `*.py` files
2. Recording file → module metadata without importing modules
3. Importing a module only when that attack is requested
4. Registering classes inheriting from `ModernBaseAttack` by `NAME`

**No manual registration required** - just create the class and it's available.

#### Lazy Loading

Attacks are imported only when requested:
```python
# List discovered attack *files* (no imports; internal metadata)
attack_files = sorted(registry._attack_metadata.keys())

# Get attack (imports only this attack)
attack_cls = registry.get_attack("pair_gen")

# Instantiate (caches for reuse)
attack = attack_cls(args=args)
```

**Benefits**:
- Fast startup time
- Reduced memory usage
- Isolated import errors

### 4. LLM Adapters

Provider-agnostic model access with response normalization and retry logic.

#### BaseLLM Interface

```python
from src.jbfoundry.llm.base import BaseLLM

class BaseLLM:
    """Abstract interface for LLM providers."""

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate single response."""

    def generate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate batch of responses."""

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
```

#### LLMLiteLLM Adapter

Primary adapter built on LiteLLM for broad provider support:

```python
from src.jbfoundry.llm.litellm import LLMLiteLLM

# Provider-agnostic instantiation
llm = LLMLiteLLM.from_config(
    provider="openai",           # openai, anthropic, azure, ...
    model_name="gpt-4o",
    temperature=0.7,
    max_tokens=500,
    api_base=None,              # Optional custom endpoint
    api_key=None                # Optional (uses env vars)
)

# Generate response
response = llm.generate("Hello world")

# Batch generation
responses = llm.generate_batch(["Q1", "Q2", "Q3"])
```

#### Supported Providers

| Provider | Config Name | Environment Variable |
|----------|-------------|---------------------|
| OpenAI | `openai` | `OPENAI_API_KEY` |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` |
| Azure OpenAI | `azure` | `AZURE_API_KEY`, `AZURE_API_BASE` |
| AWS Bedrock | `bedrock` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` |
| Google Vertex AI | `vertex_ai` | `GOOGLE_APPLICATION_CREDENTIALS` |
| Aliyun | `aliyun` | `DASHSCOPE_API_KEY` |

#### Response Normalization

LiteLLM adapters normalize provider-specific responses:
```python
# Provider responses differ, but adapter normalizes:
response = llm.generate(prompt)
# Always returns: str (cleaned text content)

# Rich response with metadata:
rich_response = llm.generate(prompt, return_rich=True)
# Returns: RichResponse(content=str, tokens=int, cost=float)
```

#### Retry Logic

Built-in retry with exponential backoff:
- **Default retries**: 4 attempts
- **Backoff**: Exponential with jitter
- **Errors handled**: Rate limits, timeouts, transient failures

**Important**: Attacks should NOT catch LLM exceptions - let them propagate for proper error handling.

### 5. Execution State Management

Thread-safe per-run state using context variables.

#### Attack Context

```python
from src.jbfoundry.attacks.context import AttackContext

# Automatic context wrapping via metaclass
class MyAttack(ModernBaseAttack):
    def generate_attack(self, prompt: str, **kwargs) -> str:
        # Access context (automatically isolated per request)
        ctx = AttackContext.get()

        # Track state within this execution
        ctx.set("intermediate_result", value)
        result = ctx.get("intermediate_result")

        return modified_prompt
```

**Benefits**:
- No shared state between concurrent requests
- Cleaner code (no manual state passing)
- Thread-safe by default

#### Defense Context

Similar isolation for defense mechanisms:
```python
from src.jbfoundry.defenses.context import DefenseContext

# Isolated per-defense execution
ctx = DefenseContext.get()
```

### 6. Configuration and Artifacts

Centralized experiment configuration and structured result storage.

#### JailbreakConfig

```python
from src.jbfoundry.config import JailbreakConfig

# Load from file
config = JailbreakConfig.from_file("config.json")

# Programmatic creation
config = JailbreakConfig(
    attack_name="pair_gen",
    model="gpt-4o",
    provider="openai",
    dataset="advbench",
    samples=10,
    temperature=0.7
)

# Access fields
print(config.attack_name, config.model)
```

#### Result Artifacts

Structured output for reproducibility:

**JailbreakInfo** (per-query):
```python
{
    "goal": "Write harmful content",
    "target": "Sure, here is",
    "attack_prompt": "Modified query...",
    "response": "Model output...",
    "success": true,
    "metadata": {
        "tokens": 150,
        "cost": 0.0005,
        "attempt_index": 1
    }
}
```

**Experiment Artifacts**:
```
results/
└── {attack_name}_{timestamp}/
    ├── config.json          # Full configuration
    ├── results.json         # Per-query traces
    ├── summary.json         # Aggregate metrics
    ├── cost_tracking.json   # Resource usage
    └── logs/
        └── execution.log    # Detailed logs
```

## Design Patterns

### 1. Separation of Concerns

**Attack Implementation**: Focus only on attack logic
```python
def generate_attack(self, prompt: str, **kwargs) -> str:
    # Only: transform prompt to bypass safety
    return modified_prompt
```

**Evaluation Logic**: Handled by harness
- Model querying
- Response judging
- Success scoring
- Result aggregation

**Boundary**: Attacks expose algorithmic controls (restarts, attempts) as parameters, but don't implement evaluation loops.

### 2. Fail-Fast Philosophy

Let errors propagate instead of masking:

```python
# ❌ BAD: Masks LLM failures
try:
    response = llm.generate(prompt)
except Exception:
    response = "fallback"

# ✅ GOOD: Let errors surface
response = llm.generate(prompt)
# Harness will catch, log, and mark as failed attempt
```

**Rationale**: Failed attacks shouldn't artificially inflate success rates.

### 3. Configuration-Driven Execution

All runtime behavior controlled via configuration:
- No hardcoded paths or values
- Environment variables for secrets
- CLI overrides for experimentation
- Config files for reproducibility

### 4. Minimal Coupling

Attacks depend only on:
- JBF-LIB base classes
- LLM adapters
- Standard library

**No dependencies on**:
- Other attacks
- Evaluation code
- Dataset loaders
- Result writers

## Performance Optimizations

### 1. Lazy Loading

Registry loads attacks only when needed:
- Fast CLI startup
- Low memory footprint
- Isolated errors

### 2. Caching

**Registry Cache**: Loaded classes cached for reuse
**LLM Cache**: Optional response caching for deterministic reuse
**Training Cache**: Attack-specific learned artifacts (if applicable)

### 3. Batch Operations

LLM adapters support batch generation:
```python
# Batch generation (single API call)
responses = llm.generate_batch([
    "Prompt 1",
    "Prompt 2",
    "Prompt 3"
])
```

### 4. Concurrent Execution

Thread-safe context enables parallel evaluation:
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(run_attack, query) for query in queries]
    results = [f.result() for f in futures]
```

## Testing and Validation

### Unit Tests

```bash
# Run JBF-LIB tests
pytest tests/test_base.py
pytest tests/test_registry.py
pytest tests/test_llm_adapters.py
```

### Integration Tests

```bash
# Test attack loading
pytest tests/test_attack_loading.py

# Test end-to-end execution
pytest tests/test_execution.py
```

### Contract Compliance

All attacks must pass contract tests:
```bash
# Validate attack implements required interface
pytest tests/test_attack_contract.py::test_attack_compliance[example_attack]
```

## Best Practices

### 1. Parameter Design

**Good**:
```python
"num_examples": AttackParameter(
    name="num_examples",
    param_type=int,
    default=20,
    description="Number of in-context examples",
    cli_arg="--num_examples"
)
```

**Bad**:
```python
"n": AttackParameter(  # Unclear name
    name="n",
    param_type=int,
    default=20,        # No description
    cli_arg="--n"
)
```

### 2. Error Handling

**Good**: Let errors propagate
```python
response = llm.generate(prompt)
```

**Bad**: Catch and mask
```python
try:
    response = llm.generate(prompt)
except:
    response = ""
```

### 3. Documentation

**Good**: Clear docstrings
```python
class WellDocumentedAttack(ModernBaseAttack):
    """
    Multi-language translation chain attack.

    Translates prompt through multiple languages to bypass
    content filters, then translates back to English.

    Reference: Author et al. (2024)
    """
```

**Bad**: Minimal context
```python
class Attack(ModernBaseAttack):
    """Translation attack."""
```

### 4. Testing

Always include test script for smoke testing:
```python
if __name__ == "__main__":
    attack = ExampleAttack()
    result = attack.generate_attack(
        prompt="Test prompt",
        goal="Test goal",
        target="Sure"
    )
    print(result)
```

## Troubleshooting

### Common Issues

1. **Attack not found in registry**
   - Check file location: `src/jbfoundry/attacks/manual/` or `generated/`
   - Verify NAME attribute matches usage
   - Check for import errors in attack file

2. **Parameter not recognized**
   - Ensure `cli_arg` matches command line usage
   - Check parameter name spelling
   - Verify parameter in PARAMETERS dict

3. **LLM adapter errors**
   - Verify API keys in environment
   - Check provider name spelling
   - Ensure model name is valid for provider

4. **Context isolation issues**
   - Don't store state in class attributes
   - Use AttackContext for per-run state
   - Avoid global variables

## References

- **Paper**: [arXiv:2602.24009](https://arxiv.org/pdf/2602.24009) - Section 3.1 (JBF-LIB) and Appendix E
- **Source Code**:
  - Attack contracts: `src/jbfoundry/attacks/base.py`
  - Registry system: `src/jbfoundry/attacks/registry.py`
  - LLM adapters: `src/jbfoundry/llm/`
- **Documentation**: [ATTACK_CONFIG.md](ATTACK_CONFIG.md), [CLI_REFERENCE.md](CLI_REFERENCE.md)

---

**Status**: Stable API

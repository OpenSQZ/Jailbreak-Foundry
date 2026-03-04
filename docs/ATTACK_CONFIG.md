# Attack Configuration Guide

Guide to attack configuration using the JBF-LIB parameter system.

## Configuration System

Attacks use embedded configuration with `AttackParameter` objects:
- Self-documenting parameters
- Automatic CLI generation
- Type validation

## Attack Structure

```python
from ..base import ModernBaseAttack, AttackParameter

class ExampleAttack(ModernBaseAttack):
    """Attack description."""

    NAME = "example_gen"
    PAPER = "Author et al. - Paper Title (Year)"

    PARAMETERS = {
        "param_name": AttackParameter(
            name="param_name",
            param_type=int,
            default=5,
            description="Parameter description",
            cli_arg="--param_name"
        )
    }

    def generate_attack(self, prompt: str, goal: str,
                       target: str, **kwargs) -> str:
        param_value = self.get_parameter_value("param_name")
        return modified_prompt
```

## Essential Attributes

- **NAME**: Unique identifier (ends with `_gen` for generated attacks)
- **PAPER**: Paper reference
- **PARAMETERS**: Parameter definitions

## AttackParameter

```python
AttackParameter(
    name="param",              # Internal name
    param_type=int,            # Type: str, int, bool, float
    default=5,                 # Default value
    description="Description", # Help text
    cli_arg="--param"         # CLI argument
)
```

## Parameter Access

```python
def generate_attack(self, prompt: str, goal: str,
                   target: str, **kwargs) -> str:
    # Access parameter (CLI > kwargs > default)
    param_value = self.get_parameter_value("param_name")

    # Access attempt metadata (multi-attempt protocol)
    attempt_idx = kwargs.get("attempt_index", 1)
    attempts = kwargs.get("attempts_per_query", 1)

    return modified_prompt
```

## CLI Integration

Parameters automatically become CLI arguments:

```bash
python src/jbfoundry/runners/universal_attack.py \
    --attack_name pair_gen \
    --max_rounds 3 \
    --improvement_threshold 0.05
```

## Real Example: PAIR Attack

From `src/jbfoundry/attacks/generated/pair_gen.py`:

```python
class PAIRAttack(ModernBaseAttack):
    """Prompt Automatic Iterative Refinement."""

    NAME = "pair_gen"
    PAPER = "Chao et al. - PAIR (2024)"

    PARAMETERS = {
        "max_rounds": AttackParameter(
            name="max_rounds",
            param_type=int,
            default=5,
            description="Maximum refinement rounds",
            cli_arg="--max_rounds"
        ),
        "improvement_threshold": AttackParameter(
            name="improvement_threshold",
            param_type=float,
            default=0.1,
            description="Minimum improvement to continue",
            cli_arg="--improvement_threshold"
        )
    }

    def generate_attack(self, prompt: str, goal: str,
                       target: str, **kwargs) -> str:
        max_rounds = self.get_parameter_value("max_rounds")
        threshold = self.get_parameter_value("improvement_threshold")
        # Implement iterative refinement
        return refined_prompt
```

Usage:
```bash
python src/jbfoundry/runners/universal_attack.py \
    --attack_name pair_gen \
    --max_rounds 10 \
    --improvement_threshold 0.05
```

## Adding Custom Attacks

1. Create file in `src/jbfoundry/attacks/manual/`
2. Inherit from `ModernBaseAttack`
3. Define NAME, PAPER, PARAMETERS
4. Implement `generate_attack()` method
5. Attack auto-discovered by registry

Example:

```python
from ..base import ModernBaseAttack, AttackParameter

class MyCustomAttack(ModernBaseAttack):
    """My custom jailbreak technique."""

    NAME = "my_custom_attack"
    PAPER = "Smith et al. - Custom Attack (2024)"

    PARAMETERS = {
        "strength": AttackParameter(
            name="strength",
            param_type=int,
            default=5,
            description="Attack strength level",
            cli_arg="--strength"
        )
    }

    def generate_attack(self, prompt: str, goal: str,
                       target: str, **kwargs) -> str:
        strength = self.get_parameter_value("strength")
        return f"[Attack with strength {strength}] {prompt}"
```

## Validation

- **Type checking**: Automatic based on `param_type`
- **Choices**: Restrict to specific values
- **Custom validators**: Via `validator` function

```python
def validate_positive(value):
    return isinstance(value, int) and value > 0

"rounds": AttackParameter(
    name="rounds",
    param_type=int,
    default=5,
    validator=validate_positive
)
```

## Best Practices

1. **Clear names**: Descriptive parameter names
2. **Sensible defaults**: Working defaults from paper
3. **Documentation**: Clear descriptions
4. **Pure functions**: No side effects (input → output)
5. **Error propagation**: No try/except around LLM calls

---

**See also**:
- [CLI_REFERENCE.md](CLI_REFERENCE.md) for command-line usage
- [ARCHITECTURE.md](ARCHITECTURE.md) for framework details
- [arXiv:2602.24009](https://arxiv.org/pdf/2602.24009) for parameter design patterns

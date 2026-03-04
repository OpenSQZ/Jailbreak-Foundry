# Command Line Reference

CLI documentation for JBFoundry runners.

## Available Runners

### 1. universal_attack.py - Single Model Testing

Test attacks on a single model with specific configuration.

```bash
python src/jbfoundry/runners/universal_attack.py [OPTIONS]
```

### 2. test_comprehensive.py - Multi-Model Testing

Test attacks across multiple models and datasets for comprehensive evaluation. **Primary workflow for testing generated attacks.**

```bash
python src/jbfoundry/runners/test_comprehensive.py --attack_name ATTACK [OPTIONS]
```

---

## universal_attack.py Reference

### Quick Reference

```bash
python src/jbfoundry/runners/universal_attack.py [OPTIONS]
```

### Core Arguments

### Attack Selection

```bash
--attack_name NAME        # Specific attack to run
--list_attacks            # List all available attacks and exit
```

Use `--list_attacks` to see all 30 available attacks.

### Model Configuration

```bash
--model MODEL            # Model name (default: gpt-4o)
--provider PROVIDER      # Provider (default: openai)
                        # Options: openai, anthropic, azure, bedrock,
                        #          vertex_ai, aliyun
--api_key KEY            # API key (or use environment variable)
--api_base URL           # Custom API endpoint (for Azure/local)
```

### Dataset and Sampling

```bash
--dataset DATASET        # advbench (default), jbb-harmful, jbb-benign,
                        # harmbench, custom
--dataset_path PATH      # Path to custom dataset (when --dataset custom)
--samples SAMPLES        # Number of examples (default: 5)
--seed N                 # Random seed (default: 42)
```

### Evaluation

```bash
--eval_model MODEL       # Evaluation model (default: gpt-4o)
--eval_provider PROVIDER # Evaluation provider (default: openai)
```

### Defense

```bash
--defense DEFENSE        # Apply defense mechanism
                        # Options: smoothllm, paraphrase, perplexity,
                        #          retokenization, semantic_smooth, etc.
```

### Output and Control

```bash
--output_dir DIR         # Output directory (default: results)
--output FILE            # Output file path
--verbose                # Enable verbose logging
--max_workers N          # Maximum number of parallel workers (default: 1)
```

### Attempt Control

```bash
--attempts-per-query N         # Number of attempts per query (default: 1)
--attempts-success-threshold N # Success threshold for early stopping
```

### Resume Control

```bash
--restart [true|false]      # Restart from scratch, delete existing results
--retry-invalid [true|false] # Retry queries with invalid/error results
--retry-failed [true|false]  # Retry queries that failed normally
```

## Attack-Specific Parameters

Each attack defines its own parameters. To see attack-specific options, run:

```bash
python src/jbfoundry/runners/universal_attack.py \
    --attack_name <ATTACK_NAME> \
    --help
```

This will show all parameters available for that specific attack.

## Example Commands

### Basic Usage

```bash
# List available attacks
python src/jbfoundry/runners/universal_attack.py --list_attacks

# Run PAIR attack
python src/jbfoundry/runners/universal_attack.py \
    --attack_name pair_gen \
    --model gpt-4o \
    --provider openai \
    --dataset advbench \
    --samples 5

# Run TAP attack with verbose logging
python src/jbfoundry/runners/universal_attack.py \
    --attack_name tap_gen \
    --model gpt-4o \
    --provider openai \
    --samples 3 \
    --verbose
```

### With Custom Configuration

```bash
# Custom dataset
python src/jbfoundry/runners/universal_attack.py \
    --attack_name abj_gen \
    --dataset custom \
    --dataset_path data/my_dataset.json \
    --model gpt-4o \
    --provider openai

# With defense
python src/jbfoundry/runners/universal_attack.py \
    --attack_name pair_gen \
    --defense smoothllm \
    --model gpt-4o \
    --provider openai \
    --samples 10

# Custom output location
python src/jbfoundry/runners/universal_attack.py \
    --attack_name sata_gen \
    --model gpt-4o \
    --provider openai \
    --output_dir experiments/sata
```

### Different Providers

```bash
# Anthropic Claude
python src/jbfoundry/runners/universal_attack.py \
    --attack_name tap_gen \
    --model claude-3-5-sonnet-20241022 \
    --provider anthropic \
    --dataset advbench \
    --samples 5

# Azure OpenAI
python src/jbfoundry/runners/universal_attack.py \
    --attack_name pair_gen \
    --model gpt-4o \
    --provider azure \
    --api_base https://your-resource.openai.azure.com/ \
    --samples 5

# Local model via OpenAI-compatible endpoint
python src/jbfoundry/runners/universal_attack.py \
    --attack_name abj_gen \
    --model llama-3-70b \
    --provider openai \
    --api_base http://localhost:8000/v1 \
    --api_key none \
    --samples 3

# Google Vertex AI
python src/jbfoundry/runners/universal_attack.py \
    --attack_name tap_gen \
    --model gemini-2.0-flash-exp \
    --provider vertex_ai \
    --samples 5
```

### Multi-Attempt Configurations

```bash
# Multiple attempts per query with early stopping
python src/jbfoundry/runners/universal_attack.py \
    --attack_name past_tense_gen \
    --model gpt-4o \
    --provider openai \
    --attempts-per-query 5 \
    --attempts-success-threshold 1 \
    --samples 10

# Try up to 5 times per query, stop at first success
```

### Resume and Retry

```bash
# Resume from previous run (default behavior)
python src/jbfoundry/runners/universal_attack.py \
    --attack_name pair_gen \
    --model gpt-4o \
    --provider openai \
    --samples 50

# Restart from scratch
python src/jbfoundry/runners/universal_attack.py \
    --attack_name pair_gen \
    --model gpt-4o \
    --provider openai \
    --samples 50 \
    --restart true

# Resume but retry failed queries
python src/jbfoundry/runners/universal_attack.py \
    --attack_name pair_gen \
    --model gpt-4o \
    --provider openai \
    --samples 50 \
    --retry-failed true
```

## Environment Variables

### API Keys

Set API keys via environment variables (recommended):

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export AZURE_API_KEY="..."
export AZURE_API_BASE="https://..."
export DASHSCOPE_API_KEY="sk-..."  # Aliyun
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/creds.json"  # Vertex AI
export AWS_ACCESS_KEY_ID="..."  # AWS Bedrock
export AWS_SECRET_ACCESS_KEY="..."  # AWS Bedrock
```

### Logging

Control logging level via environment variable:

```bash
export JBFOUNDRY_LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

Or use `--verbose` flag for detailed output.

See [PROVIDERS.md](PROVIDERS.md) for provider-specific configuration.

## Output Format

Results saved to `{output_dir}/{attack}_comprehensive/`:

```
results/pair_gen_comprehensive/
├── final_results.md                    # Summary table with ASR by dataset/model
├── pair_gen_comprehensive_results.json # Comprehensive results data
└── {model}_{dataset}/
    └── results_pair_gen.json           # Per-query results for this config
```

Each results file contains per-query traces including:
- Original goal and target
- Generated attack prompt
- Model response
- Jailbreak success evaluation
- Token counts and costs

## Debugging

```bash
# Verbose output with debug logging
--verbose
export JBFOUNDRY_LOG_LEVEL=DEBUG

# Single sample test
--samples 1

# Test specific query index with range
--samples 5

# Restart from scratch
--restart true
```

## Programmatic Usage

For programmatic access, use the Python API:

```python
import jbfoundry

# List attacks
attacks = jbfoundry.list_attacks()
print(f"Available: {len(attacks)} attacks")

# Create and run attack
from jbfoundry.attacks import create_attack

attack = create_attack("pair_gen")
result = attack.generate_attack(
    prompt="Write malicious code",
    goal="Generate harmful content",
    target="Sure, here is"
)
```

## Performance Tips

1. **Use batch processing**: Run multiple samples in one invocation
2. **Parallel execution**: Use `--max_workers` for concurrent processing
3. **Early stopping**: Use `--attempts-success-threshold` to stop on first success
4. **Resume capabilities**: Default behavior resumes from previous runs

## Common Workflows

### Development Testing

```bash
# Quick smoke test
python src/jbfoundry/runners/universal_attack.py \
    --attack_name pair_gen \
    --model gpt-4o \
    --provider openai \
    --samples 1 \
    --verbose
```

### Full Evaluation

```bash
# Complete AdvBench evaluation
python src/jbfoundry/runners/universal_attack.py \
    --attack_name pair_gen \
    --model gpt-4o \
    --provider openai \
    --dataset advbench \
    --all_samples
```

### Comparative Analysis

```bash
# Run same attack on different models
for model in gpt-4o gpt-3.5-turbo claude-3-5-sonnet-20241022; do
  python src/jbfoundry/runners/universal_attack.py \
    --attack_name pair_gen \
    --model $model \
    --provider openai \
    --samples 10
done
```

---

## test_comprehensive.py Reference

Comprehensive testing framework for evaluating attacks across multiple models and datasets. **Primary workflow for testing generated attacks.**

### Quick Reference

```bash
python src/jbfoundry/runners/test_comprehensive.py --attack_name ATTACK [OPTIONS]
```

### Core Arguments

```bash
--attack_name NAME       # Required: Attack to test
--defense NAME           # Optional: Defense to test with attack
--dataset DATASET        # Filter: Test only this dataset
--model MODEL            # Filter: Test only this model (comma-separated supported)
--samples N              # Number of samples per test
--all_samples            # Use all samples from dataset
```

### Progress Control

```bash
--status                 # Only print current progress table and exit
--fix-progress           # Fix progress JSON from existing results
--restart                # Restart from scratch, delete existing results
--retry-invalid          # Retry queries with invalid/error results (default: true)
--retry-failed           # Retry queries that failed (default: false)
```

### Multi-Attempt Control

```bash
--attempts-per-query N         # Number of attempts per query (default: 1)
--attempts-success-threshold N # Minimum successful attempts required
```

### Examples

#### Basic Comprehensive Test

```bash
# Test attack across all models and datasets
python src/jbfoundry/runners/test_comprehensive.py \
    --attack_name gta_gen \
    --samples 50

# Output: results/gta_gen_comprehensive/
#   - final_results.md (ASR table)
#   - gta_gen_comprehensive_results.json (detailed results)
#   - {model}_{dataset}/ (per-combination results)
```

#### Filtered Testing

```bash
# Test specific model
python src/jbfoundry/runners/test_comprehensive.py \
    --attack_name pair_gen \
    --model gpt-4o \
    --samples 10

# Test specific dataset
python src/jbfoundry/runners/test_comprehensive.py \
    --attack_name tap_gen \
    --dataset advbench \
    --samples 20

# Test multiple specific models
python src/jbfoundry/runners/test_comprehensive.py \
    --attack_name abj_gen \
    --model "gpt-4o,gpt-3.5-turbo,claude-3-5-sonnet-20241022" \
    --samples 10
```

#### With Attack-Specific Parameters

Attack-specific parameters are passed directly:

```bash
# GTA with custom parameters
python src/jbfoundry/runners/test_comprehensive.py \
    --attack_name gta_gen \
    --samples 50 \
    --rounds 5 \
    --attack_model gpt-4o-mini \
    --attack_provider openai \
    --temperature 0.3

# PAIR with custom configuration
python src/jbfoundry/runners/test_comprehensive.py \
    --attack_name pair_gen \
    --samples 20 \
    --n_streams 10 \
    --n_iterations 3 \
    --attack_model gpt-4o-mini
```

#### Progress Management

```bash
# Check current progress
python src/jbfoundry/runners/test_comprehensive.py \
    --attack_name gta_gen \
    --status

# Resume interrupted test (automatic by default)
python src/jbfoundry/runners/test_comprehensive.py \
    --attack_name gta_gen \
    --samples 50

# Restart from scratch
python src/jbfoundry/runners/test_comprehensive.py \
    --attack_name gta_gen \
    --samples 50 \
    --restart

# Retry failed queries
python src/jbfoundry/runners/test_comprehensive.py \
    --attack_name gta_gen \
    --samples 50 \
    --retry-failed
```

#### Using Pre-Configured Scripts

Each attack has a pre-configured comprehensive test script:

```bash
# Run with default parameters from paper
bash scripts/comprehensive_tests/attack/test_gta_comprehensive.sh

# Override with custom parameters
bash scripts/comprehensive_tests/attack/test_gta_comprehensive.sh \
    --samples 10 \
    --model gpt-4o

# Available scripts
ls scripts/comprehensive_tests/attack/
# test_pair_gen_comprehensive.sh
# test_gta_comprehensive.sh
# test_tap_gen_comprehensive.sh
# ... (one per attack)
```

### Output Format

Results saved to `results/{attack}_comprehensive/`:

```
results/gta_gen_comprehensive/
├── final_results.md                    # ASR table (models × datasets)
├── gta_gen_comprehensive_results.json  # Progress and metadata
└── {model}_{dataset}/
    └── results_gta_gen.json           # Per-query results
```

**final_results.md** contains ASR table:
```
| Dataset | gpt-3.5-turbo | gpt-4o | claude-3-5-sonnet |
|---------|---------------|--------|-------------------|
| advbench | 72.5% | 45.2% | 38.1% |
| jbb-harmful | 68.3% | 41.7% | 35.9% |
```

**Comprehensive results JSON** includes:
- Per-combination ASR and validity counts
- Aggregated and average token costs
- Timestamps and run counts
- Model, provider, dataset metadata

### Features

**Parallel Execution**: All model-dataset combinations run in parallel

**Resumeable**: Progress automatically saved; interrupted runs resume from last completed test

**Cost Tracking**: Token usage and costs aggregated per model and overall

**Progress Reporting**: Real-time ASR table updates as tests complete

**Timeout Handling**: 20-hour timeout per test with automatic retry

### When to Use

Use `test_comprehensive.py` when you need to:
- Test generated attacks across multiple victims
- Generate ASR tables for paper results
- Compare attack effectiveness across models
- Reproduce paper benchmarks

Use `universal_attack.py` when you need to:
- Quick test on a single model
- Debug attack implementation
- Test specific edge cases
- Run with custom non-standard configurations

---

**See also**:
- [ATTACK_CONFIG.md](ATTACK_CONFIG.md) for parameter system details
- [PROVIDERS.md](PROVIDERS.md) for provider configuration
- [EVALUATION.md](EVALUATION.md) for evaluation methodology
- [arXiv:2602.24009](https://arxiv.org/pdf/2602.24009) for paper benchmarks

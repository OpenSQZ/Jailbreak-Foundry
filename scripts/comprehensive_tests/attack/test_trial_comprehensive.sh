#!/bin/bash

# Configuration
ATTACK_NAME="trial_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# TRIAL-specific parameters (from paper)
# Note: Using gpt-4o as fallback since glm-4-plus may not be available
ATTACK_MODEL="gpt-4o"
ATTACK_PROVIDER="openai"
HELPER_MODEL="gpt-4o"  # Defaults to gpt-4o per plan (§3.1)
HELPER_PROVIDER="openai"  # Defaults to attack_provider if not set
JUDGE_MODEL="gpt-4o"  # Using gpt-4o instead of llama-3-70b-instruct for availability
JUDGE_PROVIDER="openai"
N_ITERATIONS="5"  # 5 follow-up queries after setup (total: 1 setup + 5 queries)
ATTACK_TEMPERATURE="1.0"
JUDGE_TEMPERATURE="0.0"

# Multi-attempt support (paper uses single attempt)
ATTEMPTS_PER_QUERY="1"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "🔍 TRIAL Attack Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Attack Model: $ATTACK_MODEL"
echo "Judge Model: $JUDGE_MODEL"
echo "Max Iterations: $N_ITERATIONS"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
    --attack_model "$ATTACK_MODEL"
    --attack_provider "$ATTACK_PROVIDER"
    --judge_model "$JUDGE_MODEL"
    --judge_provider "$JUDGE_PROVIDER"
    --n_iterations "$N_ITERATIONS"
    --attack_temperature "$ATTACK_TEMPERATURE"
    --judge_temperature "$JUDGE_TEMPERATURE"
)

# Add helper model params if specified
[ -n "$HELPER_MODEL" ] && ARGS+=(--helper_model "$HELPER_MODEL")
[ -n "$HELPER_PROVIDER" ] && ARGS+=(--helper_provider "$HELPER_PROVIDER")

# Add samples arg if not overridden
[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

# Add dataset and model filters
[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

# Add any additional arguments passed to script
ARGS+=("$@")

# Execute test
exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

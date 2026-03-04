#!/bin/bash

# Configuration
ATTACK_NAME="renellm_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# ReNeLLM-specific parameters (from paper)
MAX_ITERATIONS="20"
REWRITE_MODEL="gpt-3.5-turbo"
REWRITE_PROVIDER="openai"
JUDGE_MODEL="gpt-3.5-turbo"
JUDGE_PROVIDER="openai"
REWRITE_TEMPERATURE="0.5"

echo "🔍 ReNeLLM Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Max Iterations: $MAX_ITERATIONS"
echo "Rewrite Model: $REWRITE_MODEL"
echo "Judge Model: $JUDGE_MODEL"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --max_iterations "$MAX_ITERATIONS"
    --rewrite_model "$REWRITE_MODEL"
    --rewrite_provider "$REWRITE_PROVIDER"
    --judge_model "$JUDGE_MODEL"
    --judge_provider "$JUDGE_PROVIDER"
    --rewrite_temperature "$REWRITE_TEMPERATURE"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

#!/bin/bash

# Configuration
ATTACK_NAME="majic_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# MAJIC-specific parameters (from paper)
MAX_QUERIES="20"  # Paper uses 15-40, we default to 20 for testing
LEARNING_RATE="0.1"
DISCOUNT_FACTOR="0.9"
DECAY_FACTOR="0.99"
RESET_FACTOR="0.1"
TEMPERATURE="1.0"
ATTACKER_MODEL="gpt-4o-mini"  # Using gpt-4o-mini for testing (plan default is mistral-7b but not available on openai)
ATTACKER_PROVIDER="openai"
TARGET_MODEL="gpt-4o-mini"
TARGET_PROVIDER="openai"
EVALUATOR_MODEL="gpt-4o-mini"
EVALUATOR_PROVIDER="openai"

# Multi-attempt parameters
ATTEMPTS_PER_QUERY="3"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "🔍 MAJIC Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Max Queries: $MAX_QUERIES"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
    --max_queries "$MAX_QUERIES"
    --learning_rate "$LEARNING_RATE"
    --discount_factor "$DISCOUNT_FACTOR"
    --decay_factor "$DECAY_FACTOR"
    --reset_factor "$RESET_FACTOR"
    --temperature "$TEMPERATURE"
    --attacker_model "$ATTACKER_MODEL"
    --attacker_provider "$ATTACKER_PROVIDER"
    --target_model "$TARGET_MODEL"
    --target_provider "$TARGET_PROVIDER"
    --evaluator_model "$EVALUATOR_MODEL"
    --evaluator_provider "$EVALUATOR_PROVIDER"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

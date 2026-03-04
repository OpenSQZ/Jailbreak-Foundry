#!/bin/bash

# Configuration
ATTACK_NAME="response_attack_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# Attack-specific parameters
ATTACK_TYPE="sri"  # Options: dri, sri
AUXILIARY_MODEL="gpt-4o"
AUXILIARY_PROVIDER="openai"
ATTEMPTS_PER_QUERY="1"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "🔍 Response Attack Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Attack Type: $ATTACK_TYPE"
echo "Auxiliary Model: $AUXILIARY_PROVIDER/$AUXILIARY_MODEL"
echo "Samples: $SAMPLES_ARG"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attack_type "$ATTACK_TYPE"
    --auxiliary_model "$AUXILIARY_MODEL"
    --auxiliary_provider "$AUXILIARY_PROVIDER"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

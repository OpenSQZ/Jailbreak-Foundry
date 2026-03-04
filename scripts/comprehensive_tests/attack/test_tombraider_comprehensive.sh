#!/bin/bash

# Configuration
ATTACK_NAME="tombraider_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-4o"

# TOMBRAIDER-specific parameters (from paper)
INSPECTOR_MODEL="gpt-4o"
ATTACKER_MODEL="gpt-4o"
MAX_ROUNDS="5"
ATTEMPTS_PER_QUERY="1"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "🔍 TOMBRAIDER Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Inspector Model: $INSPECTOR_MODEL"
echo "Attacker Model: $ATTACKER_MODEL"
echo "Max Rounds: $MAX_ROUNDS"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
    --inspector_model "$INSPECTOR_MODEL"
    --attacker_model "$ATTACKER_MODEL"
    --max_rounds "$MAX_ROUNDS"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

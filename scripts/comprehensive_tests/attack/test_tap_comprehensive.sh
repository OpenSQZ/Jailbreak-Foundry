#!/bin/bash

# Configuration
ATTACK_NAME="tap_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER=""

# TAP-specific parameters (from paper defaults)
WIDTH="10"
BRANCHING_FACTOR="4"
DEPTH="10"
KEEP_LAST_N="3"
ATTACKER_MODEL="gpt-4o"
EVALUATOR_MODEL="gpt-3.5-turbo"

# Target model parameters (should match --model and --provider from test harness)
# TAP needs to query the target during attack generation
TARGET_MODEL="$MODEL_FILTER"
TARGET_PROVIDER="openai"

# Multi-attempt support (default 1/1 for TAP)
ATTEMPTS_PER_QUERY="1"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "🔍 Tree of Attacks with Pruning (TAP) Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "TAP Parameters: width=$WIDTH, branching_factor=$BRANCHING_FACTOR, depth=$DEPTH, keep_last_n=$KEEP_LAST_N"
echo "Attacker Model: $ATTACKER_MODEL"
echo "Evaluator Model: $EVALUATOR_MODEL"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
    --width "$WIDTH"
    --branching_factor "$BRANCHING_FACTOR"
    --depth "$DEPTH"
    --keep_last_n "$KEEP_LAST_N"
    --attacker_model "$ATTACKER_MODEL"
    --evaluator_model "$EVALUATOR_MODEL"
    --target_model "$TARGET_MODEL"
    --target_provider "$TARGET_PROVIDER"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

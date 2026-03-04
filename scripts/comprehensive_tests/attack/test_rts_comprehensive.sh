#!/bin/bash

# Configuration
ATTACK_NAME="rts_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# Attack-specific parameters aligned with paper and framework
# Using qwen3-14b as closest available substitute for paper's Qwen2.5
ATTACK_MODEL="qwen3-14b"
NUM_REWRITES="5"  # Paper recommends multiple rewrites for diversity
ATTEMPTS_PER_QUERY="5"  # Match num_rewrites for multi-attempt testing
ATTEMPTS_SUCCESS_THRESHOLD="1"  # Success if any attempt works

echo "🔍 RTS-Attack Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attack_model "$ATTACK_MODEL"
    --attack_provider "$ATTACK_PROVIDER"
    --num_rewrites "$NUM_REWRITES"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py --restart "${ARGS[@]}"

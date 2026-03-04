#!/bin/bash

# Configuration
ATTACK_NAME="air_gen"
SAMPLES="2"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o-mini"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# Attack-specific parameters (from paper and reference code)
ATTACK_METHOD="k4"  # Default: k4 (3 benign paragraphs + 1 malicious)
REWRITE_MODEL="gpt-4o-mini"
REWRITE_PROVIDER="openai"
USE_TARGET_FOR_REWRITE="false"
TARGET_MAX_TOKENS="300"
CLEAN_CONVERSATION="false"

# Multi-attempt support (paper uses n_restarts=20 for full evaluation)
ATTEMPTS_PER_QUERY="3"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "🔍 Attack via Implicit Reference (AIR) Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Attack Method: $ATTACK_METHOD"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
    --attack_method "$ATTACK_METHOD"
    --rewrite_model "$REWRITE_MODEL"
    --rewrite_provider "$REWRITE_PROVIDER"
    --target_max_tokens "$TARGET_MAX_TOKENS"
)

# Add boolean flags if enabled
[[ "$USE_TARGET_FOR_REWRITE" == "true" ]] && ARGS+=(--use_target_for_rewrite)
[[ "$CLEAN_CONVERSATION" == "true" ]] && ARGS+=(--clean_conversation)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py --restart "${ARGS[@]}"

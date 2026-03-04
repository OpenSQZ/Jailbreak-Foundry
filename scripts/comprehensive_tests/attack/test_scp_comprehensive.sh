#!/bin/bash

# Configuration
ATTACK_NAME="scp_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# Attack-specific parameters (from paper/plan)
# Note: Using openai provider instead of openai for environment compatibility
ATTACKER_MODEL="gpt-3.5-turbo"
ATTACKER_PROVIDER="openai"
BENIGN_RETRIES="3"
# BENIGN_CANDIDATES="3"  # Number of benign candidates to generate and select best from (refinement #1)

# Multi-attempt support (paper tests with single attempt by default)
ATTEMPTS_PER_QUERY="3"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "🔍 Sugar-Coated Poison (SCP) Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Attacker Model: $ATTACKER_PROVIDER/$ATTACKER_MODEL"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
    --attacker-model "$ATTACKER_MODEL"
    --attacker-provider "$ATTACKER_PROVIDER"
    --benign-retries "$BENIGN_RETRIES"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py  "${ARGS[@]}"

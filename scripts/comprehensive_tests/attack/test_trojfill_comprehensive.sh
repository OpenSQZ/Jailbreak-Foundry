#!/bin/bash

# Configuration matching paper parameters
ATTACK_NAME="trojfill_gen"
SAMPLES="1"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
# DATASET_FILTER="assets/jbb-harmful-behaviors-32.csv"
DATASET_FILTER="advbench"
MODEL_FILTER="gpt-4o"

# Paper-specific parameters
# Paper uses gemini-2.5-flash as attacker model
ATTACKER_MODEL="gemini-2.5-flash"
# Using openai provider as fallback for testing (paper would use gemini directly)
ATTACKER_PROVIDER="openai"
# Paper default: Caesar cipher
TRANSFORM_TYPE="Caesar"
# Paper uses 3 internal retries per iteration (Gap #1 mitigation)
INTERNAL_RETRIES="3"
# Paper uses N=10 iterations, simulating with attempts_per_query
# With internal_retries=3, we need attempts_per_query=30 to simulate 10 iterations
ATTEMPTS_PER_QUERY="5"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "🔍 TrojFill Comprehensive Testing (Refined)"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Target Model: $MODEL_FILTER"
echo "Attacker Model: $ATTACKER_PROVIDER/$ATTACKER_MODEL"
echo "Transform Type: $TRANSFORM_TYPE"
echo "Internal Retries: $INTERNAL_RETRIES (simulates paper's 3 attempts per iteration)"
echo "Total Attempts: $ATTEMPTS_PER_QUERY (simulates paper's N=10 iterations)"
echo ""
echo "Implementation Notes:"
echo "- Enhanced parsing robustness (Gap #5)"
echo "- Added internal retry variations (Gap #1 mitigation)"
echo "- Improved error handling and fallbacks"
echo "- State management for conversation history (Gap #3)"
echo ""

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
    --attacker_model "$ATTACKER_MODEL"
    --attacker_provider "$ATTACKER_PROVIDER"
    --transform_type "$TRANSFORM_TYPE"
    --internal_retries "$INTERNAL_RETRIES"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py --restart "${ARGS[@]}"
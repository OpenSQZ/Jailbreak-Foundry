#!/bin/bash

# Configuration
ATTACK_NAME="intent_laundering_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/benchmark-advbench-50.csv"
MODEL_FILTER="gpt-4o"

# Intent Laundering uses a revision-regeneration loop.
# attempts_per_query controls how many revision attempts are made per query.
# The launderer model generates increasingly refined revisions using previous failures as feedback.
LAUNDERER_MODEL="gpt-4o"
LAUNDERER_PROVIDER="openai"
ATTEMPTS_PER_QUERY="5"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "Intent Laundering Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
    --launderer-model "$LAUNDERER_MODEL"
    --launderer-provider "$LAUNDERER_PROVIDER"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python -m jbfoundry.runners.test_comprehensive --retry-failed "${ARGS[@]}"

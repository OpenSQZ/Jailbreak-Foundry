#!/bin/bash

# Configuration
ATTACK_NAME="wordgame_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# Attack-specific parameters (from paper)
ATTACKER_MODEL="gpt-3.5-turbo"
ATTACKER_PROVIDER="openai"
USE_WORDGAME_PLUS="false"  # Will be passed as boolean flag
NUM_HINTS="5"
ATTEMPTS_PER_QUERY="3"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "🔍 WordGame Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Attacker Model: $ATTACKER_MODEL"
echo "Attacker Provider: $ATTACKER_PROVIDER"
echo "WordGame+ Mode: $USE_WORDGAME_PLUS"
echo "Number of Hints: $NUM_HINTS"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
    --attacker-model "$ATTACKER_MODEL"
    --attacker-provider "$ATTACKER_PROVIDER"
    --num-hints "$NUM_HINTS"
    --use-wordgame-plus "$USE_WORDGAME_PLUS"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

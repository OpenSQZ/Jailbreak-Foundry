#!/bin/bash

# Configuration
ATTACK_NAME="past_tense_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# Attack-specific parameters from the paper
# The paper uses GPT-3.5 Turbo for reformulation with specific parameters
REFORMULATION_MODEL="gpt-3.5-turbo"
REFORMULATION_PROVIDER="openai"
REFORMULATION_TEMPERATURE="1.0"
REFORMULATION_MAX_TOKENS="150"
# n_restarts: Number of reformulation attempts (default: 20 in paper)
# Note: Currently generates one reformulation per call; framework should handle retries
N_RESTARTS="20"
ATTEMPTS_PER_QUERY="1"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "🔍 Past Tense Attack Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Reformulation Model: $REFORMULATION_MODEL"
echo "n_restarts: $N_RESTARTS (documented for future framework integration)"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --reformulation_model "$REFORMULATION_MODEL"
    --reformulation_provider "$REFORMULATION_PROVIDER"
    --reformulation_temperature "$REFORMULATION_TEMPERATURE"
    --reformulation_max_tokens "$REFORMULATION_MAX_TOKENS"
    --n_restarts "$N_RESTARTS"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

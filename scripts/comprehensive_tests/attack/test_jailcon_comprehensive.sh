#!/bin/bash

# Configuration
ATTACK_NAME="jailcon_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# JAIL-CON specific parameters
MODE="cvt"  # Options: cvt, cit, random
SEPARATOR="{}"  # Options: {}, <>, [], $$, ##, etc.
SEED="42"  # Random seed for auxiliary task selection
AUX_DATASET="jbb-benign"  # Auxiliary dataset for benign tasks
ATTEMPTS_PER_QUERY="3"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "🔍 JAIL-CON Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Mode: $MODE"
echo "Separator: $SEPARATOR"
echo "Seed: $SEED"
echo "Aux Dataset: $AUX_DATASET"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
    --mode "$MODE"
    --separator "$SEPARATOR"
    --jailcon-seed "$SEED"
    --aux_dataset "$AUX_DATASET"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

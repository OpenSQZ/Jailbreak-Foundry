#!/bin/bash

# Configuration
ATTACK_NAME="queryattack_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# QueryAttack-specific parameters
QUERY_LANGUAGE="SQL"  # Default to SQL as in paper
EXTRACTION_MODEL="gpt-4-1106-preview"  # As specified in paper
TEMPERATURE="0.0"  # For reproducibility as in paper

echo "🔍 QueryAttack Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Query Language: $QUERY_LANGUAGE"
echo "Extraction Model: $EXTRACTION_MODEL"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --query_language "$QUERY_LANGUAGE"
    --extraction_model "$EXTRACTION_MODEL"
    --temperature "$TEMPERATURE"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

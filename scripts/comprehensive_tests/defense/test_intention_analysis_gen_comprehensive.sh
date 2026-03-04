#!/bin/bash

# Configuration
DEFENSE_NAME="intention_analysis_gen"
ATTACK_NAME="deep_inception_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

echo "🔍 Intention Analysis Comprehensive Testing"
echo "Defense: $DEFENSE_NAME"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"

ARGS=(
  "--attack_name" "$ATTACK_NAME"
  "--defense" "$DEFENSE_NAME"
  "--eval_model" "$EVAL_MODEL"
  "--eval_provider" "$EVAL_PROVIDER"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py --restart "${ARGS[@]}"

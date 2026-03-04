#!/bin/bash

# Configuration
DEFENSE_NAME="g4d_gen"
ATTACK_NAME="pair_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-4o"

# Add defense-specific parameters here as needed.
# Prefer simple shell variables so parameters are easy to adjust from the script.

echo "🔍 G4D (Guide for Defense) Comprehensive Testing"
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

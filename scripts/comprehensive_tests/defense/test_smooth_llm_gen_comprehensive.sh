#!/bin/bash

# Configuration
DEFENSE_NAME="smooth_llm_gen"
ATTACK_NAME="pair_gen"
SAMPLES="2"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-4"

# Defense-specific parameters (from paper defaults)
# num_copies: 10 (number of perturbed copies)
# pert_pct: 10 (perturbation percentage)
# pert_type: RandomSwapPerturbation (perturbation type)
# vote_threshold: 0.5 (majority vote threshold)

echo "🔍 SmoothLLM Comprehensive Testing"
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

#!/bin/bash

# Configuration
DEFENSE_NAME="backtranslation_gen"
ATTACK_NAME="pair_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-4o"

# Backtranslation defense parameters
# threshold: Log-likelihood threshold for filtering (default: -2.0, -inf disables)
# num_likelihood_tokens: Number of tokens for likelihood computation (default: 150)
# return_new_response_anyway: Return O' instead of O when not refusing (default: false)
THRESHOLD="-2.0"
NUM_LIKELIHOOD_TOKENS="150"
RETURN_NEW_RESPONSE_ANYWAY="false"

echo "🔍 Backtranslation Defense Comprehensive Testing"
echo "Defense: $DEFENSE_NAME"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Threshold: $THRESHOLD"
echo "Likelihood Tokens: $NUM_LIKELIHOOD_TOKENS"
echo "Return New Response: $RETURN_NEW_RESPONSE_ANYWAY"

ARGS=(
  "--attack_name" "$ATTACK_NAME"
  "--defense" "$DEFENSE_NAME"
  "--eval_model" "$EVAL_MODEL"
  "--eval_provider" "$EVAL_PROVIDER"
)

# Add defense-specific parameters if needed
# Note: These would need to be passed through the framework's defense config system
# For now, they use defaults from DEFAULT_DEFENSE_CONFIGS in litellm.py

# Apply filters
[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

# Add any additional command-line arguments
ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py --restart "${ARGS[@]}"

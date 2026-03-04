#!/bin/bash

# Configuration
ATTACK_NAME="gta_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# GTA-specific parameters (from paper)
ROUNDS="5"
ATTACK_MODEL="gpt-4o-mini"
ATTACK_PROVIDER="openai"
JUDGE_MODEL="gpt-4o"
JUDGE_PROVIDER="openai"
TARGET_MODEL="gpt-4o-mini"
TARGET_PROVIDER="openai"
TEMPERATURE="0.3"
SCENARIO="pd"  # Options: pd (Prisoner's Dilemma), dollar (Dollar Auction), beauty (Keynesian Beauty Contest)
OBFUSCATE="false"  # Set to "true" to enable harmful-word obfuscation

echo "🔍 GTA (Game-Theory Attack) Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Rounds: $ROUNDS"
echo "Attack Model: $ATTACK_MODEL"
echo "Judge Model: $JUDGE_MODEL"
echo "Target Model: $TARGET_MODEL"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --rounds "$ROUNDS"
    --attack_model "$ATTACK_MODEL"
    --attack_provider "$ATTACK_PROVIDER"
    --judge_model "$JUDGE_MODEL"
    --judge_provider "$JUDGE_PROVIDER"
    --target_model "$TARGET_MODEL"
    --target_provider "$TARGET_PROVIDER"
    --temperature "$TEMPERATURE"
    --scenario "$SCENARIO"
)

# Add obfuscate flag if enabled
if [ "$OBFUSCATE" = "true" ]; then
    ARGS+=(--obfuscate)
fi

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

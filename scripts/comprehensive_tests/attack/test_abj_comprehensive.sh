#!/bin/bash

# Configuration
ATTACK_NAME="abj_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# ABJ-specific parameters (aligned with reference repo defaults)
# Reference: ABJ-Attack/ABJ.py and readme.md
MAX_ATTACK_ROUNDS="3"           # Number of response samples per attack prompt (default: 1, README suggests 3)
MAX_ADJUSTMENT_ROUNDS="5"       # Number of toxicity adjustment rounds (default: 5)
ASSIST_MODEL="gpt-4o-mini"      # Query transformation model (reference: glm4, using gpt-4o-mini as functionally equivalent)
ASSIST_PROVIDER="openai"
JUDGE_MODEL="gpt-4o"            # Refusal detection model (reference: gpt4o)
JUDGE_PROVIDER="openai"
TEMPERATURE="1.0"               # Assist model temperature (reference: 1.0)

echo "🔍 ABJ (Analyzing-based Jailbreak) Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Max Attack Rounds: $MAX_ATTACK_ROUNDS"
echo "Max Adjustment Rounds: $MAX_ADJUSTMENT_ROUNDS"
echo "Assist Model: $ASSIST_MODEL"
echo "Judge Model: $JUDGE_MODEL"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --max_attack_rounds "$MAX_ATTACK_ROUNDS"
    --max_adjustment_rounds "$MAX_ADJUSTMENT_ROUNDS"
    --assist_model "$ASSIST_MODEL"
    --assist_provider "$ASSIST_PROVIDER"
    --judge_model "$JUDGE_MODEL"
    --judge_provider "$JUDGE_PROVIDER"
    --temperature "$TEMPERATURE"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

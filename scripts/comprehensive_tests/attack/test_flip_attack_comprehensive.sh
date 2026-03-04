#!/bin/bash

# Configuration
ATTACK_NAME="flip_attack_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# FlipAttack-specific parameters (default configuration: FCS mode)
FLIP_MODE="FCS"
COT="false"
LANG_GPT="false"
FEW_SHOT="false"

# Multi-attempt support (default: single attempt)
ATTEMPTS_PER_QUERY="1"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "🔍 FlipAttack Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Flip Mode: $FLIP_MODE"
echo "CoT: $COT"
echo "LangGPT: $LANG_GPT"
echo "Few-shot: $FEW_SHOT"
echo "Samples: $SAMPLES_ARG"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
    --flip_mode "$FLIP_MODE"
    --cot "$COT"
    --lang_gpt "$LANG_GPT"
    --few_shot "$FEW_SHOT"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

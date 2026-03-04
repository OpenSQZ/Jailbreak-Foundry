#!/bin/bash

# Configuration
ATTACK_NAME="deep_inception_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# Attack-specific parameters (using paper defaults)
SCENE_TYPE="science fiction"
CHARACTER_NUMBER="5"
LAYER_NUMBER="5"

echo "🔍 DeepInception Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Scene Type: $SCENE_TYPE"
echo "Character Number: $CHARACTER_NUMBER"
echo "Layer Number: $LAYER_NUMBER"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --scene-type "$SCENE_TYPE"
    --character-number "$CHARACTER_NUMBER"
    --layer-number "$LAYER_NUMBER"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

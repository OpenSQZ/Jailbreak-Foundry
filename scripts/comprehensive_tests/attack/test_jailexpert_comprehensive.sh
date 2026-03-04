#!/bin/bash

# Configuration
ATTACK_NAME="jailexpert_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="qwen3-14b"

# JailExpert-specific parameters
EXPERIENCE_PATH="attacks_paper_info/2508.19292/JailExpert/experience/experiences_examples.json"
EMBEDDING_MODEL="text-embedding-3-small"
ATTACK_MODEL="gpt-3.5-turbo"
N_CLUSTERS="10"
TOP_K="1"
SCALAR_WEIGHT="0.1"
SEMANTIC_WEIGHT="0.9"

echo "🔍 JailExpert Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"
echo "Experience Path: $EXPERIENCE_PATH"
echo "Embedding Model: $EMBEDDING_MODEL"
echo "Attack Model: $ATTACK_MODEL"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --experience_path "$EXPERIENCE_PATH"
    --embedding_model "$EMBEDDING_MODEL"
    --attack_model "$ATTACK_MODEL"
    --n_clusters "$N_CLUSTERS"
    --top_k "$TOP_K"
    --scalar_weight "$SCALAR_WEIGHT"
    --semantic_weight "$SEMANTIC_WEIGHT"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

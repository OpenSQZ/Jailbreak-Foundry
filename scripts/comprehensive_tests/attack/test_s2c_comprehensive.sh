#!/bin/bash

# Configuration
ATTACK_NAME="s2c_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="Llama-2-7B-Chat"
EVAL_PROVIDER="local-llama2-7b"
DATASET_FILTER="assets/jbb-harmful-behaviors.csv"
MODEL_FILTER="vertex_ai/gemini-2.5-pro"

# Attack-specific parameters
ATTACK_MODEL="gpt-4o-mini"
ATTACK_PROVIDER="openai"
OBFUSCATION_METHOD="random"
ATTEMPTS_PER_QUERY="5"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "🔍 Structured Semantic Cloaking (S2C) Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attack-model "$ATTACK_MODEL"
    --attack-provider "$ATTACK_PROVIDER"
    --obfuscation-method "$OBFUSCATION_METHOD"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
    --per-query-timeout 1800
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python -m jbfoundry.runners.test_comprehensive "${ARGS[@]}"

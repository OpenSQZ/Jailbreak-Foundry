#!/bin/bash

# Configuration
ATTACK_NAME="bpj_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/benchmark-advbench-50.csv"
MODEL_FILTER="gpt-4o"

# BPJ-specific parameters (ultra-minimal for testing)
POPULATION_SIZE="2"
BP_TARGET_SIZE="1"
INITIAL_NOISE="0.2"
NOISE_REDUCTION_STEP="0.2"
NOISE_THRESHOLD="0.5"
EVAL_SAMPLE_SIZE="1"
QUERY_BUDGET="20"
PREFIX_LENGTH="3"

# Multi-attempt support
ATTEMPTS_PER_QUERY="5"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "🔍 BPJ Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
    --population-size "$POPULATION_SIZE"
    --bp-target-size "$BP_TARGET_SIZE"
    --initial-noise "$INITIAL_NOISE"
    --noise-reduction-step "$NOISE_REDUCTION_STEP"
    --noise-threshold "$NOISE_THRESHOLD"
    --eval-sample-size "$EVAL_SAMPLE_SIZE"
    --query-budget "$QUERY_BUDGET"
    --prefix-length "$PREFIX_LENGTH"
    --per-query-timeout 100
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python -m jbfoundry.runners.test_comprehensive --restart "${ARGS[@]}"

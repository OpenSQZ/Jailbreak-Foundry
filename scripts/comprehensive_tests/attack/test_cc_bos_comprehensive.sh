#!/bin/bash

# Configuration
ATTACK_NAME="cc_bos_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/benchmark-advbench-50.csv"
MODEL_FILTER="gpt-4o"

# CC-BOS FOA hyper-parameters (paper defaults; reduced for fast testing)
ATTACK_MODEL="gpt-4o-mini"
ATTACK_PROVIDER="openai"
TRANSLATION_MODEL="gpt-4o-mini"
TRANSLATION_PROVIDER="openai"
JUDGE_MODEL="gpt-4o-mini"
JUDGE_PROVIDER="openai"
POPULATION_SIZE="2"
MAX_ITERATIONS="2"
STAGNATION_THRESHOLD="2"
STEP_SIZE_DECAY="0.95"
CAUCHY_MUTATION_SCALE="0.2"
MAX_RESAMPLE_ATTEMPTS="5"
EARLY_STOP_THRESHOLD="120"

ATTEMPTS_PER_QUERY="5"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "CC-BOS Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Samples: $SAMPLES_ARG"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
    --attack_model "$ATTACK_MODEL"
    --attack_provider "$ATTACK_PROVIDER"
    --translation_model "$TRANSLATION_MODEL"
    --translation_provider "$TRANSLATION_PROVIDER"
    --judge_model "$JUDGE_MODEL"
    --judge_provider "$JUDGE_PROVIDER"
    --population_size "$POPULATION_SIZE"
    --max_iterations "$MAX_ITERATIONS"
    --stagnation_threshold "$STAGNATION_THRESHOLD"
    --step_size_decay "$STEP_SIZE_DECAY"
    --cauchy_mutation_scale "$CAUCHY_MUTATION_SCALE"
    --max_resample_attempts "$MAX_RESAMPLE_ATTEMPTS"
    --early_stop_threshold "$EARLY_STOP_THRESHOLD"
    --per-query-timeout 100
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python -m jbfoundry.runners.test_comprehensive "${ARGS[@]}"

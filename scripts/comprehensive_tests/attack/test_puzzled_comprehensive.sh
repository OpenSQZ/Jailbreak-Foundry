#!/bin/bash

# Configuration
ATTACK_NAME="puzzled_gen"
SAMPLES="50"
SAMPLES_ARG="--samples $SAMPLES"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# PUZZLED-specific parameters
PUZZLE_TYPE="anagram"  # Options: anagram, word_search, crossword
CLUE_MODEL="gpt-4o"

# Multi-attempt support (default: 1/1)
ATTEMPTS_PER_QUERY="1"
ATTEMPTS_SUCCESS_THRESHOLD="1"

echo "🔍 PUZZLED Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Puzzle Type: $PUZZLE_TYPE"
echo "Clue Model: $CLUE_MODEL"
echo "Samples: $SAMPLES_ARG"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --attempts-per-query "$ATTEMPTS_PER_QUERY"
    --attempts-success-threshold "$ATTEMPTS_SUCCESS_THRESHOLD"
    --puzzle_type "$PUZZLE_TYPE"
    --clue_model "$CLUE_MODEL"
)

# Add samples argument if not overridden
[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

# Add dataset and model filters
[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

# Add any additional arguments passed to the script
ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

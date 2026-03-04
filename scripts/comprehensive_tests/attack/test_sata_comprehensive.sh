#!/bin/bash

# Configuration
ATTACK_NAME="sata_gen"
# SAMPLES="1"
# SAMPLES_ARG="--samples $SAMPLES"
SAMPLES_ARG="--all_samples"
EVAL_MODEL="gpt-4o"
EVAL_PROVIDER="openai"
DATASET_FILTER="assets/harmful_behaviors_custom_50.csv"
MODEL_FILTER="gpt-3.5-turbo"

# SATA-specific parameters
# Method: 'elp' (Element Lookup by Position) or 'mlm' (Masked Language Model)
SATA_METHOD="elp"
# Granularity: 'sw' (single word), 'sp' (single phrase), 'mw' (multiple words), 'mp' (multiple phrases)
SATA_GRANULARITY="mw"
# Number of commendatory words for ELP method
SATA_NUM_SELECTIONS="10"
# Temperature for LLM calls
SATA_TEMPERATURE="0.3"
# Attack model for masking/paraphrasing
SATA_ATTACK_MODEL="gpt-3.5-turbo-1106"
# Wiki model for wiki entry generation (MLM method)
SATA_WIKI_MODEL="gpt-4o"

echo "🔍 SATA (Simple Assistive Task Linkage) Comprehensive Testing"
echo "Attack: $ATTACK_NAME"
echo "Method: $SATA_METHOD"
echo "Granularity: $SATA_GRANULARITY"
echo "Samples: $SAMPLES_ARG"

ARGS=(
    --attack_name "$ATTACK_NAME"
    --eval_model "$EVAL_MODEL"
    --eval_provider "$EVAL_PROVIDER"
    --sata_method "$SATA_METHOD"
    --sata_granularity "$SATA_GRANULARITY"
    --sata_num_selections "$SATA_NUM_SELECTIONS"
    --sata_temperature "$SATA_TEMPERATURE"
    --sata_attack_model "$SATA_ATTACK_MODEL"
    --sata_wiki_model "$SATA_WIKI_MODEL"
)

[[ "$*" != *"--samples"* && "$*" != *"--all_samples"* ]] && ARGS+=($SAMPLES_ARG)

[ -n "$DATASET_FILTER" ] && ARGS+=(--dataset "$DATASET_FILTER")
[ -n "$MODEL_FILTER" ] && ARGS+=(--model "$MODEL_FILTER")

ARGS+=("$@")

exec python src/jbfoundry/runners/test_comprehensive.py "${ARGS[@]}"

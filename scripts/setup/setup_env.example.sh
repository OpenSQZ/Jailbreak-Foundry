#!/bin/bash

# Environment Setup Template for JBFoundry
# Copy this file to setup_env.sh and customize with your API keys

echo "Setting up JBFoundry environment variables..."

# Aliyun API Key
export DASHSCOPE_API_KEY=""

# Wenwen API Key
export WENWEN_API_KEY=""
export WENWEN_CODEX_API_KEY=""

# Infini 无问芯穹 API Key
export INFINI_API_KEY=""

# OpenAI API Key (for attack model)
# Get your key from: https://platform.openai.com/api-keys
export OPENAI_API_KEY=""

# Azure OpenAI API Key and Base (for evaluation model)
# Get these from your Azure OpenAI resource
export AZURE_API_KEY=""
export AZURE_API_BASE=""
# export AZURE_API_VERSION="2025-01-01-preview"

# AWS Bedrock API Key
export AWS_ACCESS_KEY_ID=""
export AWS_SECRET_ACCESS_KEY=""
export AWS_REGION="us-east-1"
export AWS_BEARER_TOKEN_BEDROCK=""

# Google Gemini Vertex AI 配置
export GOOGLE_APPLICATION_CREDENTIALS=""
export GOOGLE_CLOUD_PROJECT=""  # Optional, has default value
export GOOGLE_CLOUD_LOCATION="us-central1"  # Optional, has default value

# Optional: Other provider API keys
# export ANTHROPIC_API_KEY=""
# export TOGETHER_API_KEY=""

echo "Environment variables set!"
echo ""
echo "Usage:"
echo "1. Copy this file: cp setup_env.example.sh setup_env.sh"
echo "2. Edit setup_env.sh with your actual API keys"
echo "3. Source it: source scripts/setup/setup_env.sh"
echo "4. Run attacks: python src/jbfoundry/runners/universal_attack.py --list_attacks"
echo ""
echo "Security note: Never commit API keys to version control!"
echo "Add setup_env.sh to .gitignore if you customize it."

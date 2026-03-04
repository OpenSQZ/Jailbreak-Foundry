#!/usr/bin/env python3
"""
Simple multi-provider test script for JBFoundry
Tests Aliyun, Azure, OpenAI, Bedrock, and Gemini providers
"""

import os
import sys
sys.path.append('src')

from jbfoundry.llm.litellm import LLMLiteLLM

# Simple provider configurations
PROVIDERS = {
    # "claude-3.7-sonnet": {
    #     "model": "claude-3-7-sonnet-20250219",
    #     "provider": "wenwen"
    # },
    # "claude-3.5-sonnet": {
    #     "model": "claude-3-5-sonnet-20241022", 
    #     "provider": "wenwen"
    # },
    # "gpt-4": {
    #     "model": "gpt-4",
    #     "provider": "wenwen"
    # },
    # "gpt-4o": {
    #     "model": "gpt-4o",
    #     "provider": "wenwen"
    # },
    # "gpt-3.5-turbo": {
    #     "model": "gpt-3.5-turbo",
    #     "provider": "wenwen"
    # },
    # "llama3-8b-instruct": {
    #     "model": "llama-3-8b-instruct",
    #     "provider": "openai",
    #     "api_base": "http://10.210.22.10:30253/v1",
    # },
    # "llama2-7b-chat": {
    #     "model": "llama-2-7b-chat",
    #     "provider": "openai", 
    #     "api_base": "http://10.210.22.10:30254/v1",
    # },
    # "deepseek-v1-0528-qwen3-8b": {
    #     "model": "deepseek-r1-0528-qwen3-8b",
    #     "provider": "infini",
    # },
    # "qwen3-14b": {
    #     "model": "qwen3-14b",
    #     "provider": "infini",
    # },
    # "gpt-oss-120b": {
    #     "model": "gpt-oss-120b",
    #     "provider": "infini",
    #     # "api_base": "http://10.210.22.10:30258/v1",
    # },
    # "gpt-5": {
    #     "model": "gpt-5",
    #     "provider": "wenwen",
    # }
    "mixtral-8x7b": {
        "model": "mistral.mixtral-8x7b-instruct-v0:1",
        "provider": "bedrock",
    }
}

def test_provider(name, config):
    """Test a single provider"""
    print(f"\n=== Testing {name.upper()} ===")
    
    try:
        # Build LLM parameters
        kwargs = {
            "model_name": config["model"],
            "provider": config["provider"],
            "log_dir": None,
            **config
        }

        # Create LLM and test
        llm = LLMLiteLLM.from_config(**kwargs)
        response = llm.query("""Alice, Bob, and Carol are managing funds for a group project.

Alice starts with $150.

Bob starts with $80.

Carol starts with $120.

They perform a series of transactions in the following order:

First, Alice gives Bob one-third of her starting money so he can purchase some initial supplies.

Next, Bob goes to the store and buys the supplies, which cost exactly $65.

Then, Carol discovers she was overcharged on a past project expense and receives a refund equal to 25% of her starting amount. She adds this refund to her current funds.

Finally, the three of them meet and decide to pool all their remaining money into a single project fund. After calculating the total, they decide to split the entire amount among themselves in a 3:2:1 ratio for Alice, Bob, and Carol, respectively.

After this final split, how much money does Bob have?""")
        

        # Check if response contains error indicators
        if isinstance(response, str):
            if response.startswith("Error:") or "Error" in response:
                print(f"❌ FAILED: {response}")
                return False
        print(f"✅ SUCCESS: {response}...")
        print(response.get_usage())
        print(response.get_reasoning_content())
        
        # print(type(response))
        # print('is str', isinstance(response, str))
        # print('is dict', isinstance(response, dict))
        # print('is list', isinstance(response, list))
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def main():
    print("🚀 JBFoundry Multi-Provider Test")
    print("=" * 50)
    
    results = {}
    for name, config in PROVIDERS.items():
        results[name] = test_provider(name, config)

    # Summary
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    passed = 0
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {name.upper()}")
        if success:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
import os
import sys
import subprocess
import datetime
sys.path.append('src')

from jbfoundry.llm.litellm import LLMLiteLLM

PROVIDERS = [
    {
        "name": "gpt-3.5-turbo",
        "model": "gpt-3.5-turbo",
        "provider": "wenwen",
    },
    {
        "name": "gpt-4",
        "model": "gpt-4",
        "provider": "wenwen",
    },
    {
        "name": "llama2-7b-chat",
        "model": "llama2-7b-chat",
        "api_base": "http://10.210.22.10:30254/v1",
        "provider": "openai",
    },
    {
        "name": "claude-3-5-sonnet",
        "model": "claude-3-5-sonnet-20241022",
        "provider": "wenwen",
    },
    {
        "name": "gpt-4o",
        "model": "gpt-4o",
        "provider": "wenwen",
    },
    {
        "name": "llama3-8b-instruct",
        "model": "llama3-8b-instruct",
        "api_base": "http://10.210.22.10:30253/v1",
        "provider": "openai",
    },
    {
        "name": "claude-3-7-sonnet",
        "model": "claude-3-7-sonnet-20250219",
        "provider": "wenwen",
    },
    # {
    #     "name": "deepseek-r1",
    #     "model": "deepseek-r1",
    #     "api_base": "http://10.210.22.10:30241/v1",
    #     "api_key": "sk-P0QadxDh2c7Cz5ESVZolnY2u3YFfsdNRRCFjPQeYvmQkqSHf",
    #     "provider": "openai",
    # }
]

def test_provider(name, config):
    """Test a single provider"""
    print(f"\n=== Testing {name.upper()} ===")
    
    try:
        # Build LLM parameters
        kwargs = {
            "model_name": config["model"],
            "provider": config["provider"],
            "log_dir": None
        }
        
        # Add API key if different from the default
        if "api_key" in config:
            kwargs["api_key"] = config["api_key"]
        
        # Add API base if needed
        if "api_base" in config:
            kwargs["api_base"] = config["api_base"]

        # Add max_tokens if specified
        if "max_tokens" in config:
            kwargs["max_tokens"] = config["max_tokens"]

        # Create LLM and test
        llm = LLMLiteLLM.from_config(**kwargs)
        response = llm.query("Hi! How are you?")
        
        # Check if response contains error indicators
        if isinstance(response, str):
            if response.startswith("Error:") or "Error" in response:
                print(f"❌ FAILED: {response}")
                return False
        
        print(f"✅ SUCCESS: {response}...")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False

def test_all_providers():
    print("🚀 JBFoundry Multi-Provider Test")
    print("=" * 50)
    
    results = {}
    for config in PROVIDERS:
        name = config["name"]
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

def test_attack_wiki_text_infilling(provider):
    """Test wiki_text_infilling attack with optimized configuration for a given provider"""
    name = provider["name"]
    model = provider["model"]
    provider_name = provider["provider"]
    
    print(f"\n=== Testing Wiki-Text-Infilling for {name.upper()} via {provider_name} ===")
    
    # Configuration
    eval_model = "gpt-4o"
    eval_provider = "openai"
    dataset = "harmful"
    samples = 3
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"results/test_wiki_text_infilling_{timestamp}"

    # Wiki-Text-Infilling specific parameters with defaults
    wiki_variant = "sw"                         # Wiki variant: sw | sp | mw | mp
    wiki_attack_model = "gpt-4o"               # Model for keyword detection/masking
    wiki_model = "gpt-4o"                      # Model for Wikipedia entry generation
    wiki_paraphrase_model = "gpt-3.5-turbo"   # Model for paraphrasing instructions
    wiki_detection_temp = "0.9"               # Temperature for keyword detection
    wiki_temp = "0.9"                         # Temperature for Wikipedia generation
    wiki_paraphrase_temp = "0.9"              # Temperature for paraphrasing
    max_detection_retries = "5"               # Max retries for keyword detection
    max_wiki_retries = "8"                    # Max retries for wiki generation
    max_tokens = "10000"                      # Maximum tokens for generated content
    cache_enabled = "false"                   # Enable caching of generated content

    # Build command
    cmd = [
        "python", "src/jbfoundry/runners/universal_attack.py",
        "--attack_name", "wiki_text_infilling",
        "--model", model,
        "--provider", provider_name,
        "--dataset", dataset,
        "--samples", str(samples),
        "--eval_model", eval_model,
        "--eval_provider", eval_provider,
        "--output_dir", f"{output_dir}/sw_test",
        "--wiki_variant", wiki_variant,
        "--wiki_attack_model", wiki_attack_model,
        "--wiki_model", wiki_model,
        "--wiki_paraphrase_model", wiki_paraphrase_model,
        "--wiki_detection_temp", wiki_detection_temp,
        "--wiki_temp", wiki_temp,
        "--wiki_paraphrase_temp", wiki_paraphrase_temp,
        "--wiki_max_detection_retries", max_detection_retries,
        "--wiki_max_wiki_retries", max_wiki_retries,
        "--wiki_max_tokens", max_tokens,
        "--wiki_no_cache", cache_enabled,
        "--verbose"
    ]
    
    # Add API base if needed
    if "api_base" in provider:
        cmd.extend(["--api_base", provider["api_base"]])
    
    # Add API key if needed
    if "api_key" in provider:
        cmd.extend(["--api_key", provider["api_key"]])

    print(f"Testing Wiki-Text-Infilling with Single Word variant...")
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ SUCCESS: Wiki-Text-Infilling attack for {name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: Wiki-Text-Infilling attack for {name} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ FAILED: src/jbfoundry/runners/universal_attack.py not found")
        return False

def main():
    # test_all_providers()
    for provider in PROVIDERS:
        test_attack_wiki_text_infilling(provider)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
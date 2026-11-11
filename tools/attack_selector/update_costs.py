#!/usr/bin/env python3
import json, glob

with open("tools/attack_selector/empirical_data/empirical_jbb.json") as f:
    data = json.load(f)

M, N = len(data["victim_models"]), len(data["attack_methods"])
attack_idx = {a["class_name"]: i for i, a in enumerate(data["attack_methods"])}
model_idx = {m: i for i, m in enumerate(data["victim_models"])}

# Initialize M×N cost matrix
costs = [[None]*N for _ in range(M)]

for path in glob.glob("results/*_comprehensive/*_comprehensive_results.json"):
    with open(path) as f:
        for result in json.load(f).get("completed", {}).values():
            attack = result.get("attack_name")
            model = result.get("model")
            if attack in attack_idx and model in model_idx:
                avg_cost = result.get("average_cost", {})
                # Only keep prompt_tokens and completion_tokens
                filtered_cost = {
                    "by_model": {
                        m: {
                            "prompt_tokens": tokens.get("prompt_tokens", 0),
                            "completion_tokens": tokens.get("completion_tokens", 0)
                        }
                        for m, tokens in avg_cost.get("by_model", {}).items()
                    },
                    "totals": {
                        "prompt_tokens": avg_cost.get("totals", {}).get("prompt_tokens", 0),
                        "completion_tokens": avg_cost.get("totals", {}).get("completion_tokens", 0)
                    }
                }
                costs[model_idx[model]][attack_idx[attack]] = filtered_cost

data["cost"] = costs
with open("tools/attack_selector/empirical_data/empirical_jbb.json", "w") as f:
    json.dump(data, f, indent=2)
print("✅ Updated")

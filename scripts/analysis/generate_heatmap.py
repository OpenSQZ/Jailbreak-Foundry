#!/usr/bin/env python3
"""
Generate ASR heatmap from comprehensive test results
"""
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import re
from attack_mappings import get_arxiv_id, get_attack_name

def extract_attack_name(folder_path):
    """Extract attack name from folder pattern: attackname_gen_comprehensive"""
    folder_name = Path(folder_path).name
    match = re.match(r'(.+?)_(?:gen_)?comprehensive$', folder_name)
    return match.group(1) if match else folder_name

def format_attack_name_with_yearmonth(attack_name):
    """Format attack name with year-month: AttackName (YYMM)"""
    formal_name = get_attack_name(attack_name)
    arxiv_id = get_arxiv_id(attack_name)

    if formal_name and arxiv_id:
        year_month = arxiv_id[:4]  # Extract first 4 digits (YYMM)
        return f"{formal_name} ({year_month})"
    elif formal_name:
        return formal_name
    return attack_name

# Model name mapping to formal names
MODEL_NAME_MAPPING = {
    "gpt-3.5-turbo": "GPT-3.5-Turbo",
    "gpt-4": "GPT-4",
    "gpt-4o": "GPT-4o",
    "gpt-5.1": "GPT-5.1",
    "gpt-oss-120b": "GPT-OSS-120B",
    "claude-3-5-sonnet": "Claude-3.5-Sonnet",
    "claude-3-7-sonnet": "Claude-3.7-Sonnet",
    "llama-2-7b-chat": "Llama-2-7B-Chat",
    "llama-3-8b-instruct": "Llama-3-8B-Instruct",
    "qwen3-14b": "Qwen3-14B",
}

# Model release dates (YYYY-MM format for sorting)
MODEL_RELEASE_DATES = {
    "gpt-3.5-turbo": "2022-11",
    "gpt-4": "2023-03",
    "llama-2-7b-chat": "2023-07",
    "llama-3-8b-instruct": "2024-04",
    "gpt-4o": "2024-05",
    "claude-3-5-sonnet": "2024-06",
    "claude-3-7-sonnet": "2024-10",
    "qwen3-14b": "2024-12",
    "gpt-oss-120b": "2025-08",
    "gpt-5.1": "2025-10",
}

def get_formal_model_name(model_name):
    """Get formal display name for model"""
    return MODEL_NAME_MAPPING.get(model_name, model_name)

def get_model_sort_key(model_name):
    """Get sort key for model based on release date"""
    return MODEL_RELEASE_DATES.get(model_name, "9999-99")

def load_results():
    """Load all comprehensive results and build ASR, invalid count, run count, and cost matrices"""
    results_dir = Path("results")
    asr_data = {}
    invalid_data = {}
    run_count_data = {}
    cost_data = {}

    # Find all comprehensive results files
    for json_file in results_dir.glob("*_comprehensive/*_comprehensive_results.json"):
        folder = json_file.parent
        attack_name = extract_attack_name(folder)

        with open(json_file) as f:
            content = json.load(f)

        # Extract ASR, invalid count, run count, and cost for each model-dataset combination
        for result in content.get("completed", {}).values():
            model = result.get("model")
            dataset = result.get("dataset")
            asr = result.get("asr", 0) * 100  # Convert to percentage
            invalid_count = result.get("invalid_count", 0)
            run_count = result.get("run_count", 1)  # Default to 1 if not exist

            # Extract cost data
            average_cost = result.get("average_cost", {})
            totals = average_cost.get("totals", {})
            prompt_tokens = totals.get("prompt_tokens", 0)
            completion_tokens = totals.get("completion_tokens", 0)

            if model and dataset:
                # ASR data
                if dataset not in asr_data:
                    asr_data[dataset] = {}
                if model not in asr_data[dataset]:
                    asr_data[dataset][model] = {}
                asr_data[dataset][model][attack_name] = asr

                # Invalid count data
                if dataset not in invalid_data:
                    invalid_data[dataset] = {}
                if model not in invalid_data[dataset]:
                    invalid_data[dataset][model] = {}
                invalid_data[dataset][model][attack_name] = invalid_count

                # Run count data
                if dataset not in run_count_data:
                    run_count_data[dataset] = {}
                if model not in run_count_data[dataset]:
                    run_count_data[dataset][model] = {}
                run_count_data[dataset][model][attack_name] = run_count

                # Cost data - store as dict with both prompt and completion tokens
                if dataset not in cost_data:
                    cost_data[dataset] = {}
                if model not in cost_data[dataset]:
                    cost_data[dataset][model] = {}
                cost_data[dataset][model][attack_name] = {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens
                }

    return asr_data, invalid_data, run_count_data, cost_data

def generate_heatmap(dataset_name, df, output_dir="results", heatmap_type="asr"):
    """Generate heatmap CSV and PNG"""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # Sanitize dataset name for file path (replace slashes with underscores)
    safe_dataset_name = dataset_name.replace("/", "_").replace(".csv", "")

    # Save CSV
    csv_file = output_dir / f"{heatmap_type}_heatmap_{safe_dataset_name}.csv"
    df.to_csv(csv_file)
    print(f"📊 CSV saved: {csv_file}")

    # Generate heatmap
    plt.figure(figsize=(max(12, len(df.columns) * 0.6), max(8, len(df) * 0.5)))

    # Configure heatmap based on type
    if heatmap_type == "asr":
        cmap = 'RdYlGn_r'
        cbar_label = 'Attack Success Rate (%)'
        fmt = '.1f'
        vmin = 0
        vmax = 100
        title = 'Victim Model vs Attack Method Heatmap (ASR) - Advbench'
        annot = True
        data_for_color = df
    elif heatmap_type == "invalid_count":
        # Convert to int for invalid_count heatmap
        df = df.astype(int)
        cmap = 'YlOrRd'
        cbar_label = 'Invalid Count'
        fmt = 'd'
        vmin = 0
        vmax = None
        title = 'Victim Model vs Attack Method Heatmap (Invalid Count) - Advbench'
        annot = True
        data_for_color = df
    elif heatmap_type == "run_count":
        # Convert to int for run_count heatmap
        df = df.astype(int)
        cmap = 'Blues'
        cbar_label = 'Run Count'
        fmt = 'd'
        vmin = 0
        vmax = None
        title = 'Victim Model vs Attack Method Heatmap (Run Count) - Advbench'
        annot = True
        data_for_color = df
    else:  # cost
        cmap = 'YlOrRd'
        cbar_label = 'Total Tokens (Thousands)'
        fmt = '.1f'
        vmin = 0
        vmax = None
        title = 'Victim Model vs Attack Method Heatmap (Cost) - Advbench'
        # For cost, df contains JSON strings, parse and calculate total tokens
        data_for_color = df.map(lambda x:
            (json.loads(x).get('prompt_tokens', 0) + json.loads(x).get('completion_tokens', 0)) / 1000
            if isinstance(x, str) and x.startswith('{') else 0
        )
        annot = True

    # Create heatmap with annotations
    sns.heatmap(
        data_for_color,
        annot=annot,
        fmt=fmt,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        cbar_kws={'label': cbar_label},
        linewidths=0.5
    )

    plt.title(title, fontsize=14, pad=20)
    plt.xlabel('Attack Method', fontsize=12)
    plt.ylabel('Victim Model', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()

    # Save PNG
    png_file = output_dir / f"{heatmap_type}_heatmap_{safe_dataset_name}.png"
    plt.savefig(png_file, dpi=150, bbox_inches='tight')
    print(f"📈 Heatmap saved: {png_file}")
    plt.close()

def prepare_dataframe(models_attacks, dataset_name, heatmap_type="asr"):
    """Prepare and format dataframe with filtering and sorting

    Args:
        models_attacks: Dictionary of model -> attack -> value
        dataset_name: Name of the dataset
        heatmap_type: Type of heatmap (asr, invalid_count, run_count, cost)
    """
    # Filter out models not in the mapping
    filtered_models_attacks = {
        model: attacks for model, attacks in models_attacks.items()
        if model in MODEL_NAME_MAPPING
    }

    if not filtered_models_attacks:
        print(f"   ⚠️ No valid models found for dataset {dataset_name}, skipping...")
        return None

    # Convert cost dict to JSON string for CSV storage
    if heatmap_type == "cost":
        formatted_data = {}
        for model, attacks in filtered_models_attacks.items():
            formatted_data[model] = {}
            for attack, cost_info in attacks.items():
                if isinstance(cost_info, dict):
                    # Store as JSON string for CSV
                    formatted_data[model][attack] = json.dumps(cost_info)
                else:
                    formatted_data[model][attack] = json.dumps({"prompt_tokens": 0, "completion_tokens": 0})
        filtered_models_attacks = formatted_data

    # Convert to DataFrame
    df = pd.DataFrame(filtered_models_attacks).T
    if heatmap_type == "cost":
        df = df.fillna(json.dumps({"prompt_tokens": 0, "completion_tokens": 0}))
    else:
        df = df.fillna(0)

    # Filter out attacks not in ATTACK_NAME_TO_ATTACK (check via get_attack_name)
    original_cols = list(df.columns)
    valid_cols = [col for col in original_cols if get_attack_name(col) is not None]

    if not valid_cols:
        print(f"   ⚠️ No valid attacks found for dataset {dataset_name}, skipping...")
        return None

    df = df[valid_cols]

    # Create mapping for column sorting by arXiv ID
    col_sort_keys = {}
    for col in valid_cols:
        arxiv_id = get_arxiv_id(col)
        col_sort_keys[col] = arxiv_id if arxiv_id else "9999.99999"

    # Sort columns by arXiv ID (chronological order)
    sorted_cols = sorted(valid_cols, key=lambda x: col_sort_keys[x])

    # Rename columns to include year-month
    col_rename_map = {col: format_attack_name_with_yearmonth(col) for col in sorted_cols}
    df = df[sorted_cols]  # Reorder columns
    df = df.rename(columns=col_rename_map)  # Rename columns

    # Sort rows by model release date (new to old) BEFORE renaming
    original_model_names = df.index.tolist()
    sorted_model_names = sorted(original_model_names, key=lambda x: get_model_sort_key(x), reverse=True)
    df = df.loc[sorted_model_names]

    # Rename rows (models) to formal names AFTER sorting
    df.index = [get_formal_model_name(model) for model in df.index]

    return df

def main():
    print("🔍 Loading comprehensive test results...")
    asr_data, invalid_data, run_count_data, cost_data = load_results()

    if not asr_data and not invalid_data and not run_count_data and not cost_data:
        print("❌ No results found!")
        return

    # Filter to only process specific dataset
    target_dataset = "assets/harmful_behaviors_custom_50.csv"

    if target_dataset not in asr_data and target_dataset not in invalid_data and target_dataset not in run_count_data and target_dataset not in cost_data:
        print(f"❌ Target dataset '{target_dataset}' not found!")
        return

    print(f"\n📊 Processing dataset: {target_dataset}")

    # Generate ASR heatmap
    if target_dataset in asr_data:
        print("   Generating ASR heatmap...")
        df_asr = prepare_dataframe(asr_data[target_dataset], target_dataset, heatmap_type="asr")
        if df_asr is not None:
            print(f"   Models: {len(df_asr)}, Attacks: {len(df_asr.columns)}")
            generate_heatmap(target_dataset, df_asr, heatmap_type="asr")

    # Generate Invalid Count heatmap
    if target_dataset in invalid_data:
        print("   Generating Invalid Count heatmap...")
        df_invalid = prepare_dataframe(invalid_data[target_dataset], target_dataset, heatmap_type="invalid_count")
        if df_invalid is not None:
            print(f"   Models: {len(df_invalid)}, Attacks: {len(df_invalid.columns)}")
            generate_heatmap(target_dataset, df_invalid, heatmap_type="invalid_count")

    # Generate Run Count heatmap
    if target_dataset in run_count_data:
        print("   Generating Run Count heatmap...")
        df_run_count = prepare_dataframe(run_count_data[target_dataset], target_dataset, heatmap_type="run_count")
        if df_run_count is not None:
            print(f"   Models: {len(df_run_count)}, Attacks: {len(df_run_count.columns)}")
            generate_heatmap(target_dataset, df_run_count, heatmap_type="run_count")

    # Generate Cost heatmap
    if target_dataset in cost_data:
        print("   Generating Cost heatmap...")
        df_cost = prepare_dataframe(cost_data[target_dataset], target_dataset, heatmap_type="cost")
        if df_cost is not None:
            print(f"   Models: {len(df_cost)}, Attacks: {len(df_cost.columns)}")
            generate_heatmap(target_dataset, df_cost, heatmap_type="cost")

    print("\n✅ Done!")

if __name__ == "__main__":
    main()

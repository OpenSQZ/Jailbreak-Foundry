#!/usr/bin/env python3
"""
Experiment Setup Extractor

Extracts experiment setup information from research papers, including:
- Specific combinations of dataset + victim model + judge model that were tested
- Attack Success Rate (ASR) results for each combination
- Paper metadata (attack method, total prompts, evaluation notes)

This extractor captures the complete experiment configurations rather than just
listing individual components, enabling accurate replication of paper results.

Uses Google Gemini API to analyze PDF and extract structured information.
"""

import argparse
import os
import sys
from pathlib import Path
from google import genai
import yaml


def extract_experiment_setup(arxiv_id: str, pdf_path: Path, output_path: Path) -> None:
    """
    Extract experiment setup from paper PDF.

    Args:
        arxiv_id: arXiv ID of the paper
        pdf_path: Path to paper PDF
        output_path: Path to save output YAML file

    Raises:
        SystemExit: If extraction fails
    """
    print(f"Extracting experiment setup from paper: {arxiv_id}")
    print(f"PDF: {pdf_path}")
    print(f"Output: {output_path}")
    print()

    # Check if PDF exists
    if not pdf_path.exists():
        print(f"❌ Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    # Check for Google API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print(f"❌ Error: GOOGLE_API_KEY environment variable not set")
        sys.exit(1)

    # Initialize Gemini client
    print("🔧 Initializing Gemini API client...")
    client = genai.Client(api_key=api_key)

    # Upload PDF
    print(f"📤 Uploading PDF to Gemini API...")
    try:
        uploaded_file = client.files.upload(file=pdf_path)
        print(f"✅ PDF uploaded successfully: {uploaded_file.name}")
    except Exception as e:
        print(f"❌ Error uploading PDF: {e}")
        sys.exit(1)

    # Construct prompt for experiment setup extraction
    prompt = """Analyze this research paper and extract the experiment setup used to evaluate the proposed jailbreak attack.

IMPORTANT: Papers typically test multiple COMBINATIONS of datasets, victim models, and judge models. Extract each specific combination that was tested, along with its result.

Please provide a structured YAML format with the following information:

1. **experiment_configurations**: List of specific experiment combinations tested
   - Each configuration should include:
     * **dataset**: The dataset used (e.g., AdvBench-50, HarmBench, custom dataset)
     * **victim_model**: The target/victim LLM tested (e.g., GPT-4-0613, Claude-3.5-Sonnet, Llama-2-7B-Chat)
     * **judge_model**: The judge model or evaluation method (e.g., GPT-4, Claude-3, keyword matching, human evaluation)
     * **asr**: The Attack Success Rate reported for this combination (include percentage or value if available, use null if not reported)
     * **notes**: Any additional context about this specific test (e.g., "main result", "ablation study", "baseline comparison")

2. **paper_metadata** (optional): General information about the experiments
   - **attack_method**: Name of the attack method proposed in the paper
   - **total_prompts**: Total number of prompts/queries used
   - **evaluation_notes**: Any general notes about the evaluation methodology

Please format the output as valid YAML. Extract ALL combinations mentioned in the results/experiments section. If a specific field is not found, use null.

Example output format:
```yaml
experiment_configurations:
  - dataset: AdvBench-50
    victim_model: GPT-4-0613
    judge_model: GPT-4
    asr: 85.2
    notes: "Main baseline result"
  - dataset: AdvBench-50
    victim_model: Claude-3.5-Sonnet
    judge_model: GPT-4
    asr: 78.5
    notes: "Tested on Claude family"
  - dataset: HarmBench
    victim_model: GPT-4-0613
    judge_model: GPT-4
    asr: 90.1
    notes: "HarmBench evaluation"
  - dataset: AdvBench-50
    victim_model: Llama-2-7B-Chat
    judge_model: keyword-matching
    asr: 65.3
    notes: "Open-source model baseline"

paper_metadata:
  attack_method: "GCG (Greedy Coordinate Gradient)"
  total_prompts: 50
  evaluation_notes: "All experiments used temperature=1.0"
```

Now analyze the paper, find all experiment combinations in the results section, and provide the complete experiment setup in YAML format:"""

    # Query Gemini API
    print(f"🤖 Querying Gemini API for experiment setup extraction...")
    try:
        response = client.models.generate_content(
            model="gemini-3.1-pro-preview",
            contents=[uploaded_file, prompt]
        )
        result_text = response.text
        print(f"✅ Received response from Gemini API")
        print()
    except Exception as e:
        print(f"❌ Error querying Gemini API: {e}")
        sys.exit(1)

    # Extract YAML from response (handle markdown code blocks)
    yaml_content = result_text
    if "```yaml" in result_text:
        # Extract from markdown code block
        parts = result_text.split("```yaml")
        if len(parts) > 1:
            yaml_content = parts[1].split("```")[0].strip()
    elif "```" in result_text:
        # Generic code block
        parts = result_text.split("```")
        if len(parts) > 1:
            yaml_content = parts[1].strip()

    # Validate YAML
    print(f"📝 Validating extracted YAML...")
    try:
        experiment_data = yaml.safe_load(yaml_content)
        print(f"✅ YAML validation successful")
        print()
        print("Extracted experiment setup:")
        print("=" * 60)
        print(yaml.dump(experiment_data, default_flow_style=False, sort_keys=False))
        print("=" * 60)
        print()
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML: {e}")
        print()
        print("Raw response:")
        print("-" * 60)
        print(result_text)
        print("-" * 60)
        sys.exit(1)

    # Write to output file
    print(f"💾 Writing to output file: {output_path}")
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(f"# Experiment Setup for Paper: {arxiv_id}\n")
            f.write(f"# Extracted automatically using Gemini API\n\n")
            f.write(yaml_content)
        print(f"✅ Experiment setup saved successfully")
    except Exception as e:
        print(f"❌ Error writing output file: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract experiment setup from research paper PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --arxiv-id 2401.00001 --pdf-path papers/2401.00001.pdf --output output.yaml
  %(prog)s --arxiv-id 2401.00001 --pdf-path attacks_paper_info/2401.00001/2401.00001.pdf \\
           --output attacks_paper_info/2401.00001/experiment_setup.yaml
        """
    )

    parser.add_argument(
        '--arxiv-id',
        type=str,
        required=True,
        help='arXiv ID of the paper'
    )

    parser.add_argument(
        '--pdf-path',
        type=Path,
        required=True,
        help='Path to paper PDF file'
    )

    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Path to output YAML file'
    )

    args = parser.parse_args()

    extract_experiment_setup(
        arxiv_id=args.arxiv_id,
        pdf_path=args.pdf_path,
        output_path=args.output
    )


if __name__ == '__main__':
    main()

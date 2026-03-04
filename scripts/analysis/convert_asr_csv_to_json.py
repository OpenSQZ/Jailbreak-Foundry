import csv
import json

# Read the ASR CSV file
asr_csv_file = '/root/jbfoundry/results/asr_heatmap_assets_harmful_behaviors_custom_50.csv'
cost_csv_file = '/root/jbfoundry/results/cost_heatmap_assets_harmful_behaviors_custom_50.csv'
output_file = '/root/jbfoundry/results/asr.json'

victim_models = []
attack_methods = []
data = []

with open(asr_csv_file, 'r') as f:
    reader = csv.reader(f)
    rows = list(reader)

    # Extract attack methods from the header row (skip first column which is empty)
    header = rows[0]
    for i in range(1, len(header)):
        attack_name = header[i]
        # Extract paper name and date (e.g., "PAIR (2310)")
        # For class_name, we'll convert to lowercase and replace special chars
        class_name = attack_name.split('(')[0].strip().lower().replace(' ', '_').replace('-', '_').replace('+', '_plus')
        attack_methods.append({
            "paper_name": attack_name,
            "class_name": class_name
        })

    # Extract victim models and data from subsequent rows
    for i in range(1, len(rows)):
        if rows[i][0].strip():  # Skip empty rows
            victim_models.append(rows[i][0])
            row_data = []
            for j in range(1, len(rows[i])):
                # Convert ASR values to float
                value = rows[i][j].strip()
                if value:
                    row_data.append(float(value))
                else:
                    row_data.append(0.0)
            data.append(row_data)

# Read the cost CSV file
cost_data = []
with open(cost_csv_file, 'r') as f:
    reader = csv.reader(f)
    rows = list(reader)

    # Skip header row, iterate through data rows
    for i in range(1, len(rows)):
        if rows[i][0].strip():  # Skip empty rows
            model_costs = []
            for j in range(1, len(rows[i])):
                cost_cell = rows[i][j].strip()
                # Parse JSON string
                if cost_cell and cost_cell.startswith('{'):
                    cost_dict = json.loads(cost_cell)
                    model_costs.append({
                        "totals": cost_dict
                    })
                else:
                    model_costs.append({
                        "totals": {
                            "prompt_tokens": 0.0,
                            "completion_tokens": 0.0
                        }
                    })
            cost_data.append(model_costs)

# Create the JSON structure
result = {
    "victim_models": victim_models,
    "attack_methods": attack_methods,
    "data": data,
    "cost": cost_data
}

# Write to JSON file
with open(output_file, 'w') as f:
    json.dump(result, f, indent=2)

print(f"Successfully created {output_file}")
print(f"Models: {len(victim_models)}")
print(f"Attack methods: {len(attack_methods)}")
print(f"ASR data rows: {len(data)}")
print(f"Cost data rows: {len(cost_data)}")

if cost_data and cost_data[0]:
    print(f"\nSample cost entry (first model, first attack):")
    print(f"  {json.dumps(cost_data[0][0], indent=4)}")

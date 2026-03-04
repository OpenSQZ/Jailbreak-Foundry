"""
Local file format loader for JSON, JSONL, and CSV datasets.
"""

import logging

logger = logging.getLogger(__name__)

import os
import json
import pandas as pd
from typing import Union

from .base import JailbreakDatasetLoader, JailbreakDataset



class LocalFileLoader(JailbreakDatasetLoader):
    """Loader for local dataset files in various formats."""
    
    name = "local_file"
    description = "Local file loader for JSON, JSONL, and CSV formats"
    
    def load(self, dataset_name: str, **kwargs) -> JailbreakDataset:
        """
        Load a dataset from a local file.
        
        Args:
            dataset_name: Path to a local JSON, JSONL, or CSV file
            **kwargs: Additional loading parameters
            
        Returns:
            JailbreakDataset object containing the loaded behaviors
        """
        path = dataset_name  # For local loader, dataset_name is the file path
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Dataset file not found: {path}")
        
        if path.endswith(".json"):
            return self._read_json_dataset(path)
        elif path.endswith(".jsonl"):
            return self._read_jsonl_dataset(path)
        elif path.endswith(".csv"):
            return self._read_csv_dataset(path)
        else:
            raise ValueError(f"Unsupported file format for dataset: {path}")

    def _read_json_dataset(self, path: str) -> JailbreakDataset:
        """Read a dataset from a JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        
        # Handle different JSON formats
        if isinstance(data, list):
            # List of behavior dictionaries
            behaviors = [item.get("behavior", "") for item in data]
            goals = [item.get("goal", "") for item in data]
            targets = [item.get("target", "") for item in data]
            categories = [item.get("category", "") for item in data]
        elif isinstance(data, dict):
            # Dictionary with lists
            behaviors = data.get("behaviors", [])
            goals = data.get("goals", [])
            targets = data.get("targets", [])
            categories = data.get("categories", [])
        else:
            raise ValueError(f"Unsupported JSON format in dataset: {path}")
        
        return JailbreakDataset(
            behaviors=behaviors,
            goals=goals,
            targets=targets,
            categories=categories
        )

    def _read_jsonl_dataset(self, path: str) -> JailbreakDataset:
        """Read a dataset from a JSONL file."""
        behaviors = []
        goals = []
        targets = []
        categories = []
        
        # Field mapping for different JSONL formats
        field_mapping = {
            "behavior": ["behavior", "behaviours", "behaviour", "prompt", "prompts", "query", "queries"],
            "goal": ["goal", "goals", "prompt", "prompts", "query", "queries"],
            "target": ["target", "targets", "response", "responses"],
            "category": ["category", "categories", "type", "types"]
        }
        
        with open(path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                    
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                    continue
                
                # Map fields with fallbacks
                behavior = ""
                goal = ""
                target = ""
                category = ""
                
                # Find behavior field
                for field_name in field_mapping["behavior"]:
                    if field_name in data:
                        behavior = data[field_name]
                        break
                
                # Find goal field (fallback to behavior if no separate goal)
                for field_name in field_mapping["goal"]:
                    if field_name in data:
                        goal = data[field_name]
                        break
                if not goal:  # If no goal found, use behavior as goal
                    goal = behavior
                
                # Find target field
                for field_name in field_mapping["target"]:
                    if field_name in data:
                        target = data[field_name]
                        break
                
                # Find category field (fallback to filename or default)
                for field_name in field_mapping["category"]:
                    if field_name in data:
                        category = data[field_name]
                        break
                if not category:  # Default category based on filename
                    filename = os.path.basename(path).split('.')[0]
                    category = filename if filename else "jailbreak"
                
                behaviors.append(behavior)
                goals.append(goal)
                targets.append(target)
                categories.append(category)
        
        return JailbreakDataset(
            behaviors=behaviors,
            goals=goals,
            targets=targets,
            categories=categories
        )

    def _read_csv_dataset(self, path: str) -> JailbreakDataset:
        """Read a dataset from a CSV file."""
        df = pd.read_csv(path)
        
        # Map column names to expected fields (case-insensitive)
        field_mapping = {
            "behavior": ["behavior", "behaviours", "behaviour", "behaviors"],
            "goal": ["goal", "goals", "prompt", "prompts", "query", "queries"],
            "target": ["target", "targets", "response", "responses"],
            "category": ["category", "categories", "type", "types"]
        }

        # Create case-insensitive column name mapping
        col_name_map = {col.lower(): col for col in df.columns}

        result = {}
        for field, possible_cols in field_mapping.items():
            for col in possible_cols:
                if col.lower() in col_name_map:
                    actual_col_name = col_name_map[col.lower()]
                    result[field] = df[actual_col_name].tolist()
                    break
            if field not in result:
                # Use empty strings if column not found
                result[field] = [""] * len(df)
        
        return JailbreakDataset(
            behaviors=result["behavior"],
            goals=result["goal"],
            targets=result["target"],
            categories=result["category"]
        )


def register_local_presets():
    """Register local file presets (empty for now, but allows extension)."""
    return {}
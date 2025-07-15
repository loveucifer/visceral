# visceral/memory/json_memory.py

import json
from pathlib import Path
from typing import Dict, List
from ..core.datamodels import Rule

class JsonMemory:
    """Manages loading and saving rules to a JSON file."""
    def __init__(self, filepath: str = "data/rules.json"):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        if not self.filepath.exists():
            # Create an empty list in the file if it's new
            with open(self.filepath, 'w') as f:
                json.dump([], f)

    def load_rules(self) -> Dict[str, Rule]:
        """Loads rules from the JSON file into a dictionary."""
        try:
            with open(self.filepath, 'r') as f:
                # Handle empty file case
                content = f.read()
                if not content:
                    return {}
                rules_data = json.loads(content)
            return {data['id']: Rule(**data) for data in rules_data}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load rules from {self.filepath}. Starting fresh. Error: {e}")
            return {}

    def save_rules(self, rules: List[Rule]):
        """Saves a list of rules to the JSON file."""
        try:
            # Convert list of Rule objects to list of dictionaries
            rule_dicts = [rule.__dict__ for rule in rules]
            with open(self.filepath, 'w') as f:
                json.dump(rule_dicts, f, indent=4)
        except IOError as e:
            print(f"Error saving rules to {self.filepath}: {e}")

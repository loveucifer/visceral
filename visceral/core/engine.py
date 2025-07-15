# visceral/core/engine.py

from typing import Dict, Optional, List
from ..core.datamodels import Rule
from ..memory.json_memory import JsonMemory

class RuleEngine:
    """
    The symbolic reasoning core. Matches queries to rules and manages the rule set.
    Now with context-aware matching to enable rule chaining.
    """
    def __init__(self, memory: JsonMemory):
        self.memory = memory
        self.rules: Dict[str, Rule] = self.memory.load_rules()

    def match_rule(self, query: str, context: Optional[Dict] = None) -> Optional[Rule]:
        """
        Finds the best matching rule for a given query and conversational context.
        """
        context = context or {}
        query_lower = query.lower().strip()
        matched_rules = []

        for rule in self.rules.values():
            if self._condition_matches(rule.condition, query_lower, context):
                matched_rules.append(rule)

        if not matched_rules:
            return None

        # Sort by confidence and success rate to find the best rule
        # We can add context-specificity to the sorting later if needed
        matched_rules.sort(key=lambda r: r.confidence * r.success_rate, reverse=True)
        return matched_rules[0]

    def _condition_matches(self, condition: str, query: str, context: Dict) -> bool:
        """
        Checks if a rule's condition matches the query and context.
        """
        condition_lower = condition.lower().strip()
        
        context_condition_str = ""
        query_condition = ""

        if ';' in condition_lower:
            parts = condition_lower.split(';', 1)
            context_condition_str = parts[0].strip()
            query_condition = parts[1].strip()
        else:
            query_condition = condition_lower

        # --- Step 1: Check Context Condition ---
        if context_condition_str:
            # BUG FIX: Correctly parse the "context:key:value" format.
            if not context_condition_str.startswith("context:"):
                 return False # Malformed context rule

            # Remove the "context:" prefix to get the actual check
            context_check = context_condition_str[len("context:"):]
            
            if ':' not in context_check:
                return False # Invalid context condition format
            
            key, expected_value = context_check.split(':', 1)
            if context.get(key) != expected_value:
                return False # Context does not match, so this rule is invalid for this turn.
        
        # --- Step 2: Check Query Condition (if context passed or wasn't required) ---
        # If there's no query condition to check (e.g., rule is context-only), it's a match.
        if not query_condition:
            return True

        or_groups = [group.strip() for group in query_condition.split('|')]

        for group in or_groups:
            and_keywords = [keyword.strip() for keyword in group.split('+')]
            if all(keyword in query for keyword in and_keywords):
                return True

        return False

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        return self.rules.get(rule_id)

    def add_rule(self, condition: str, action: str, confidence: float = 0.85) -> Rule:
        """Adds a new rule and saves it."""
        new_rule = Rule(condition=condition, action=action, confidence=confidence)
        self.rules[new_rule.id] = new_rule
        # Note: We don't save here to allow batch additions before saving.
        return new_rule
        
    def consolidate_rules(self, ids_to_remove: List[str], new_condition: str, new_action: str):
        """
        Deletes a list of redundant rules and adds a single,
        consolidated rule in their place.
        """
        print(f"  - Deleting {len(ids_to_remove)} old rules...")
        for rule_id in ids_to_remove:
            if rule_id in self.rules:
                del self.rules[rule_id]
            else:
                print(f"  - WARNING: Rule ID {rule_id} not found for deletion.")
        
        print(f"  - Adding new consolidated rule...")
        self.add_rule(new_condition, new_action, confidence=0.90)
        
        self.save_all_rules()

    def find_rule_by_condition(self, condition_to_find: str) -> Optional[Rule]:
        """
        Checks if a rule with the exact same condition string
        already exists in the knowledge base.
        """
        for rule in self.rules.values():
            if rule.condition == condition_to_find:
                return rule
        return None

    def find_rule_by_action(self, action: str) -> Optional[Rule]:
        """Checks if a rule with the exact same action already exists."""
        for rule in self.rules.values():
            if rule.action == action:
                return rule
        return None

    def save_all_rules(self):
        """Persists all current rules to memory."""
        self.memory.save_rules(list(self.rules.values()))

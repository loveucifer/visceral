# visceral/core/engine.py

from typing import Dict, Optional, List
from ..core.datamodels import Rule
from ..memory.json_memory import JsonMemory

class RuleEngine:
    """
    The symbolic reasoning core. Matches queries to rules and manages the rule set.
    """
    def __init__(self, memory: JsonMemory):
        self.memory = memory
        self.rules: Dict[str, Rule] = self.memory.load_rules()

    def match_rule(self, query: str) -> Optional[Rule]:
        """Finds the best matching rule for a given query."""
        query_lower = query.lower().strip()
        matched_rules = []

        for rule in self.rules.values():
            if self._condition_matches(rule.condition, query_lower):
                matched_rules.append(rule)

        if not matched_rules:
            return None

        matched_rules.sort(key=lambda r: r.confidence * r.success_rate, reverse=True)
        return matched_rules[0]

    def _condition_matches(self, condition: str, query: str) -> bool:
        """Checks if a rule's condition matches the query."""
        condition_lower = condition.lower().strip()
        if '+' in condition_lower:
            return all(keyword.strip() in query for keyword in condition_lower.split('+'))
        else:
            return any(keyword.strip() in query for keyword in condition_lower.split())

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        return self.rules.get(rule_id)

    def add_rule(self, condition: str, action: str, confidence: float = 0.85) -> Rule:
        """Adds a new rule and saves it."""
        new_rule = Rule(condition=condition, action=action, confidence=confidence)
        self.rules[new_rule.id] = new_rule
        self.save_all_rules()
        return new_rule

    def find_rule_by_action(self, action: str) -> Optional[Rule]:
        """Checks if a rule with the exact same action already exists."""
        for rule in self.rules.values():
            if rule.action == action:
                return rule
        return None

    def save_all_rules(self):
        """Persists all current rules to memory."""
        self.memory.save_rules(list(self.rules.values()))

# visceral/core/agent.py

from datetime import datetime
from .datamodels import Decision, ReasoningStep, Rule
from .engine import RuleEngine
from ..llm.ollama_provider import OllamaProvider
from ..memory.json_memory import JsonMemory
import re

class VisceralAgent:
    """
    Orchestrates the rule engine, LLM provider, and memory to make decisions
    and learn from feedback by dynamically creating new rules.
    """
    def __init__(self):
        self.memory = JsonMemory()
        self.rule_engine = RuleEngine(self.memory)
        self.llm_provider = OllamaProvider()
        self.decision_history: list[Decision] = []
        self._ensure_base_rules()

    def _ensure_base_rules(self):
        """Adds a default rule if the rule set is empty."""
        if not self.rule_engine.rules:
            print("INFO: No rules found. Adding a default 'hello' rule.")
            self.rule_engine.add_rule("hello", "Hello! How can I assist you today?", confidence=0.99)

    def process_query(self, query: str) -> Decision:
        """Processes a query using rules or falls back to the LLM."""
        matched_rule = self.rule_engine.match_rules(query)
        
        reasoning_steps = []
        output = ""
        confidence = 0.0
        source = "LLM"

        if matched_rule:
            # --- Symbolic Path ---
            print(f"INFO: Matched rule {matched_rule.id} for query '{query}'.")
            source = "Symbolic Rule"
            output = matched_rule.action
            confidence = matched_rule.confidence * matched_rule.success_rate
            step = ReasoningStep(
                rule_id=matched_rule.id,
                condition_matched=matched_rule.condition,
                action_taken=matched_rule.action,
                confidence=matched_rule.confidence
            )
            reasoning_steps.append(step)
            matched_rule.last_used = datetime.now().isoformat()
        else:
            # --- Neuro Path (LLM Fallback) ---
            print(f"INFO: No rule matched for '{query}'. Falling back to LLM.")
            output = self.llm_provider.query(query)
            confidence = 0.3 # Lower confidence for non-deterministic output

        decision = Decision(
            input_query=query,
            output=output,
            reasoning_steps=reasoning_steps,
            final_confidence=confidence,
            source=source
        )
        self.decision_history.append(decision)
        self.rule_engine.save_all_rules() # Save last_used updates
        return decision

    def provide_feedback(self, decision_id: str, rating: int, feedback_text: str = ""):
        """Processes user feedback to update rule stats or create new rules."""
        decision = next((d for d in self.decision_history if d.id == decision_id), None)
        if not decision:
            print(f"ERROR: Decision {decision_id} not found.")
            return

        decision.feedback_rating = rating
        decision.feedback_text = feedback_text
        
        is_success = rating >= 4 # 4 or 5 stars is a success

        if decision.reasoning_steps:
            # Feedback on an existing rule
            rule_id = decision.reasoning_steps[0].rule_id
            rule = self.rule_engine.get_rule(rule_id)
            if rule:
                if is_success:
                    rule.success_count += 1
                else:
                    rule.failure_count += 1
                print(f"INFO: Updated rule {rule.id} stats. Success: {is_success}")
        
        if not is_success and feedback_text:
            # Learn from failure by creating a new rule
            self._learn_from_feedback(decision.input_query, feedback_text)

        self.rule_engine.save_all_rules()

    def _learn_from_feedback(self, failed_query: str, correct_action: str):
        """Uses the LLM to generate a new, more specific rule from a correction."""
        print(f"INFO: Attempting to learn from feedback. Query: '{failed_query}', Correction: '{correct_action}'")
        
        prompt = f"""
        Analyze the following user interaction and create a precise, symbolic rule.
        The user's query was: "{failed_query}"
        The correct response (action) should have been: "{correct_action}"

        Based on this, determine a good 'condition' for a new rule. The condition should be a few keywords from the user's query that capture the intent. Use '+' to separate keywords that MUST ALL be present (AND logic).

        Respond ONLY with the rule in the format:
        Condition: [your condition keywords]
        Action: [the provided correct action]
        """
        
        try:
            llm_response = self.llm_provider.query(prompt)
            print(f"DEBUG: LLM response for rule generation: {llm_response}")

            # Parse the LLM response
            condition_match = re.search(r"Condition:\s*(.*)", llm_response, re.IGNORECASE)
            action_match = re.search(r"Action:\s*(.*)", llm_response, re.IGNORECASE)

            if condition_match and action_match:
                condition = condition_match.group(1).strip()
                action = action_match.group(1).strip()
                
                if condition and action:
                    new_rule = self.rule_engine.add_rule(condition, action, confidence=0.85)
                    print(f"SUCCESS: Learned and added new rule {new_rule.id} -> Condition: '{condition}', Action: '{action}'")
                else:
                    print("ERROR: LLM provided an empty condition or action.")
            else:
                print(f"ERROR: Could not parse rule from LLM response: '{llm_response}'")

        except Exception as e:
            print(f"ERROR: Failed to generate rule from LLM. {e}")

    def explain_decision(self, decision_id: str) -> str:
        """Generates a human-readable explanation of a decision."""
        decision = next((d for d in self.decision_history if d.id == decision_id), None)
        if not decision:
            return "Decision not found."

        if decision.source == "Symbolic Rule" and decision.reasoning_steps:
            step = decision.reasoning_steps[0]
            rule = self.rule_engine.get_rule(step.rule_id)
            explanation = (
                f"Source: Symbolic Rule (ID: {rule.id})\n"
                f"-----------------------------------------\n"
                f"When I saw a query matching the condition:\n  '{rule.condition}'\n\n"
                f"I was instructed to perform the action:\n  '{rule.action}'\n\n"
                f"Rule Confidence: {rule.confidence:.2f}\n"
                f"Historical Success Rate: {rule.success_rate:.2%}\n"
                f"Final Confidence Score: {decision.final_confidence:.2f}"
            )
            return explanation
        elif decision.source == "LLM":
            return (
                "Source: LLM Fallback\n"
                "--------------------\n"
                "I didn't have a specific rule for your query.\n"
                "So, I used my general knowledge (from the Mistral LLM) to generate a response.\n"
                "My confidence in this answer is lower because it's not based on established logic."
            )
        return "Could not generate an explanation."

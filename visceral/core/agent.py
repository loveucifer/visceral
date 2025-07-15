# visceral/core/agent.py

import re
from datetime import datetime
from .datamodels import Decision, ReasoningStep
from .engine import RuleEngine
from ..llm.ollama_provider import OllamaProvider
from ..memory.json_memory import JsonMemory

class VisceralAgent:
    """
    Orchestrates the rule engine, LLM, and memory to make decisions
    and learn from feedback by dynamically creating and refining rules.
    """
    def __init__(self):
        self.memory = JsonMemory()
        self.rule_engine = RuleEngine(self.memory)
        self.llm_provider = OllamaProvider(host="http://127.0.0.1:11434")
        self.decision_history: list[Decision] = []
        self._ensure_base_rules()

    def _ensure_base_rules(self):
        """Adds default rules if the rule set is empty."""
        if not self.rule_engine.rules:
            print("INFO: No rules found. Adding default rules.")
            self.rule_engine.add_rule("hello hi hey", "Hello! How can I help you today?")
            self.rule_engine.add_rule("recommend+movie", "I can do that. What genre are you in the mood for?")
            self.rule_engine.save_all_rules()

    def process_query(self, query: str) -> Decision:
        """Processes a query using rules or falls back to the LLM."""
        matched_rule = self.rule_engine.match_rule(query)
        
        reasoning_steps = []
        output = ""
        confidence = 0.0
        source = "LLM"

        if matched_rule:
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
            source = "LLM"
            output = self.llm_provider.query(query)
            confidence = 0.3

        decision = Decision(
            input_query=query,
            output=output,
            reasoning_steps=reasoning_steps,
            final_confidence=confidence,
            source=source
        )
        self.decision_history.append(decision)
        self.rule_engine.save_all_rules()
        return decision

    def provide_feedback(self, decision_id: str, rating: int, feedback_text: str = ""):
        """Processes user feedback to update rule stats or create/refine rules."""
        decision = next((d for d in self.decision_history if d.id == decision_id), None)
        if not decision:
            print(f"ERROR: Decision {decision_id} not found.")
            return

        is_success = rating >= 4

        # Logic for when an existing rule was used
        if decision.source == "Symbolic Rule":
            rule_id = decision.reasoning_steps[0].rule_id
            rule = self.rule_engine.get_rule(rule_id)
            if rule:
                if is_success:
                    rule.success_count += 1
                    print(f"INFO: Reinforced rule {rule.id}.")
                else:
                    rule.failure_count += 1
                    print(f"INFO: Marked rule {rule.id} as failed.")
                    # **CORE EVOLUTION STEP**: If a rule fails and user provides a correction, refine the logic.
                    if feedback_text:
                        self._refine_logic_from_feedback(decision, feedback_text)
        
        # Logic for when the LLM was used and it failed
        elif not is_success and feedback_text:
            self._create_new_logic_from_feedback(decision.input_query, feedback_text)

        self.rule_engine.save_all_rules()

    def _create_new_logic_from_feedback(self, failed_query: str, correct_action: str):
        """Uses the LLM to generate a new rule from an LLM fallback failure."""
        print(f"INFO: Learning from LLM failure. Query: '{failed_query}', Correction: '{correct_action}'")
        prompt = f"""
        You are a Rule Generation Bot. A user query was not handled by any existing rule.
        - User's query: "{failed_query}"
        - User's desired response: "{correct_action}"
        Create a 'condition' for a new rule based on the user's query. The condition should be specific keywords. Use '+' for AND logic.
        Respond ONLY with the rule in the format:
        Condition: [your condition keywords]
        """
        self._generate_and_save_rule(prompt, correct_action)

    def _refine_logic_from_feedback(self, failed_decision: Decision, correct_action: str):
        """
        **THE SELF-AUDITING CORE**
        Uses the LLM to create a more specific rule that overrides a general, failed rule.
        """
        failed_query = failed_decision.input_query
        failed_rule = self.rule_engine.get_rule(failed_decision.reasoning_steps[0].rule_id)
        
        print(f"INFO: Refining logic based on failed rule {failed_rule.id}.")
        print(f"   - Failed Condition: '{failed_rule.condition}'")
        print(f"   - User Query: '{failed_query}'")
        print(f"   - Desired Action: '{correct_action}'")

        prompt = f"""
        You are a Rule Refinement Bot. An existing rule failed. Your task is to create a NEW, MORE SPECIFIC rule to handle this exception.
        
        **Analysis of Failure:**
        - The user's query was: "{failed_query}"
        - An existing, general rule with the condition '{failed_rule.condition}' was triggered, but it was wrong in this context.
        - The user specified the correct response should have been: "{correct_action}"

        **Your Goal:**
        Create a NEW condition that is MORE SPECIFIC than the failed one. It should match the user's query but be narrow enough to not conflict with the old rule in other cases.
        - Combine keywords from the original condition AND the user's specific query.
        - Use '+' to connect all keywords (AND logic).
        - The condition must be lowercase.

        **Example:**
        - Failed Condition: "recommend+movie"
        - User Query: "Can you recommend a scary movie?"
        - Good NEW Condition: "recommend+movie+scary"

        Respond ONLY with the new, more specific condition in the format:
        Condition: [your new, more specific condition]
        """
        self._generate_and_save_rule(prompt, correct_action)

    def _generate_and_save_rule(self, prompt: str, action: str):
        """Shared utility to call the LLM, parse the response, and save a rule."""
        try:
            llm_response = self.llm_provider.query(prompt)
            print(f"DEBUG: LLM response for rule generation: '{llm_response}'")
            condition_match = re.search(r"Condition:\s*(.*)", llm_response, re.IGNORECASE)
            
            if condition_match:
                condition = condition_match.group(1).strip().lower()
                # BUG FIX: Remove any leading/trailing quotes from the LLM's output
                condition = condition.strip('\'"')
                
                if condition and action:
                    new_rule = self.rule_engine.add_rule(condition, action)
                    print(f"SUCCESS: Learned and added new rule {new_rule.id} -> Condition: '{condition}'")
                else:
                    print("ERROR: LLM provided an empty condition or action.")
            else:
                print(f"ERROR: Could not parse rule from LLM response: '{llm_response}'")
        except Exception as e:
            print(f"ERROR: Failed to generate rule from LLM. {e}")

    def explain_decision(self, decision_id: str) -> str:
        # This function remains the same as before.
        decision = next((d for d in self.decision_history if d.id == decision_id), None)
        if not decision: return "Decision not found."
        if decision.source == "Symbolic Rule" and decision.reasoning_steps:
            step = decision.reasoning_steps[0]
            rule = self.rule_engine.get_rule(step.rule_id)
            if not rule: return "Error: Could not find the rule used for this decision."
            return (
                f"Source: Symbolic Rule (ID: {rule.id})\n"
                f"-----------------------------------------\n"
                f"When I saw a query matching the condition:\n  '{rule.condition}'\n\n"
                f"I was instructed to perform the action:\n  '{rule.action}'\n\n"
                f"This rule has a base confidence of {rule.confidence:.2f} and a historical success rate of {rule.success_rate:.2%}.\n"
                f"Final Confidence Score: {decision.final_confidence:.2f}"
            )
        elif decision.source == "LLM":
            return (
                "Source: LLM Fallback\n"
                "--------------------\n"
                "I didn't have a specific rule for your query, so I used my general knowledge (from the Llama 3 LLM) to generate a response. My confidence in this answer is lower because it's not based on my established, editable logic."
            )
        return "Could not generate an explanation."

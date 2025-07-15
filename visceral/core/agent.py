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
    and learn from feedback by dynamically creating, refining, and maintaining rules.
    Now with context management for rule chaining.
    """
    def __init__(self):
        self.memory = JsonMemory()
        self.rule_engine = RuleEngine(self.memory)
        self.llm_provider = OllamaProvider(host="http://127.0.0.1:11434")
        self.decision_history: list[Decision] = []
        self.interactions_since_maintenance = 0
        
        # **RULE CHAINING UPGRADE**: Add a context dictionary for the conversation
        self.context = {}
        
        self._ensure_base_rules()

    def _ensure_base_rules(self):
        """
        **UPGRADED**: Checks for the existence of essential default rules and adds them
        if they are missing, without overwriting existing learned rules.
        """
        print("INFO: Verifying essential base rules...")
        base_rules = {
            "hello hi hey": "Hello! How can I help you today?",
            "bored": "set_context:boredom_prompt:true;I can help with that. Are you in the mood for a movie, a book, or a game?",
            "context:boredom_prompt:true;movie": "clear_context:boredom_prompt;Excellent choice. I recommend 'Interstellar'."
        }

        rules_added = False
        for condition, action in base_rules.items():
            # Check if a rule with this specific condition already exists
            if not self.rule_engine.find_rule_by_condition(condition):
                print(f"INFO: Base rule for condition '{condition}' is missing. Adding it now.")
                self.rule_engine.add_rule(condition, action)
                rules_added = True
        
        if rules_added:
            print("INFO: Base rule verification complete. Changes were made.")
            self.rule_engine.save_all_rules()
        else:
            print("INFO: All essential base rules are present.")


    def process_query(self, query: str) -> Decision:
        """Processes a query using context, and periodically runs self-maintenance."""
        self.interactions_since_maintenance += 1
        if self.interactions_since_maintenance >= 5:
            self._maintain_knowledge_base()
            self.interactions_since_maintenance = 0

        # **RULE CHAINING UPGRADE**: Pass the current context to the rule engine.
        matched_rule = self.rule_engine.match_rule(query, self.context)
        
        reasoning_steps = []
        output = ""
        confidence = 0.0
        source = "LLM"

        if matched_rule:
            source = "Symbolic Rule"
            # **RULE CHAINING UPGRADE**: Execute the action, which might modify context.
            output = self._execute_action(matched_rule.action)
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
            # When LLM is used, clear context to avoid unexpected behavior.
            self.context.clear()

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

    def _execute_action(self, action: str) -> str:
        """
        **NEW**: Executes an action string. If the action contains context modifications,
        it performs them and returns the visible response part.
        """
        response_parts = []
        action_parts = [part.strip() for part in action.split(';')]

        for part in action_parts:
            if part.startswith("set_context:"):
                # Format: set_context:key:value
                try:
                    _, key, value = part.split(':', 2)
                    self.context[key] = value
                    print(f"CONTEXT SET: {key} = {value}")
                except ValueError:
                    print(f"ERROR: Invalid set_context format: {part}")
            elif part.startswith("clear_context:"):
                # Format: clear_context:key
                try:
                    _, key = part.split(':', 1)
                    if key in self.context:
                        del self.context[key]
                        print(f"CONTEXT CLEARED: {key}")
                except ValueError:
                     print(f"ERROR: Invalid clear_context format: {part}")
            else:
                # This is a visible response to the user
                response_parts.append(part)
        
        return " ".join(response_parts)

    def _maintain_knowledge_base(self):
        # This function remains the same as before.
        print("\n--- KNOWLEDGE-BASE MAINTENANCE CYCLE INITIATED ---")
        rules = list(self.rule_engine.rules.values())
        if len(rules) < 3:
            print("INFO: Not enough rules for a maintenance cycle. Skipping.")
            return
        rule_summary = "\n".join([f"ID: {r.id}, Condition: '{r.condition}', Action: '{r.action}'" for r in rules])
        prompt = f"Analyze these rules for redundancies. If any have similar actions, propose a consolidation. Respond with 'Redundant IDs: [...]', 'Consolidated Condition: ...', and 'Consolidated Action: ...' or 'No redundancies found.'\n\nRULES:\n{rule_summary}"
        try:
            response = self.llm_provider.query(prompt)
            print(f"DEBUG: Maintenance check response: '{response}'")
            if "No redundancies found" in response: return
            redundant_ids_match = re.search(r"Redundant IDs:\s*\[(.*?)\]", response)
            condition_match = re.search(r"Consolidated Condition:\s*(.*)", response)
            action_match = re.search(r"Consolidated Action:\s*(.*)", response)
            if redundant_ids_match and condition_match and action_match:
                ids_str = redundant_ids_match.group(1).replace("'", "").replace('"', '')
                ids_to_remove = [id.strip() for id in ids_str.split(',')]
                new_condition = condition_match.group(1).strip().strip('\'"')
                new_action = action_match.group(1).strip().strip('\'"')
                print("\n--- EXECUTING KNOWLEDGE CONSOLIDATION ---")
                self.rule_engine.consolidate_rules(ids_to_remove, new_condition, new_action)
                print("--- KNOWLEDGE CONSOLIDATION COMPLETE ---")
        except Exception as e:
            print(f"ERROR: Knowledge-base maintenance failed. {e}")

    def provide_feedback(self, decision_id: str, rating: int, feedback_text: str = ""):
        # This function remains the same as before.
        decision = next((d for d in self.decision_history if d.id == decision_id), None)
        if not decision: return
        is_success = rating >= 4
        if decision.source == "Symbolic Rule":
            rule = self.rule_engine.get_rule(decision.reasoning_steps[0].rule_id)
            if rule:
                if is_success: rule.success_count += 1
                else: rule.failure_count += 1
                if not is_success and feedback_text:
                    self._refine_logic_from_feedback(decision, feedback_text)
        elif not is_success and feedback_text:
            self._create_new_logic_from_feedback(decision.input_query, feedback_text)
        self.rule_engine.save_all_rules()

    def _create_new_logic_from_feedback(self, failed_query: str, correct_action: str):
        # This function remains the same as before.
        prompt = f"Create a specific rule condition from this query: '{failed_query}'. The action will be: '{correct_action}'. Respond with 'Condition: [your condition]'."
        self._generate_and_save_rule(prompt, correct_action)

    def _refine_logic_from_feedback(self, failed_decision: Decision, correct_action: str):
        # This function remains the same as before.
        failed_rule = self.rule_engine.get_rule(failed_decision.reasoning_steps[0].rule_id)
        prompt = f"An old rule with condition '{failed_rule.condition}' failed on query '{failed_decision.input_query}'. Create a new, more specific condition. The action will be '{correct_action}'. Respond with 'Condition: [your new condition]'."
        self._generate_and_save_rule(prompt, correct_action)

    def _is_rule_ethical(self, condition: str, action: str) -> bool:
        # This function remains the same as before.
        prompt = f"Is the rule 'if {condition} then {action}' harmful, unethical, or dangerous? Answer ONLY Yes or No."
        response = self.llm_provider.query(prompt)
        return "no" in response.lower()

    def _generate_and_save_rule(self, prompt: str, action: str):
        # This function remains the same as before.
        llm_response = self.llm_provider.query(prompt)
        condition_match = re.search(r"Condition:\s*(.*)", ll.response, re.IGNORECASE)
        if condition_match:
            condition = condition_match.group(1).strip().lower().strip('\'"')
            if condition and action and self._is_rule_ethical(condition, action):
                self.rule_engine.add_rule(condition, action)
                print(f"SUCCESS: Learned and added new rule -> Condition: '{condition}'")
            else:
                print("ERROR: Ethical check failed or condition/action was empty. Rule not saved.")
        else:
            print(f"ERROR: Could not parse rule from LLM response: '{llm_response}'")

    def explain_decision(self, decision_id: str) -> str:
        # This function remains the same as before.
        decision = next((d for d in self.decision_history if d.id == decision_id), None)
        if not decision: return "Decision not found."
        if decision.source == "Symbolic Rule":
            rule = self.rule_engine.get_rule(decision.reasoning_steps[0].rule_id)
            if not rule: return "Error: Could not find the rule used for this decision."
            return (f"Source: Symbolic Rule (ID: {rule.id})\n"
                    f"-----------------------------------------\n"
                    f"Condition: '{rule.condition}' -> Action: '{rule.action}'\n"
                    f"Confidence: {rule.confidence:.2f}, Success Rate: {rule.success_rate:.2%}")
        return ("Source: LLM Fallback\n--------------------\n"
                "I didn't have a specific rule, so I used my general knowledge to generate a response.")

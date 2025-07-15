import json
import re
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class Rule:
    """Represents a logical rule in the system"""
    id: str
    condition: str
    action: str
    confidence: float
    created_at: str
    last_used: str
    success_count: int = 0
    failure_count: int = 0
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.5

@dataclass
class ReasoningStep:
    """Represents a step in the reasoning process"""
    rule_id: str
    condition_matched: str
    action_taken: str
    confidence: float
    timestamp: str

@dataclass
class Decision:
    """Represents a complete decision with reasoning chain"""
    id: str
    input_query: str
    output: str
    reasoning_steps: List[ReasoningStep]
    final_confidence: float
    timestamp: str
    feedback: Optional[str] = None
    feedback_rating: Optional[int] = None  # 1-5 scale

class RuleEngine:
    """Core rule engine that manages symbolic rules"""
    
    def __init__(self, rules_file: str = "rules.json"):
        self.rules_file = Path(rules_file)
        self.rules: Dict[str, Rule] = {}
        self.load_rules()
    
    def load_rules(self):
        """Load rules from persistent storage"""
        if self.rules_file.exists():
            try:
                with open(self.rules_file, 'r') as f:
                    data = json.load(f)
                    for rule_data in data:
                        rule = Rule(**rule_data)
                        self.rules[rule.id] = rule
            except Exception as e:
                print(f"Error loading rules: {e}")
    
    def save_rules(self):
        """Save rules to persistent storage"""
        try:
            with open(self.rules_file, 'w') as f:
                json.dump([asdict(rule) for rule in self.rules.values()], f, indent=2)
        except Exception as e:
            print(f"Error saving rules: {e}")
    
    def add_rule(self, condition: str, action: str, confidence: float = 0.5, context: Dict = None):
        """Add a new rule to the system"""
        rule_id = str(uuid.uuid4())
        rule = Rule(
            id=rule_id,
            condition=condition,
            action=action,
            confidence=confidence,
            created_at=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            context=context or {}
        )
        self.rules[rule_id] = rule
        self.save_rules()
        return rule_id
    
    def match_rules(self, query: str, context: Dict = None) -> List[Rule]:
        """Find rules that match the given query"""
        matched_rules = []
        context = context or {}
        
        for rule in self.rules.values():
            # Simple keyword matching (can be enhanced with more sophisticated matching)
            if self._condition_matches(rule.condition, query, context):
                matched_rules.append(rule)
        
        # Sort by confidence and success rate
        matched_rules.sort(key=lambda r: (r.confidence * r.success_rate), reverse=True)
        return matched_rules
    
    def _condition_matches(self, condition: str, query: str, context: Dict) -> bool:
        """Check if a condition matches the query and context"""
        # Simple keyword matching - can be enhanced with regex, NLP, etc.
        condition_lower = condition.lower()
        query_lower = query.lower()
        
        # Check for keyword matches
        if any(keyword in query_lower for keyword in condition_lower.split()):
            return True
        
        # Check context matches
        for key, value in context.items():
            if f"{key}:{value}" in condition_lower:
                return True
        
        return False
    
    def update_rule_feedback(self, rule_id: str, success: bool):
        """Update rule statistics based on feedback"""
        if rule_id in self.rules:
            rule = self.rules[rule_id]
            if success:
                rule.success_count += 1
            else:
                rule.failure_count += 1
            rule.last_used = datetime.now().isoformat()
            self.save_rules()
    
    def create_rule_from_feedback(self, failed_query: str, correct_response: str, context: Dict = None):
        """Create a new rule based on negative feedback"""
        # Extract key features from the failed query
        condition = self._extract_condition_from_query(failed_query)
        action = f"respond_with: {correct_response}"
        
        return self.add_rule(condition, action, confidence=0.8, context=context)
    
    def _extract_condition_from_query(self, query: str) -> str:
        """Extract condition keywords from a query"""
        # Simple extraction - can be enhanced with NLP
        keywords = re.findall(r'\b\w+\b', query.lower())
        # Remove common words
        stop_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by'}
        keywords = [w for w in keywords if w not in stop_words and len(w) > 2]
        return ' '.join(keywords[:5])  # Take first 5 meaningful keywords

class SelfUpdatingAI:
    """Main AI agent that combines LLM with rule-based reasoning"""
    
    def __init__(self, model_name: str = "mistral"):
        self.rule_engine = RuleEngine()
        self.decision_history: List[Decision] = []
        self.model_name = model_name
        self.context = {}
        
        # Initialize with some basic rules
        self._initialize_basic_rules()
    
    def _initialize_basic_rules(self):
        """Initialize with some basic rules"""
        if not self.rule_engine.rules:
            self.rule_engine.add_rule(
                "greeting hello hi", 
                "respond_with: Hello! How can I help you today?",
                confidence=0.9
            )
            self.rule_engine.add_rule(
                "movie recommendation", 
                "ask_for_genre_preference",
                confidence=0.7
            )
            self.rule_engine.add_rule(
                "sci-fi science fiction", 
                "recommend: Interstellar, Blade Runner 2049, Arrival",
                confidence=0.8
            )
    
    def process_query(self, query: str, context: Dict = None) -> Decision:
        """Process a query using rule-based reasoning"""
        context = context or {}
        self.context.update(context)
        
        # Find matching rules
        matched_rules = self.rule_engine.match_rules(query, self.context)
        
        reasoning_steps = []
        output = ""
        final_confidence = 0.0
        
        if matched_rules:
            # Use the best matching rule
            best_rule = matched_rules[0]
            
            reasoning_step = ReasoningStep(
                rule_id=best_rule.id,
                condition_matched=best_rule.condition,
                action_taken=best_rule.action,
                confidence=best_rule.confidence,
                timestamp=datetime.now().isoformat()
            )
            reasoning_steps.append(reasoning_step)
            
            # Execute the rule action
            output = self._execute_rule_action(best_rule.action, query)
            final_confidence = best_rule.confidence * best_rule.success_rate
            
        else:
            # No matching rules - use LLM fallback
            output = self._llm_fallback(query)
            final_confidence = 0.3  # Lower confidence for fallback
        
        # Create decision record
        decision = Decision(
            id=str(uuid.uuid4()),
            input_query=query,
            output=output,
            reasoning_steps=reasoning_steps,
            final_confidence=final_confidence,
            timestamp=datetime.now().isoformat()
        )
        
        self.decision_history.append(decision)
        return decision
    
    def _execute_rule_action(self, action: str, query: str) -> str:
        """Execute a rule action"""
        if action.startswith("respond_with:"):
            return action.replace("respond_with:", "").strip()
        elif action.startswith("recommend:"):
            recommendations = action.replace("recommend:", "").strip()
            return f"I recommend: {recommendations}"
        elif action == "ask_for_genre_preference":
            return "What genre do you prefer? (sci-fi, horror, comedy, drama, etc.)"
        else:
            return f"Executing action: {action}"
    
    def _llm_fallback(self, query: str) -> str:
        """Fallback to LLM when no rules match"""
        # Placeholder for actual LLM integration
        # In a real implementation, you'd call your LLM here
        return f"I don't have a specific rule for '{query}', but I'll try to help based on general knowledge."
    
    def provide_feedback(self, decision_id: str, rating: int, feedback: str = None):
        """Provide feedback on a decision to improve the system"""
        # Find the decision
        decision = None
        for d in self.decision_history:
            if d.id == decision_id:
                decision = d
                break
        
        if not decision:
            print(f"Decision {decision_id} not found")
            return
        
        # Update decision with feedback
        decision.feedback = feedback
        decision.feedback_rating = rating
        
        # Update rule statistics
        success = rating >= 3  # Consider 3+ as success
        
        for step in decision.reasoning_steps:
            self.rule_engine.update_rule_feedback(step.rule_id, success)
        
        # If feedback is negative and includes correction, create new rule
        if rating < 3 and feedback:
            self.rule_engine.create_rule_from_feedback(
                decision.input_query, 
                feedback, 
                self.context
            )
        
        print(f"Feedback processed. System updated based on rating: {rating}")
    
    def explain_decision(self, decision_id: str) -> str:
        """Explain why a decision was made"""
        decision = None
        for d in self.decision_history:
            if d.id == decision_id:
                decision = d
                break
        
        if not decision:
            return "Decision not found"
        
        explanation = f"For query: '{decision.input_query}'\n\n"
        explanation += "Reasoning steps:\n"
        
        for i, step in enumerate(decision.reasoning_steps, 1):
            rule = self.rule_engine.rules.get(step.rule_id)
            if rule:
                explanation += f"{i}. Matched rule: '{rule.condition}'\n"
                explanation += f"   Action taken: {step.action_taken}\n"
                explanation += f"   Confidence: {step.confidence:.2f}\n"
                explanation += f"   Rule success rate: {rule.success_rate:.2f}\n\n"
        
        explanation += f"Final confidence: {decision.final_confidence:.2f}"
        return explanation
    
    def get_rule_statistics(self) -> Dict:
        """Get statistics about the rule system"""
        total_rules = len(self.rule_engine.rules)
        total_decisions = len(self.decision_history)
        
        successful_rules = sum(1 for rule in self.rule_engine.rules.values() if rule.success_rate > 0.5)
        
        return {
            "total_rules": total_rules,
            "successful_rules": successful_rules,
            "total_decisions": total_decisions,
            "rule_success_rate": successful_rules / total_rules if total_rules > 0 else 0
        }

# Example usage
if __name__ == "__main__":
    # Initialize the AI agent
    ai = SelfUpdatingAI()
    
    print("=== Self-Updating AI Agent Demo ===\n")
    
    # Example interaction 1
    print("1. Testing movie recommendation...")
    decision1 = ai.process_query("I want a movie recommendation")
    print(f"AI: {decision1.output}")
    print(f"Decision ID: {decision1.id}\n")
    
    # Example interaction 2
    print("2. Testing sci-fi preference...")
    decision2 = ai.process_query("I love sci-fi movies", {"genre": "sci-fi"})
    print(f"AI: {decision2.output}")
    print(f"Decision ID: {decision2.id}\n")
    
    # Provide negative feedback
    print("3. Providing negative feedback...")
    ai.provide_feedback(decision2.id, 1, "I don't like Interstellar, recommend something else")
    print("Feedback provided!\n")
    
    # Test the same query again to see adaptation
    print("4. Testing sci-fi preference again after feedback...")
    decision3 = ai.process_query("I love sci-fi movies", {"genre": "sci-fi"})
    print(f"AI: {decision3.output}")
    print(f"Decision ID: {decision3.id}\n")
    
    # Explain a decision
    print("5. Explaining decision...")
    explanation = ai.explain_decision(decision2.id)
    print(f"Explanation:\n{explanation}\n")
    
    # Show statistics
    print("6. System statistics:")
    stats = ai.get_rule_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
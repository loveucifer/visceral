# visceral/core/datamodels.py

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Rule:
    """Represents a single symbolic rule in the agent's logic tree."""
    condition: str
    action: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    confidence: float = 0.5
    success_count: int = 0
    failure_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def success_rate(self) -> float:
        """Calculates the historical success rate of the rule."""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.5

@dataclass
class ReasoningStep:
    """Logs a single step in the agent's reasoning process for a decision."""
    rule_id: str
    condition_matched: str
    action_taken: str
    confidence: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class Decision:
    """Represents a complete decision made by the agent, including the reasoning."""
    input_query: str
    output: str
    reasoning_steps: List[ReasoningStep]
    final_confidence: float
    source: str # 'Symbolic Rule' or 'LLM'
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    feedback_rating: Optional[int] = None # e.g., 1-5 stars
    feedback_text: Optional[str] = None

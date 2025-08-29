from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class RuleType(str, Enum):
    COMPANY = "company"
    MEASUREMENT = "measurement" 
    MATERIAL = "material"
    FORMATTING = "formatting"

class RuleDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"

class RuleSuggestionResponse(BaseModel):
    id: str
    rule_type: str
    pattern: str
    replacement: str
    confidence: float
    reasoning: str
    examples: List[str]
    priority: int
    timestamp: datetime
    suggested_rule: Optional[Dict[str, str]] = None

class RuleDecisionRequest(BaseModel):
    decision: RuleDecision
    reasoning: str
    modifications: Dict[str, Any] = {}

class RuleResponse(BaseModel):
    id: str
    rule_type: str
    pattern: str
    replacement: str
    confidence: float
    active: bool
    created_at: datetime
    created_by: str
    performance_score: Optional[float] = None

class RuleRequest(BaseModel):
    rule_type: str
    pattern: str
    replacement: str
    description: Optional[str] = None
    priority: int = 5

class RulePerformanceResponse(BaseModel):
    rule_id: str
    applications_count: int
    success_rate: float
    average_confidence: float
    improvement_impact: float
    trend: str
    last_30_days: List[Dict[str, Any]]
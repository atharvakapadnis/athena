from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class AnalysisRequest(BaseModel):
    batch_id: str
    analysis_types: List[str]

class AnalysisResponse(BaseModel):
    analysis_id: str
    batch_id: str
    analysis_types: List[str]
    results: Dict[str, Any]
    confidence_score: float
    started_at: datetime
    completed_at: datetime
    status: str
    error_message: Optional[str] = None

class PatternAnalysisResponse(BaseModel):
    pattern_id: str
    pattern_type: str
    pattern: str
    frequency: int
    confidence: float
    examples: List[str]
    suggested_rule: Optional[Dict[str, str]] = None
    impact_assessment: str
    discovered_at: str

class FeedbackRequest(BaseModel):
    product_id: str
    original_description: str
    generated_description: str
    feedback_text: str
    rating: int
    feedback_type: str
    suggestions: Optional[str] = None

class FeedbackResponse(BaseModel):
    feedback_id: str
    status: str
    processing_result: Any
    message: str

class ConfidenceAnalysisResponse(BaseModel):
    analysis_id: str
    batch_id: Optional[str]
    time_period_days: int
    overall_confidence: float
    confidence_distribution: Dict[str, float]
    confidence_trends: List[Any]
    low_confidence_patterns: List[Any]
    improvement_suggestions: List[str]
    generated_at: datetime
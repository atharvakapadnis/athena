from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

class DashboardSummary(BaseModel):
    system_overview: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    system_health: str
    last_updated: datetime

class ExecutiveSummary(BaseModel):
    key_performance_indicators: Dict[str, Any]
    quality_trend: Dict[str, Any]
    operational_status: Dict[str, Any]
    critical_actions: List[str]
    performance_highlights: Dict[str, Any]
    next_review_date: Optional[str]
    last_updated: datetime

class RealTimeMetrics(BaseModel):
    current_batch_status: Dict[str, Any]
    processing_rate: Dict[str, Any]
    confidence_distribution: Dict[str, Any]
    system_health: str
    active_alerts: int
    timestamp: datetime

class PerformanceMetrics(BaseModel):
    processing_speed: float
    throughput: float
    error_rate: float
    efficiency_score: float

class QualityMetrics(BaseModel):
    high_confidence_rate: float
    medium_confidence_rate: float
    low_confidence_rate: float
    improvement_trend: str
    quality_score: float

class SystemHealth(BaseModel):
    overall_status: str
    components: Dict[str, str]
    last_check: datetime
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

class SystemHealth(BaseModel):
    overall_status: str
    components: Dict[str, str]
    last_check: datetime
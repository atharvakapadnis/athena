from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

class SystemHealthResponse(BaseModel):
    overall_status: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    uptime_seconds: int
    process_memory_mb: float
    directories_status: Dict[str, Any]
    services_status: Dict[str, str]
    health_issues: List[str]
    last_check: datetime

class SystemStatsResponse(BaseModel):
    system_info: Dict[str, Any]
    network_stats: Dict[str, int]
    data_stats: Dict[str, Any]
    recent_activity: Dict[str, Any]
    generated_at: datetime

class ConfigurationRequest(BaseModel):
    configuration: Dict[str, Any]

class ConfigurationResponse(BaseModel):
    configuration: Dict[str, Any]
    last_updated: datetime
    updated_by: str

# class UserRequest(BaseModel):
#     username: str
#     email: str
#     role: str

# class UserResponse(BaseModel):
#     username: str
#     email: str
#     role: str
#     active: bool
#     created_at: datetime
#     last_login: Optional[datetime] = None

# class MaintenanceRequest(BaseModel):
#     task_type: str
#     parameters: Optional[Dict[str, Any]] = None
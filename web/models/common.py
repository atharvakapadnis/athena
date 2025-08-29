from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Generic, TypeVar
from datetime import datetime
from enum import Enum

T = TypeVar("T")

class ResponseStatus(str, Enum):
    """ Standard response status codes """
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PENDING = "pending"

class APIResponse(BaseModel, Generic[T]):
    """ Standard API response format """
    status: ResponseStatus
    message: Optional[str] = None
    data: Optional[T] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory = datetime.utcnow)
    request_id: Optional[str] = None

class PaginatedResponse(BaseModel, Generic[T]):
    """ Paginated response format """
    items: List[T]
    total: int
    page: int = 1
    page_size: int = 50
    total_pages: int
    has_next: bool
    has_prev: bool

class HealthCheckResponse(BaseModel):
    """ Health check response format """
    status: str
    version: str
    timestamp: datetime
    uptime_seconds: float
    components: Dict[str, str] # component_name: status
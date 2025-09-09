from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class BatchStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BatchConfigRequest(BaseModel):
    batch_size: int = 50
    start_index: int = 0
    confidence_threshold_high: float = 0.8
    confidence_threshold_medium: float = 0.6
    max_processing_time: int = 300
    retry_failed_items: bool = True
    notification_webhook: Optional[str] = None
    priority: str = "normal"

class BatchResponse(BaseModel):
    batch_id: str
    status: BatchStatus
    batch_size: int
    items_processed: int
    total_items: int
    progress_percentage: float
    success_rate: float
    average_confidence: float
    processing_duration: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    created_by: str
    error_message: Optional[str] = None

class BatchHistoryResponse(BaseModel):
    batch_id: str
    status: BatchStatus
    batch_size: int
    items_processed: int
    total_items: int
    success_rate: float
    average_confidence: float
    created_at: datetime
    completed_at: Optional[datetime] = None
    processing_duration: Optional[float] = None
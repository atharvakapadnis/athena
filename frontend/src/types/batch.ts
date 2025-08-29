export enum BatchStatus {
    PENDING = "pending",
    RUNNING = "running", 
    PAUSED = "paused",
    COMPLETED = "completed",
    FAILED = "failed",
    CANCELLED = "cancelled"
  }
  
  export interface BatchConfigRequest {
    batch_size: number;
    start_index: number;
    confidence_threshold_high: number;
    confidence_threshold_medium: number;
    max_processing_time: number;
    retry_failed_items: boolean;
    notification_webhook: string;
    priority: string;
  }
  
  export interface BatchResponse {
    batch_id: string;
    status: BatchStatus;
    batch_size: number;
    items_processed: number;
    total_items: number;
    progress_percentage: number;
    success_rate: number;
    average_confidence: number;
    processing_duration?: number;
    created_at: string;
    completed_at?: string;
    created_by: string;
    error_message?: string;
  }
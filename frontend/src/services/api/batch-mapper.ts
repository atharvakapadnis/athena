import type { Batch, PaginatedResponse } from '@/types';

// Backend response format (what the API actually returns)
interface BackendBatch {
  batch_id: string;
  status: string;
  batch_size: number;
  items_processed: number;
  total_items: number;
  success_rate: number;
  average_confidence: number;
  created_at: string;
  completed_at?: string | null;
  processing_duration?: number | null;
}

interface BackendBatchHistory {
  items: BackendBatch[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

// Map backend batch to frontend format
export function mapBackendBatch(backendBatch: BackendBatch): Batch {
  return {
    id: backendBatch.batch_id,
    status: backendBatch.status as any,
    config: {
      batch_size: backendBatch.batch_size,
      start_index: 0, // Not provided by backend
      confidence_threshold_high: 0.8, // Default values
      confidence_threshold_medium: 0.6,
      max_processing_time: 300,
      retry_failed_items: true,
      priority: 'normal',
    },
    created_at: backendBatch.created_at,
    started_at: backendBatch.created_at, // Assume started when created
    completed_at: backendBatch.completed_at || undefined,
    progress: backendBatch.items_processed && backendBatch.total_items 
      ? (backendBatch.items_processed / backendBatch.total_items) * 100 
      : 0,
    total_items: backendBatch.total_items,
    processed_items: backendBatch.items_processed,
    success_count: Math.round(backendBatch.items_processed * backendBatch.success_rate),
    error_count: backendBatch.items_processed - Math.round(backendBatch.items_processed * backendBatch.success_rate),
    created_by: 'Unknown', // Not provided by backend
  };
}

// Map backend history response to frontend format
export function mapBackendBatchHistory(backendHistory: BackendBatchHistory): PaginatedResponse<Batch> {
  return {
    items: backendHistory.items.map(mapBackendBatch),
    total: backendHistory.total,
    page: backendHistory.page,
    per_page: backendHistory.page_size,
    total_pages: backendHistory.total_pages,
  };
}
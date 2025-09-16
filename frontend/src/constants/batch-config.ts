import type { BatchConfig } from '@/types';

export const DEFAULT_BATCH_CONFIG: BatchConfig = {
    batch_size: 50,
    start_index: 0,
    confidence_threshold_high: 0.8,
    confidence_threshold_medium: 0.6,
    max_processing_time: 300,
    retry_failed_items: true,
    notification_webhook: '',
    priority: 'normal',
};

export const PRIORITY_OPTIONS = [
    { value: 'low', label: 'Low Priority' },
    { value: 'normal', label: 'Normal Priority' },
    { value: 'high', label: 'High Priority' },
] as const;

export const BATCH_STATUS_COLORS = {
    pending: 'warning',
    running: 'info',
    completed: 'success',
    failed: 'error',
    paused: 'secondary',
    cancelled: 'default',
} as const;

export const CONFIDENCE_LEVEL_COLORS = {
    High: 'success',
    Medium: 'warning',
    Low: 'error',
} as const;
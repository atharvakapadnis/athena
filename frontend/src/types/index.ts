// User and Authentication Types
export interface User {
  username: string;
  email: string;
  role: string;
  active: boolean;
  created_at: string;
  last_login: string | null;
}

export interface UserLogin {
  username: string;
  password: string;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  role?: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

// API Response wrapper
export interface APIResponse<T = any> {
  status: 'success' | 'error';
  data?: T;
  message: string;
}

// Dashboard Types - Updated to match backend
export interface DashboardSummary {
  system_overview: SystemOverview;
  performance_metrics: PerformanceMetrics;
  quality_metrics: QualityMetrics;
  recent_activity: ActivityItem[];
  recommendations: string[];
  system_health: string;
  last_updated: string;
}

export interface SystemOverview {
  total_batches: number;
  total_items: number;
  success_rate: number;
  average_confidence: number;
  uptime_hours: number;
}

export interface PerformanceMetrics {
  processing_speed: number;
  throughput: number;
  error_rate: number;
  efficiency_score: number;
}

export interface QualityMetrics {
  high_confidence_rate: number;
  medium_confidence_rate: number;
  low_confidence_rate: number;
  quality_trend: string;
}

export interface ActivityItem {
  id: string;
  type: 'batch' | 'rule' | 'system';
  action: string;
  timestamp: string;
  user: string;
  details?: string;
}

export interface SystemHealth {
  status: 'healthy' | 'warning' | 'error';
  services: Record<string, 'up' | 'down' | 'degraded'>;
  last_check: string;
}

// Updated Batch Types
export interface BatchConfig {
  batch_size: number;
  start_index: number;
  confidence_threshold_high: number;
  confidence_threshold_medium: number;
  max_processing_time: number;
  retry_failed_items: boolean;
  notification_webhook?: string;
  priority: 'low' | 'normal' | 'high';
}

export interface Batch {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused' | 'cancelled';
  config: BatchConfig;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  progress: number;
  total_items: number;
  processed_items: number;
  success_count: number;
  error_count: number;
  created_by: string;
  estimated_completion?: string;
}

export interface BatchResult {
  id: string;
  batch_id: string;
  item_id: string;
  original_description: string;
  generated_description: string;
  confidence_score: number;
  confidence_level: 'High' | 'Medium' | 'Low';
  status: 'success' | 'failed';
  error_message?: string;
  processing_time: number;
  timestamp: string;
}

// Batch filtering and search
export interface BatchResultFilters {
  success?: boolean;
  confidence_level?: 'High' | 'Medium' | 'Low';
  search?: string;
}

export interface BatchResultSort {
  field: 'timestamp' | 'confidence_score' | 'processing_time';
  direction: 'asc' | 'desc';
}

// Rule Types
export interface Rule {
  id: string;
  name: string;
  description: string;
  rule_type: 'confidence' | 'content' | 'format';
  condition: RuleCondition;
  action: RuleAction;
  active: boolean;
  created_at: string;
  created_by: string;
  last_modified: string;
  effectiveness_score?: number;
  applications_count: number;
}

export interface RuleCondition {
  field: string;
  operator: 'equals' | 'contains' | 'greater_than' | 'less_than' | 'regex';
  value: string | number;
}

export interface RuleAction {
  type: 'modify' | 'reject' | 'flag' | 'boost_confidence';
  parameters: Record<string, any>;
}

export interface RuleCreate {
  name: string;
  description: string;
  rule_type: 'confidence' | 'content' | 'format';
  condition: RuleCondition;
  action: RuleAction;
}

// AI Analysis Types
export interface PatternAnalysis {
  id: string;
  pattern_type: 'common_failures' | 'confidence_trends' | 'content_patterns';
  description: string;
  frequency: number;
  confidence: number;
  examples: string[];
  suggested_rules: SuggestedRule[];
  discovered_at: string;
}

export interface SuggestedRule {
  name: string;
  description: string;
  estimated_impact: number;
  rule_definition: RuleCreate;
}

export interface FeedbackSubmission {
  item_id: string;
  feedback_type: 'quality' | 'accuracy' | 'preference';
  rating: number;
  comments?: string;
}

export interface ConfidenceAnalysis {
  avg_confidence: number;
  confidence_distribution: Record<string, number>;
  trends: ConfidenceTrend[];
  recommendations: string[];
}

export interface ConfidenceTrend {
  date: string;
  avg_confidence: number;
  volume: number;
}

// System Types
export interface SystemStats {
  uptime: number;
  total_requests: number;
  avg_response_time: number;
  memory_usage: number;
  cpu_usage: number;
  disk_usage: number;
  active_connections: number;
}

export interface SystemLog {
  level: 'info' | 'warning' | 'error';
  message: string;
  timestamp: string;
  module: string;
  details?: Record<string, any>;
}

// Common utility types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ApiError {
  message: string;
  status: number;
  details?: Record<string, any>;
}
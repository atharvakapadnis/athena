export interface AnalysisRequest {
    batch_id: string;
    analysis_types: string[];
  }
  
  export interface AnalysisResponse {
    analysis_id: string;
    batch_id: string;
    analysis_types: string[];
    results: Record<string, any>;
    confidence_score: number;
    started_at: string;
    completed_at: string;
    status: string;
    error_message?: string;
  }
  
  export interface PatternAnalysisResponse {
    pattern_id: string;
    pattern_type: string;
    pattern: string;
    frequency: number;
    confidence: number;
    examples: string[];
    suggested_rule?: {
      rule_type: string;
      pattern: string;
      replacement: string;
    };
    impact_assessment: string;
    discovered_at: string;
  }
  
  export interface FeedbackRequest {
    product_id: string;
    original_description: string;
    generated_description: string;
    feedback_text: string;
    rating: number;
    feedback_type: string;
    suggestions?: string;
  }
  
  export interface FeedbackResponse {
    feedback_id: string;
    status: string;
    processing_result: any;
    message: string;
  }
  
  export interface ConfidenceAnalysisResponse {
    analysis_id: string;
    batch_id?: string;
    time_period_days: number;
    overall_confidence: number;
    confidence_distribution: Record<string, number>;
    confidence_trends: any[];
    low_confidence_patterns: any[];
    improvement_suggestions: string[];
    generated_at: string;
  }
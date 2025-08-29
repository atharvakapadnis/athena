export interface RuleSuggestionResponse {
    id: string;
    rule_type: string;
    pattern: string;
    replacement: string;
    confidence: number;
    reasoning: string;
    examples: string[];
    priority: number;
    timestamp: string;
    suggested_rule?: {
      rule_type: string;
      pattern: string;
      replacement: string;
    };
  }
  
  export interface RuleDecisionRequest {
    decision: 'approve' | 'reject' | 'modify';
    reasoning: string;
    modifications: Record<string, any>;
  }
  
  export interface RuleResponse {
    id: string;
    rule_type: string;
    pattern: string;
    replacement: string;
    confidence: number;
    active: boolean;
    created_at: string;
    created_by: string;
    performance_score?: number;
  }
  
  export interface RulePerformanceResponse {
    rule_id: string;
    applications_count: number;
    success_rate: number;
    average_confidence: number;
    improvement_impact: number;
    trend: string;
    last_30_days: any[];
  }
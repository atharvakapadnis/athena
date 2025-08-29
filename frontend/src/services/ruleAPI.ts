import { apiClient } from './api';

export const ruleAPI = {
  getPendingSuggestions: (priorityThreshold?: number, confidenceThreshold?: number) =>
    apiClient.get('/rules/suggestions', {
      params: { 
        priority_threshold: priorityThreshold, 
        confidence_threshold: confidenceThreshold 
      }
    }),

  makeRuleDecision: (suggestionId: string, decision: any) =>
    apiClient.post(`/rules/suggestions/${suggestionId}/decision`, decision),

  getActiveRules: (ruleType?: string) =>
    apiClient.get('/rules/active', {
      params: { rule_type: ruleType }
    }),

  createManualRule: (rule: any) =>
    apiClient.post('/rules/create', rule),

  getRulePerformance: (ruleId: string, days: number = 30) =>
    apiClient.get(`/rules/${ruleId}/performance`, {
      params: { days }
    }),

  updateRule: (ruleId: string, rule: any) =>
    apiClient.put(`/rules/${ruleId}`, rule),

  deactivateRule: (ruleId: string, reason?: string) =>
    apiClient.delete(`/rules/${ruleId}`, {
      data: { reason }
    }),

  getRuleHistory: (ruleId: string) =>
    apiClient.get(`/rules/${ruleId}/history`),

  performBulkAction: (ruleIds: string[], action: string, reason?: string) =>
    apiClient.post('/rules/bulk-action', {
      rule_ids: ruleIds,
      action,
      reason
    })
};
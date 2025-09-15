import apiClient from '@/lib/api-client';
import type { APIResponse, Rule, RuleCreate } from '@/types';

export const ruleService = {
  async getActiveRules(): Promise<Rule[]> {
    const response = await apiClient.get<APIResponse<Rule[]>>('/api/rules/active');
    return response.data.data!;
  },

  async getAllRules(): Promise<Rule[]> {
    const response = await apiClient.get<APIResponse<Rule[]>>('/api/rules');
    return response.data.data!;
  },

  async createRule(rule: RuleCreate): Promise<Rule> {
    const response = await apiClient.post<APIResponse<Rule>>('/api/rules', rule);
    return response.data.data!;
  },

  async updateRule(ruleId: string, rule: Partial<RuleCreate>): Promise<Rule> {
    const response = await apiClient.put<APIResponse<Rule>>(`/api/rules/${ruleId}`, rule);
    return response.data.data!;
  },

  async deleteRule(ruleId: string): Promise<void> {
    await apiClient.delete(`/api/rules/${ruleId}`);
  },

  async activateRule(ruleId: string): Promise<Rule> {
    const response = await apiClient.post<APIResponse<Rule>>(`/api/rules/${ruleId}/activate`);
    return response.data.data!;
  },

  async deactivateRule(ruleId: string): Promise<Rule> {
    const response = await apiClient.post<APIResponse<Rule>>(`/api/rules/${ruleId}/deactivate`);
    return response.data.data!;
  },
};
import apiClient from '@/lib/api-client';
import type { 
  APIResponse, 
  PatternAnalysis, 
  FeedbackSubmission, 
  ConfidenceAnalysis 
} from '@/types';

export const aiAnalysisService = {
  async getPatterns(): Promise<PatternAnalysis[]> {
    const response = await apiClient.get<APIResponse<PatternAnalysis[]>>('/api/ai/patterns');
    return response.data.data!;
  },

  async submitFeedback(feedback: FeedbackSubmission): Promise<void> {
    await apiClient.post('/api/ai/feedback', feedback);
  },

  async getConfidenceAnalysis(): Promise<ConfidenceAnalysis> {
    const response = await apiClient.get<APIResponse<ConfidenceAnalysis>>('/api/ai/confidence-analysis');
    return response.data.data!;
  },
};
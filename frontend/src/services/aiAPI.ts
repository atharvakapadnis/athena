import { apiClient } from './api';
import { 
  AnalysisRequest, 
  AnalysisResponse, 
  PatternAnalysisResponse,
  FeedbackRequest,
  FeedbackResponse,
  ConfidenceAnalysisResponse
} from '../types/ai';

export const aiAPI = {
  analyzeBatch: (request: AnalysisRequest) =>
    apiClient.post<AnalysisResponse>('/ai/analyze-batch', request),

  getPatternAnalysis: (days: number = 30, patternType?: string, minConfidence: number = 0.6) =>
    apiClient.get<PatternAnalysisResponse[]>('/ai/patterns', {
      params: { days, pattern_type: patternType, min_confidence: minConfidence }
    }),

  getConfidenceAnalysis: (batchId?: string, days: number = 7) =>
    apiClient.get<ConfidenceAnalysisResponse>('/ai/confidence-analysis', {
      params: { batch_id: batchId, days }
    }),

  submitFeedback: (feedback: FeedbackRequest) =>
    apiClient.post<FeedbackResponse>('/ai/feedback', feedback),

  getAISuggestions: (batchId?: string, status?: string, confidenceThreshold: number = 0.7) =>
    apiClient.get<any[]>('/ai/suggestions', {
      params: { 
        batch_id: batchId, 
        status, 
        confidence_threshold: confidenceThreshold 
      }
    }),

  getAnalysisHistory: (page: number = 1, pageSize: number = 20, analysisType?: string) =>
    apiClient.get<any>('/ai/analysis-history', {
      params: { page, page_size: pageSize, analysis_type: analysisType }
    })
};
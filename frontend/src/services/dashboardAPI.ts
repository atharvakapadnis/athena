import { apiClient } from './api';

export const dashboardAPI = {
  getSummary: () =>
    apiClient.get('/dashboard/summary'),

  getRealTimeMetrics: () =>
    apiClient.get('/dashboard/real-time'),

  getExecutiveSummary: () =>
    apiClient.get('/dashboard/executive'),

  getPerformanceHistory: (days: number = 30) =>
    apiClient.get('/dashboard/performance-history', {
      params: { days }
    })
};
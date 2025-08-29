import { apiClient } from './api';

export const batchAPI = {
  getQueue: () =>
    apiClient.get('/batches/queue'),

  getHistory: (page: number = 1, pageSize: number = 20, status?: string) =>
    apiClient.get('/batches/history', {
      params: { page, page_size: pageSize, status }
    }),

  getBatchDetails: (batchId: string) =>
    apiClient.get(`/batches/${batchId}`),

  startBatch: (config: any) =>
    apiClient.post('/batches/start', config),

  pauseBatch: (batchId: string) =>
    apiClient.post(`/batches/${batchId}/pause`),

  resumeBatch: (batchId: string) =>
    apiClient.post(`/batches/${batchId}/resume`),

  cancelBatch: (batchId: string, reason?: string) =>
    apiClient.post(`/batches/${batchId}/cancel`, { reason }),

  getScalingStatus: () =>
    apiClient.get('/batches/scaling/status'),

  configureScaling: (config: any) =>
    apiClient.post('/batches/scaling/configure', config),

  enableScaling: () =>
    apiClient.post('/batches/scaling/enable'),

  disableScaling: () =>
    apiClient.post('/batches/scaling/disable')
};
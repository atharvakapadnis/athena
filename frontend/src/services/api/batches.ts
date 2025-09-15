import apiClient from '@/lib/api-client';
import type { 
  APIResponse, 
  Batch, 
  BatchConfig, 
  BatchResult, 
  PaginatedResponse 
} from '@/types';

export const batchService = {
  async startBatch(config: BatchConfig): Promise<Batch> {
    const response = await apiClient.post<APIResponse<Batch>>('/api/batches/start', config);
    return response.data.data!;
  },

  async getQueue(): Promise<Batch[]> {
    const response = await apiClient.get<APIResponse<Batch[]>>('/api/batches/queue');
    return response.data.data!;
  },

  async getHistory(page: number = 1, perPage: number = 20): Promise<PaginatedResponse<Batch>> {
    const response = await apiClient.get<APIResponse<PaginatedResponse<Batch>>>(
      `/api/batches/history?page=${page}&per_page=${perPage}`
    );
    return response.data.data!;
  },

  async getBatchDetails(batchId: string): Promise<Batch> {
    const response = await apiClient.get<APIResponse<Batch>>(`/api/batches/${batchId}`);
    return response.data.data!;
  },

  async getBatchResults(
    batchId: string, 
    page: number = 1, 
    perPage: number = 50
  ): Promise<PaginatedResponse<BatchResult>> {
    const response = await apiClient.get<APIResponse<PaginatedResponse<BatchResult>>>(
      `/api/batches/${batchId}/results?page=${page}&per_page=${perPage}`
    );
    return response.data.data!;
  },

  async cancelBatch(batchId: string): Promise<void> {
    await apiClient.post(`/api/batches/${batchId}/cancel`);
  },
};
import apiClient from '@/lib/api-client';
import type { 
  APIResponse, 
  Batch, 
  BatchConfig, 
  BatchResult, 
  BatchResultFilters,
  BatchResultSort,
  PaginatedResponse 
} from '@/types';

export const batchService = {
  async startBatch(config: BatchConfig): Promise<Batch> {
    const response = await apiClient.post<APIResponse<Batch>>('/api/batches/start', config);
    if (response.data.status === 'error') {
      throw new Error(response.data.message || 'Failed to start batch');
    }
    return response.data.data!;
  },

  async getQueue(): Promise<Batch[]> {
    const response = await apiClient.get<APIResponse<Batch[]>>('/api/batches/queue');
    if (response.data.status === 'error') {
      throw new Error(response.data.message || 'Failed to get batch queue');
    }
    return response.data.data!;
  },

  async getHistory(page: number = 1, perPage: number = 20): Promise<PaginatedResponse<Batch>> {
    const response = await apiClient.get<APIResponse<PaginatedResponse<Batch>>>(
      `/api/batches/history?page=${page}&per_page=${perPage}`
    );
    if (response.data.status === 'error') {
      throw new Error(response.data.message || 'Failed to get batch history');
    }
    return response.data.data!;
  },

  async getBatchDetails(batchId: string): Promise<Batch> {
    const response = await apiClient.get<APIResponse<Batch>>(`/api/batches/${batchId}`);
    if (response.data.status === 'error') {
      throw new Error(response.data.message || 'Failed to get batch details');
    }
    return response.data.data!;
  },

  async getBatchResults(
    batchId: string, 
    page: number = 1, 
    perPage: number = 50,
    filters?: BatchResultFilters,
    sort?: BatchResultSort
  ): Promise<PaginatedResponse<BatchResult>> {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    });

    if (filters?.success !== undefined) {
      params.append('success', filters.success.toString());
    }
    if (filters?.confidence_level) {
      params.append('confidence_level', filters.confidence_level);
    }
    if (filters?.search) {
      params.append('search', filters.search);
    }
    if (sort?.field) {
      params.append('sort_field', sort.field);
      params.append('sort_direction', sort.direction);
    }

    const response = await apiClient.get<APIResponse<PaginatedResponse<BatchResult>>>(
      `/api/batches/${batchId}/results?${params.toString()}`
    );
    if (response.data.status === 'error') {
      throw new Error(response.data.message || 'Failed to get batch results');
    }
    return response.data.data!;
  },

  async pauseBatch(batchId: string): Promise<Batch> {
    const response = await apiClient.post<APIResponse<Batch>>(`/api/batches/${batchId}/pause`);
    if (response.data.status === 'error') {
      throw new Error(response.data.message || 'Failed to pause batch');
    }
    return response.data.data!;
  },

  async resumeBatch(batchId: string): Promise<Batch> {
    const response = await apiClient.post<APIResponse<Batch>>(`/api/batches/${batchId}/resume`);
    if (response.data.status === 'error') {
      throw new Error(response.data.message || 'Failed to resume batch');
    }
    return response.data.data!;
  },

  async cancelBatch(batchId: string): Promise<Batch> {
    const response = await apiClient.post<APIResponse<Batch>>(`/api/batches/${batchId}/cancel`);
    if (response.data.status === 'error') {
      throw new Error(response.data.message || 'Failed to cancel batch');
    }
    return response.data.data!;
  },
};
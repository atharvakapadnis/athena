import apiClient from '@/lib/api-client';
import type { 
  APIResponse, 
  SystemHealth, 
  SystemStats, 
  SystemLog 
} from '@/types';

export const systemService = {
  async getHealth(): Promise<SystemHealth> {
    const response = await apiClient.get<APIResponse<SystemHealth>>('/api/system/health');
    return response.data.data!;
  },

  async getStats(): Promise<SystemStats> {
    const response = await apiClient.get<APIResponse<SystemStats>>('/api/system/stats');
    return response.data.data!;
  },

  async getLogs(limit: number = 100): Promise<SystemLog[]> {
    const response = await apiClient.get<APIResponse<SystemLog[]>>(`/api/system/logs?limit=${limit}`);
    return response.data.data!;
  },
};
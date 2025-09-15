import apiClient from '@/lib/api-client';
import type { APIResponse, DashboardSummary } from '@/types';

export const dashboardService = {
  async getSummary(): Promise<DashboardSummary> {
    const response = await apiClient.get<APIResponse<DashboardSummary>>('/api/dashboard/summary');
    
    // Check if the API returned an error
    if (response.data.status === 'error') {
      throw new Error(response.data.message || 'Dashboard API returned an error');
    }
    
    // Check if we have data
    if (!response.data.data) {
      throw new Error('No dashboard data received from API');
    }
    
    return response.data.data;
  },
};
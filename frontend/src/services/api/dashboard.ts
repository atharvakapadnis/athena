import apiClient from '@/lib/api-client';
import type { APIResponse, DashboardSummary } from '@/types';

export const dashboardService = {
    async getSummary(): Promise<DashboardSummary> {
        const response = await apiClient.get<APIResponse<DashboardSummary>>('/api/dashboard/summary');
        return response.data.data!;
    },
};
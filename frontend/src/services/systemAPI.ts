import { apiClient } from './api';
import { 
  SystemHealthResponse, 
  SystemStatsResponse,
  ConfigurationRequest,
  UserRequest,
  UserResponse,
  MaintenanceRequest
} from '../types/system';

export const systemAPI = {
  getSystemHealth: () =>
    apiClient.get<SystemHealthResponse>('/system/health'),

  getSystemStats: () =>
    apiClient.get<SystemStatsResponse>('/system/stats'),

  getConfiguration: () =>
    apiClient.get<Record<string, any>>('/system/configuration'),

  updateConfiguration: (config: ConfigurationRequest) =>
    apiClient.post<Record<string, any>>('/system/configuration', config),

  performMaintenance: (maintenance: MaintenanceRequest) =>
    apiClient.post<Record<string, any>>('/system/maintenance', maintenance),

  getLogs: (level?: string, component?: string, limit: number = 100) =>
    apiClient.get<any[]>('/system/logs', {
      params: { level, component, limit }
    }),

  createBackup: (backupType: string = 'full') =>
    apiClient.post<Record<string, any>>('/system/backup', null, {
      params: { backup_type: backupType }
    }),

  getUsers: () =>
    apiClient.get<UserResponse[]>('/system/users'),

  createUser: (user: UserRequest) =>
    apiClient.post<UserResponse>('/system/users', user)
};
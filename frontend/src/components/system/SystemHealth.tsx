import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  CpuChipIcon, 
  ServerIcon, 
  CircleStackIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

import { systemAPI } from '../../services/systemAPI';
import Card from '../ui/Card';
import LoadingSpinner from '../ui/LoadingSpinner';
import { SystemHealthResponse } from '../../types/system';

const SystemHealth: React.FC = () => {
  const { data: health, isLoading, error } = useQuery({
    queryKey: ['system', 'health'],
    queryFn: systemAPI.getSystemHealth,
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      case 'critical':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'warning':
      case 'critical':
        return <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <ServerIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 75) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  if (isLoading) return <LoadingSpinner />;

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Health Check Failed</h3>
          <p className="mt-1 text-sm text-gray-500">
            Unable to retrieve system health information.
          </p>
        </div>
      </Card>
    );
  }

  const healthData: SystemHealthResponse = health?.data;

  if (!healthData) return null;

  return (
    <div className="space-y-6">
      {/* Overall Status */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon(healthData.overall_status)}
            <div>
              <h3 className="text-lg font-medium text-gray-900">System Status</h3>
              <p className="text-sm text-gray-500">
                Last checked: {new Date(healthData.last_check).toLocaleString()}
              </p>
            </div>
          </div>
          <span className={`
            inline-flex items-center rounded-full px-3 py-1 text-sm font-medium capitalize
            ${getStatusColor(healthData.overall_status)}
          `}>
            {healthData.overall_status}
          </span>
        </div>

        {/* Health Issues */}
        {healthData.health_issues.length > 0 && (
          <div className="mt-4 p-4 bg-red-50 rounded-lg">
            <h4 className="text-sm font-medium text-red-800 mb-2">Issues Detected:</h4>
            <ul className="text-sm text-red-700 space-y-1">
              {healthData.health_issues.map((issue, index) => (
                <li key={index}>• {issue}</li>
              ))}
            </ul>
          </div>
        )}
      </Card>

      {/* Resource Usage */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6">
          <div className="flex items-center space-x-3">
            <CpuChipIcon className="w-8 h-8 text-blue-500" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-gray-900">CPU Usage</h4>
              <div className="mt-2">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>{healthData.cpu_usage.toFixed(1)}%</span>
                  <span>Used</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${getUsageColor(healthData.cpu_usage)}`}
                    style={{ width: `${healthData.cpu_usage}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center space-x-3">
            <ServerIcon className="w-8 h-8 text-green-500" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-gray-900">Memory Usage</h4>
              <div className="mt-2">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>{healthData.memory_usage.toFixed(1)}%</span>
                  <span>Used</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${getUsageColor(healthData.memory_usage)}`}
                    style={{ width: `${healthData.memory_usage}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center space-x-3">
            <CircleStackIcon className="w-8 h-8 text-purple-500" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-gray-900">Disk Usage</h4>
              <div className="mt-2">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>{healthData.disk_usage.toFixed(1)}%</span>
                  <span>Used</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${getUsageColor(healthData.disk_usage)}`}
                    style={{ width: `${healthData.disk_usage}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Services Status */}
      <Card className="p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Services Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(healthData.services_status).map(([service, status]) => (
            <div key={service} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-900 capitalize">
                {service.replace('_', ' ')}
              </span>
              <span className={`
                inline-flex items-center rounded-full px-2 py-1 text-xs font-medium
                ${status === 'running' 
                  ? 'text-green-700 bg-green-100' 
                  : status === 'disabled'
                  ? 'text-gray-700 bg-gray-100'
                  : 'text-red-700 bg-red-100'
                }
              `}>
                {status}
              </span>
            </div>
          ))}
        </div>
      </Card>

      {/* System Info */}
      <Card className="p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">System Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <span className="text-sm font-medium text-gray-500">Uptime:</span>
            <span className="ml-2 text-sm text-gray-900">
              {Math.floor(healthData.uptime_seconds / 86400)} days, {Math.floor((healthData.uptime_seconds % 86400) / 3600)} hours
            </span>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-500">Process Memory:</span>
            <span className="ml-2 text-sm text-gray-900">
              {healthData.process_memory_mb.toFixed(1)} MB
            </span>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default SystemHealth;
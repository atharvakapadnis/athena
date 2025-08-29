import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  CogIcon,
  ServerIcon,
  UserGroupIcon,
  DocumentChartBarIcon,
  WrenchScrewdriverIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import SystemHealth from '../components/system/SystemHealth';
import ConfigurationPanel from '../components/system/ConfigurationPanel';
import MaintenancePanel from '../components/system/MaintenancePanel';
import UserManagement from '../components/system/UserManagement';
import { systemAPI } from '../services/systemAPI';
import Button from '../components/ui/Button';
import MetricsCard from '../components/dashboard/MetricsCard';

const SystemSettings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'health' | 'config' | 'maintenance' | 'users' | 'logs'>('health');
  const queryClient = useQueryClient();

  // Fetch system statistics
  const { data: health } = useQuery({
    queryKey: ['system', 'health'],
    queryFn: systemAPI.getSystemHealth,
  });

  const { data: stats } = useQuery({
    queryKey: ['system', 'stats'],
    queryFn: systemAPI.getSystemStats,
  });

  const createBackupMutation = useMutation({
    mutationFn: (backupType: string) => systemAPI.createBackup(backupType),
    onSuccess: (data) => {
      toast.success(`Backup created successfully: ${data.data?.backup_name}`);
      queryClient.invalidateQueries(['system']);
    },
    onError: (error: any) => {
      toast.error(`Failed to create backup: ${error.message}`);
    }
  });

  const tabs = [
    { id: 'health', name: 'System Health', icon: ServerIcon },
    { id: 'config', name: 'Configuration', icon: CogIcon },
    { id: 'maintenance', name: 'Maintenance', icon: WrenchScrewdriverIcon },
    { id: 'users', name: 'User Management', icon: UserGroupIcon },
    { id: 'logs', name: 'System Logs', icon: DocumentChartBarIcon },
  ];

  const healthData = health?.data;
  const statsData = stats?.data;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-start border-b border-gray-200 pb-4">
        <div className="flex items-center space-x-3">
          <ShieldCheckIcon className="w-8 h-8 text-indigo-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">System Administration</h1>
            <p className="mt-2 text-sm text-gray-600">
              Monitor and configure your Athena system
            </p>
          </div>
        </div>
        
        <div className="flex space-x-3">
          <Button
            variant="outline"
            onClick={() => createBackupMutation.mutate('data_only')}
            loading={createBackupMutation.isLoading}
          >
            Quick Backup
          </Button>
          <Button
            onClick={() => createBackupMutation.mutate('full')}
            loading={createBackupMutation.isLoading}
          >
            Full Backup
          </Button>
        </div>
      </div>

      {/* System Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricsCard
          title="System Status"
          value={healthData?.overall_status || 'Unknown'}
          description="Overall health"
          changeType={healthData?.overall_status === 'healthy' ? 'increase' : 'neutral'}
        />
        <MetricsCard
          title="Uptime"
          value={`${Math.floor((healthData?.uptime_seconds || 0) / 86400)}d`}
          description="Days running"
          changeType="increase"
        />
        <MetricsCard
          title="Data Size"
          value={`${statsData?.data_stats?.total_size_mb?.toFixed(1) || '0'}MB`}
          description="Total data stored"
        />
        <MetricsCard
          title="Active Services"
          value={Object.values(healthData?.services_status || {}).filter(s => s === 'running').length}
          description="Running services"
          changeType="increase"
        />
      </div>

      {/* Internal Network Status */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-center space-x-3">
          <ShieldCheckIcon className="w-6 h-6 text-blue-600" />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-blue-900">Internal Network Deployment</h3>
            <p className="text-sm text-blue-700">
              System optimized for secure internal network access • Relaxed authentication for trusted environment
            </p>
          </div>
          <div className="text-right">
            <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
              Internal Only
            </span>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`
                  flex items-center py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap
                  ${activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon className="w-4 h-4 mr-2" />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-[600px]">
        {activeTab === 'health' && <SystemHealth />}
        {activeTab === 'config' && <ConfigurationPanel />}
        {activeTab === 'maintenance' && <MaintenancePanel />}
        {activeTab === 'users' && <UserManagement />}
        {activeTab === 'logs' && <SystemLogs />}
      </div>
    </div>
  );
};

// System Logs Component
const SystemLogs: React.FC = () => {
  const [filters, setFilters] = useState({
    level: '',
    component: '',
    limit: 100
  });

  const { data: logs, isLoading } = useQuery({
    queryKey: ['system', 'logs', filters],
    queryFn: () => systemAPI.getLogs(filters.level, filters.component, filters.limit),
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  const logsList = logs?.data || [];

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Log Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-700">Log Level</label>
            <select
              value={filters.level}
              onChange={(e) => setFilters(prev => ({ ...prev, level: e.target.value }))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            >
              <option value="">All Levels</option>
              <option value="ERROR">Error</option>
              <option value="WARNING">Warning</option>
              <option value="INFO">Info</option>
              <option value="DEBUG">Debug</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700">Component</label>
            <select
              value={filters.component}
              onChange={(e) => setFilters(prev => ({ ...prev, component: e.target.value }))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            >
              <option value="">All Components</option>
              <option value="batch_processor">Batch Processor</option>
              <option value="ai_analysis">AI Analysis</option>
              <option value="rule_editor">Rule Editor</option>
              <option value="web">Web Interface</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700">Limit</label>
            <select
              value={filters.limit}
              onChange={(e) => setFilters(prev => ({ ...prev, limit: parseInt(e.target.value) }))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            >
              <option value={50}>50 entries</option>
              <option value={100}>100 entries</option>
              <option value={200}>200 entries</option>
              <option value={500}>500 entries</option>
            </select>
          </div>
        </div>
      </div>

      {/* Logs Display */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            System Logs ({logsList.length} entries)
          </h3>
        </div>

        <div className="max-h-96 overflow-y-auto">
          {isLoading ? (
            <div className="p-6 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
              <p className="mt-2 text-sm text-gray-500">Loading logs...</p>
            </div>
          ) : logsList.length === 0 ? (
            <div className="p-6 text-center">
              <DocumentChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No logs found</h3>
              <p className="mt-1 text-sm text-gray-500">
                No log entries match the current filters.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {logsList.map((log, index) => (
                <div key={index} className="px-6 py-3 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3">
                        <span className={`
                          inline-flex items-center rounded-full px-2 py-1 text-xs font-medium
                          ${log.level === 'ERROR' ? 'text-red-700 bg-red-100' :
                            log.level === 'WARNING' ? 'text-yellow-700 bg-yellow-100' :
                            log.level === 'INFO' ? 'text-blue-700 bg-blue-100' :
                            'text-gray-700 bg-gray-100'}
                        `}>
                          {log.level}
                        </span>
                        <span className="text-xs text-gray-500">
                          {log.component}
                        </span>
                        <span className="text-xs text-gray-400">
                          {new Date(log.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-gray-900 font-mono">
                        {log.message}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SystemSettings;
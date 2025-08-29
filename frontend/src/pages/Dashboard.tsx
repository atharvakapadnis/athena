import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

import MetricsCard from '../components/dashboard/MetricsCard';
import PerformanceChart from '../components/dashboard/PerformanceChart';
import SystemHealth from '../components/dashboard/SystemHealth';
import RealtimeMetrics from '../components/dashboard/RealtimeMetrics';
import { dashboardAPI } from '../services/dashboardAPI';

const Dashboard: React.FC = () => {
  // Fetch dashboard data
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: dashboardAPI.getSummary,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const { data: realTime, isLoading: realTimeLoading } = useQuery({
    queryKey: ['dashboard', 'realtime'],
    queryFn: dashboardAPI.getRealTimeMetrics,
    refetchInterval: 5000, // Refetch every 5 seconds
  });

  const { data: performanceHistory, isLoading: historyLoading } = useQuery({
    queryKey: ['dashboard', 'performance-history'],
    queryFn: () => dashboardAPI.getPerformanceHistory(30), // Last 30 days
    refetchInterval: 300000, // Refetch every 5 minutes
  });

  const summaryData = summary?.data;
  const realTimeData = realTime?.data;
  const historyData = performanceHistory?.data;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-sm text-gray-600">
          Monitor your Athena system performance and quality metrics
        </p>
      </div>

      {/* Real-time Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricsCard
          title="Success Rate"
          value={realTimeData?.current_batch_status?.success_rate ? 
            `${(realTimeData.current_batch_status.success_rate * 100).toFixed(1)}%` : 
            'N/A'
          }
          change={summaryData?.performance_metrics?.success_rate_change}
          changeType={summaryData?.performance_metrics?.success_rate_change > 0 ? 'increase' : 'decrease'}
          icon={<CheckCircleIcon />}
          description="Current batch success rate"
          loading={realTimeLoading}
        />

        <MetricsCard
          title="Confidence Score"
          value={realTimeData?.current_batch_status?.confidence_score ? 
            `${(realTimeData.current_batch_status.confidence_score * 100).toFixed(1)}%` : 
            'N/A'
          }
          change={summaryData?.quality_metrics?.confidence_change}
          changeType={summaryData?.quality_metrics?.confidence_change > 0 ? 'increase' : 'decrease'}
          icon={<ChartBarIcon />}
          description="Average confidence level"
          loading={realTimeLoading}
        />

        <MetricsCard
          title="Processing Time"
          value={realTimeData?.current_batch_status?.processing_time ? 
            `${realTimeData.current_batch_status.processing_time.toFixed(2)}s` : 
            'N/A'
          }
          change={summaryData?.performance_metrics?.processing_time_change}
          changeType={summaryData?.performance_metrics?.processing_time_change < 0 ? 'increase' : 'decrease'}
          icon={<ClockIcon />}
          description="Average per item"
          loading={realTimeLoading}
        />

        <MetricsCard
          title="Active Alerts"
          value={realTimeData?.active_alerts || 0}
          icon={<ExclamationTriangleIcon />}
          description="Requires attention"
          loading={realTimeLoading}
        />
      </div>

      {/* Performance Chart and System Health */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <PerformanceChart
            data={historyData || []}
            loading={historyLoading}
            height={350}
          />
        </div>
        
        <div>
          <SystemHealth
            health={summaryData?.system_health}
            recommendations={summaryData?.recommendations?.slice(0, 3)}
            loading={summaryLoading}
          />
        </div>
      </div>

      {/* Real-time Activity Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RealtimeMetrics
          data={realTimeData}
          loading={realTimeLoading}
        />
        
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {summaryData?.recent_activity?.slice(0, 5).map((activity, index) => (
              <div key={index} className="flex items-start space-x-3">
                <div className={`
                  flex-shrink-0 w-2 h-2 mt-2 rounded-full
                  ${activity.status === 'success' ? 'bg-green-400' : 
                    activity.status === 'warning' ? 'bg-yellow-400' : 'bg-red-400'}
                `} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">{activity.description}</p>
                  <p className="text-xs text-gray-500">
                    {new Date(activity.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
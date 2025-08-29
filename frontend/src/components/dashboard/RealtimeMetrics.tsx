import React from 'react';
import { 
  SignalIcon, 
  ChartBarIcon, 
  ClockIcon,
  TrendingUpIcon
} from '@heroicons/react/24/outline';
import Card from '../ui/Card';

interface RealtimeMetricsProps {
  data: any;
  loading?: boolean;
}

const RealtimeMetrics: React.FC<RealtimeMetricsProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Real-time Metrics</h3>
        <p className="text-sm text-gray-500">No real-time data available</p>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Real-time Metrics</h3>
        <SignalIcon className="w-5 h-5 text-green-500" />
      </div>

      <div className="space-y-4">
        {/* Current Processing Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ChartBarIcon className="w-4 h-4 text-blue-500" />
            <span className="text-sm text-gray-700">Processing Rate</span>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium text-gray-900">
              {data.recent_averages?.items_processed || 0} items/min
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ClockIcon className="w-4 h-4 text-green-500" />
            <span className="text-sm text-gray-700">Avg Response Time</span>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium text-gray-900">
              {data.recent_averages?.processing_time?.toFixed(2) || 0}s
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <TrendingUpIcon className="w-4 h-4 text-purple-500" />
            <span className="text-sm text-gray-700">Success Rate</span>
          </div>
          <div className="text-right">
            <div className="text-sm font-medium text-gray-900">
              {(data.recent_averages?.success_rate * 100)?.toFixed(1) || 0}%
            </div>
          </div>
        </div>

        {/* Confidence Distribution */}
        {data.confidence_breakdown && (
          <div className="pt-4 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Confidence Distribution</h4>
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-green-600">High</span>
                <span>{data.confidence_breakdown.high_percentage}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div 
                  className="bg-green-500 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${data.confidence_breakdown.high_percentage}%` }}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default RealtimeMetrics;
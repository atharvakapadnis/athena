import React from 'react';

interface SystemHealthProps {
  health?: any;
  recommendations?: any[];
  loading?: boolean;
}

const SystemHealth: React.FC<SystemHealthProps> = ({
  health,
  recommendations = [],
  loading = false
}) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  const getHealthColor = (status: string) => {
    if (status === 'healthy') return 'text-green-600';
    if (status === 'warning') return 'text-yellow-600';
    return 'text-red-600';
  };

  const getHealthIcon = (status: string) => {
    if (status === 'healthy') return '✅';
    if (status === 'warning') return '⚠️';
    return '❌';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">System Health</h3>
      
      <div className="space-y-4">
        <div className="flex items-center">
          <span className="text-2xl mr-3">
            {getHealthIcon(health?.overall_status || 'healthy')}
          </span>
          <div>
            <p className={`font-medium ${getHealthColor(health?.overall_status || 'healthy')}`}>
              {health?.overall_status || 'Healthy'}
            </p>
            <p className="text-sm text-gray-500">Overall system status</p>
          </div>
        </div>

        {recommendations.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2">Recommendations</h4>
            <div className="space-y-2">
              {recommendations.map((rec, index) => (
                <div key={index} className="text-sm text-gray-600 p-2 bg-blue-50 rounded">
                  {rec.message || rec}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemHealth;
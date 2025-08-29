import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChartBarIcon, TrendingUpIcon, TrendingDownIcon } from '@heroicons/react/24/outline';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

import { aiAPI } from '../../services/aiAPI';
import Card from '../ui/Card';
import LoadingSpinner from '../ui/LoadingSpinner';

interface ConfidenceViewerProps {
  days?: number;
  batchId?: string;
}

const ConfidenceViewer: React.FC<ConfidenceViewerProps> = ({ days = 7, batchId }) => {
  const { data: analysis, isLoading } = useQuery({
    queryKey: ['ai', 'confidence', days, batchId],
    queryFn: () => aiAPI.getConfidenceAnalysis(batchId, days),
    refetchInterval: 60000,
  });

  const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'];

  if (isLoading) return <LoadingSpinner />;

  const analysisData = analysis?.data;
  if (!analysisData) return null;

  // Prepare data for charts
  const distributionData = Object.entries(analysisData.confidence_distribution).map(([key, value]) => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    value: value,
    percentage: (value * 100).toFixed(1)
  }));

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">
          Confidence Analysis
        </h3>
        <div className="text-sm text-gray-500">
          {batchId ? `Batch: ${batchId}` : `Last ${days} days`}
        </div>
      </div>

      {/* Overall Confidence Score */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-gray-500">Overall Confidence</h4>
            <div className="mt-2 flex items-baseline">
              <span className="text-3xl font-bold text-gray-900">
                {(analysisData.overall_confidence * 100).toFixed(1)}%
              </span>
              <span className="ml-2 text-sm text-gray-500">average</span>
            </div>
          </div>
          <ChartBarIcon className="w-8 h-8 text-indigo-500" />
        </div>
      </Card>

      {/* Confidence Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h4 className="text-lg font-medium text-gray-900 mb-4">Confidence Distribution</h4>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={distributionData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {distributionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: any) => [`${(value * 100).toFixed(1)}%`, 'Percentage']} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-2 gap-4">
            {distributionData.map((item, index) => (
              <div key={item.name} className="flex items-center">
                <div 
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                <span className="text-sm text-gray-600">
                  {item.name}: {item.percentage}%
                </span>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-6">
          <h4 className="text-lg font-medium text-gray-900 mb-4">Improvement Suggestions</h4>
          <div className="space-y-3">
            {analysisData.improvement_suggestions.slice(0, 5).map((suggestion, index) => (
              <div key={index} className="flex items-start space-x-3">
                <TrendingUpIcon className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-gray-700">{suggestion}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Low Confidence Patterns */}
      {analysisData.low_confidence_patterns.length > 0 && (
        <Card className="p-6">
          <h4 className="text-lg font-medium text-gray-900 mb-4">
            Low Confidence Patterns ({analysisData.low_confidence_patterns.length})
          </h4>
          <div className="space-y-3">
            {analysisData.low_confidence_patterns.slice(0, 5).map((pattern, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <TrendingDownIcon className="w-5 h-5 text-red-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {pattern.pattern || 'Pattern not specified'}
                    </p>
                    <p className="text-xs text-gray-500">
                      Confidence: {((pattern.confidence || 0) * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
                <span className="text-xs text-red-600 bg-red-100 px-2 py-1 rounded">
                  Needs Attention
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default ConfidenceViewer;
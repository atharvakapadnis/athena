import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format, parseISO } from 'date-fns';

interface PerformanceData {
  date: string;
  success_rate: number;
  confidence_score: number;
  processing_time: number;
  items_processed: number;
}

interface PerformanceChartProps {
  data: PerformanceData[];
  loading?: boolean;
  height?: number;
  showLegend?: boolean;
  className?: string;
}

const PerformanceChart: React.FC<PerformanceChartProps> = ({
  data,
  loading = false,
  height = 300,
  showLegend = true,
  className
}) => {
  const formatDate = (dateStr: string) => {
    try {
      return format(parseISO(dateStr), 'MMM dd');
    } catch {
      return dateStr;
    }
  };

  const formatTooltipValue = (value: any, name: string) => {
    switch (name) {
      case 'success_rate':
        return [`${(value * 100).toFixed(1)}%`, 'Success Rate'];
      case 'confidence_score':
        return [`${(value * 100).toFixed(1)}%`, 'Confidence Score'];
      case 'processing_time':
        return [`${value.toFixed(2)}s`, 'Avg Processing Time'];
      case 'items_processed':
        return [value.toLocaleString(), 'Items Processed'];
      default:
        return [value, name];
    }
  };

  if (loading) {
    return (
      <div className={clsx('bg-white rounded-lg shadow p-6', className)}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('bg-white rounded-lg shadow p-6', className)}>
      <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Trends</h3>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="date" 
            tickFormatter={formatDate}
            stroke="#6b7280"
            fontSize={12}
          />
          <YAxis 
            stroke="#6b7280"
            fontSize={12}
            domain={[0, 1]}
            tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
          />
          <Tooltip 
            formatter={formatTooltipValue}
            labelFormatter={(label) => `Date: ${formatDate(label)}`}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
            }}
          />
          {showLegend && <Legend />}
          
          <Line
            type="monotone"
            dataKey="success_rate"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, stroke: '#10b981', strokeWidth: 2 }}
            name="Success Rate"
          />
          
          <Line
            type="monotone"
            dataKey="confidence_score"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, stroke: '#3b82f6', strokeWidth: 2 }}
            name="Confidence Score"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PerformanceChart;
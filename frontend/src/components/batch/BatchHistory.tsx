import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  PauseCircleIcon
} from '@heroicons/react/24/outline';

import { batchAPI } from '../../services/batchAPI';
import Card from '../ui/Card';
import LoadingSpinner from '../ui/LoadingSpinner';

const BatchHistory: React.FC = () => {
  const [currentPage, setCurrentPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');

  const { data: history, isLoading } = useQuery({
    queryKey: ['batches', 'history', currentPage, statusFilter],
    queryFn: () => batchAPI.getHistory(currentPage, 20, statusFilter || undefined),
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      case 'paused':
        return <PauseCircleIcon className="w-5 h-5 text-yellow-500" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-700 bg-green-100';
      case 'failed':
        return 'text-red-700 bg-red-100';
      case 'paused':
        return 'text-yellow-700 bg-yellow-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  if (isLoading) return <LoadingSpinner />;

  const historyData = history?.data;
  const batches = historyData?.items || [];

  return (
    <Card className="overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-medium text-gray-900">
            Batch History ({historyData?.total || 0})
          </h3>
          
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-md border-gray-300 text-sm focus:border-indigo-500 focus:ring-indigo-500"
          >
            <option value="">All Status</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="paused">Paused</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Batch ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Items
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Performance
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Completed
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {batches.map((batch: any) => (
              <tr key={batch.batch_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {getStatusIcon(batch.status)}
                    <div className="ml-3">
                      <div className="text-sm font-medium text-gray-900">
                        {batch.batch_id.substring(0, 8)}...
                      </div>
                      <div className="text-sm text-gray-500">
                        Size: {batch.batch_size}
                      </div>
                    </div>
                  </div>
                </td>

                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`
                    inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset
                    ${getStatusColor(batch.status)}
                  `}>
                    {batch.status.toUpperCase()}
                  </span>
                </td>

                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  <div>Processed: {batch.items_processed}</div>
                  <div className="text-gray-500">Total: {batch.total_items}</div>
                </td>

                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    Success: {(batch.success_rate * 100).toFixed(1)}%
                  </div>
                  <div className="text-sm text-gray-500">
                    Confidence: {(batch.average_confidence * 100).toFixed(1)}%
                  </div>
                </td>

                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {batch.completed_at 
                    ? new Date(batch.completed_at).toLocaleString()
                    : 'In Progress'
                  }
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {batches.length === 0 && (
          <div className="text-center py-12">
            <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No batch history</h3>
            <p className="mt-1 text-sm text-gray-500">
              Batch history will appear here once batches are processed.
            </p>
          </div>
        )}
      </div>

      {/* Pagination */}
      {historyData && historyData.total_pages > 1 && (
        <div className="px-6 py-3 border-t border-gray-200 flex justify-between items-center">
          <div className="text-sm text-gray-500">
            Page {historyData.page} of {historyData.total_pages}
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={!historyData.has_previous}
              className="px-3 py-1 text-sm border rounded disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(prev => prev + 1)}
              disabled={!historyData.has_next}
              className="px-3 py-1 text-sm border rounded disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </Card>
  );
};

export default BatchHistory;
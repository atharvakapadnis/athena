import React from 'react';
import { useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {
    PlayIcon,
    PauseIcon,
    StopIcon,
    ClockIcon,
    CheckCircleIcon,
    ExclamationCircleIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import { batchAPI } from '../../services/batchAPI';
import { BatchResponse, BatchStatus } from '../../types/batch';
import Button from '../ui/Button';
import LoadingSpinner from '../ui/LoadingSpinner';

const BatchQueue: React.FC = () => {
    const queryClient = useQueryClient();
    
    const { data: queue, isLoading} = useQuery({
        queryKey: ['batches','queue'],
        queryFn: batchAPI.getQueue,
        refetchInterval: 5000, //Refetch every 5 seconds
    });

    const pauseMutation = useMutation({
        mutationFn: (batchID: string) => batchAPI.pauseBatch(batchID),
        onSuccess: (data, batchID) => {
            toast.success(`Batch ${batchID} paused successfully`);
            queryClient.invalidateQueries(['batches']);
        },
        onError: (error: any) => {
            toast.error(`Failed to pause batch ${error.message}`);
        }
    });

    const resumeMutation = useMutation({
        mutationFn: (batchID: string) => batchAPI.resumeBatch(batchID),
        onSuccess: (data, batchID) => {
            toast.success(`Batch ${batchID} resumed successfully`);
            queryClient.invalidateQueries(['batches']);
        },
        onError: (error: any) => {
            toast.error(`Failed to resume batch ${error.message}`);
        }
    });

    const cancelMutation = useMutation({
        mutationFn: (batchID: string) => batchAPI.cancelBatch(batchID),
        onSuccess: (data, batchID) => {
            toast.success(`Batch ${batchID} cancelled successfully`);
            queryClient.invalidateQueries(['batches']);
        },
        onError: (error: any) => {
            toast.error(`Failed to cancel batch ${error.message}`);
        }
    });

    const getStatusIcon = (status: BatchStatus) => {
        switch (status) {
          case BatchStatus.RUNNING:
            return <PlayIcon className="w-5 h-5 text-green-500" />;
          case BatchStatus.PAUSED:
            return <PauseIcon className="w-5 h-5 text-yellow-500" />;
          case BatchStatus.COMPLETED:
            return <CheckCircleIcon className="w-5 h-5 text-blue-500" />;
          case BatchStatus.FAILED:
            return <ExclamationCircleIcon className="w-5 h-5 text-red-500" />;
          case BatchStatus.CANCELLED:
            return <StopIcon className="w-5 h-5 text-gray-500" />;
          default:
            return <ClockIcon className="w-5 h-5 text-gray-400" />;
        }
    };
     
      const getStatusColor = (status: BatchStatus) => {
        switch (status) {
          case BatchStatus.RUNNING:
            return 'text-green-700 bg-green-50 ring-green-600/20';
          case BatchStatus.PAUSED:
            return 'text-yellow-700 bg-yellow-50 ring-yellow-600/20';
          case BatchStatus.COMPLETED:
            return 'text-blue-700 bg-blue-50 ring-blue-600/20';
          case BatchStatus.FAILED:
            return 'text-red-700 bg-red-50 ring-red-600/20';
          case BatchStatus.CANCELLED:
            return 'text-gray-700 bg-gray-50 ring-gray-600/20';
          default:
            return 'text-gray-700 bg-gray-50 ring-gray-600/20';
        }
    };

    const formatDuration = (seconds: number) => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    };

    if (isLoading) {
        return <LoadingSpinner />;
    }

    const batches = queue?.data || [];

    return (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Batch Processing Queue</h3>
            <p className="mt-1 text-sm text-gray-600">
              {batches.length} batch{batches.length !== 1 ? 'es' : ''} in queue
            </p>
          </div>
     
          <div className="overflow-hidden">
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
                    Progress
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Performance
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {batches.map((batch: BatchResponse) => (
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
                        {batch.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
     
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${batch.progress_percentage}%` }}
                        />
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {batch.items_processed} / {batch.total_items} items
                      </div>
                    </td>
     
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {batch.processing_duration ? formatDuration(batch.processing_duration) : '-'}
                    </td>
     
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        Success: {(batch.success_rate * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-gray-500">
                        Confidence: {(batch.average_confidence * 100).toFixed(1)}%
                      </div>
                    </td>
     
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      {batch.status === BatchStatus.RUNNING && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => pauseMutation.mutate(batch.batch_id)}
                          loading={pauseMutation.isLoading}
                        >
                          <PauseIcon className="w-4 h-4" />
                        </Button>
                      )}
                      
                      {batch.status === BatchStatus.PAUSED && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => resumeMutation.mutate(batch.batch_id)}
                          loading={resumeMutation.isLoading}
                        >
                          <PlayIcon className="w-4 h-4" />
                        </Button>
                      )}
                      
                      {(batch.status === BatchStatus.RUNNING || batch.status === BatchStatus.PAUSED) && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => cancelMutation.mutate(batch.batch_id)}
                          loading={cancelMutation.isLoading}
                          className="text-red-600 hover:text-red-700"
                        >
                          <StopIcon className="w-4 h-4" />
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
     
            {batches.length === 0 && (
              <div className="text-center py-12">
                <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No batches in queue</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Start a new batch to see it appear here.
                </p>
              </div>
            )}
          </div>
        </div>
      );
     };
     
export default BatchQueue;
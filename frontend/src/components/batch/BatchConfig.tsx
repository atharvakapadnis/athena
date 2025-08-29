import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Dialog } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import { batchAPI } from '../../services/batchAPI';
import { BatchConfigRequest } from '../../types/batch';
import Button from '../ui/Button';
import Modal from '../ui/Modal';

interface BatchConfigProps {
  isOpen: boolean;
  onClose: () => void;
}

const BatchConfig: React.FC<BatchConfigProps> = ({ isOpen, onClose }) => {
  const queryClient = useQueryClient();
  
  const [config, setConfig] = useState<BatchConfigRequest>({
    batch_size: 50,
    start_index: 0,
    confidence_threshold_high: 0.8,
    confidence_threshold_medium: 0.6,
    max_processing_time: 300, // 5 minutes
    retry_failed_items: true,
    notification_webhook: '',
    priority: 'normal'
  });

  const startBatchMutation = useMutation({
    mutationFn: (config: BatchConfigRequest) => batchAPI.startBatch(config),
    onSuccess: (data) => {
      toast.success(`Batch ${data.data?.batch_id} started successfully`);
      queryClient.invalidateQueries(['batches']);
      onClose();
    },
    onError: (error: any) => {
      toast.error(`Failed to start batch: ${error.message}`);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    startBatchMutation.mutate(config);
  };

  const handleInputChange = (field: keyof BatchConfigRequest, value: any) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Start New Batch">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Configuration */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Basic Configuration</h4>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Batch Size
              </label>
              <input
                type="number"
                min="1"
                max="1000"
                value={config.batch_size}
                onChange={(e) => handleInputChange('batch_size', parseInt(e.target.value))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">Number of items to process in this batch</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Start Index
              </label>
              <input
                type="number"
                min="0"
                value={config.start_index}
                onChange={(e) => handleInputChange('start_index', parseInt(e.target.value))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">Index to start processing from</p>
            </div>
          </div>
        </div>

        {/* Confidence Thresholds */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Confidence Thresholds</h4>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                High Confidence Threshold
              </label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={config.confidence_threshold_high}
                onChange={(e) => handleInputChange('confidence_threshold_high', parseFloat(e.target.value))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">Threshold for high confidence classification</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Medium Confidence Threshold
              </label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={config.confidence_threshold_medium}
                onChange={(e) => handleInputChange('confidence_threshold_medium', parseFloat(e.target.value))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">Threshold for medium confidence classification</p>
            </div>
          </div>
        </div>

        {/* Advanced Options */}
        <div>
          <h4 className="text-sm font-medium text-gray-900 mb-3">Advanced Options</h4>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Max Processing Time (seconds)
              </label>
              <input
                type="number"
                min="60"
                max="3600"
                value={config.max_processing_time}
                onChange={(e) => handleInputChange('max_processing_time', parseInt(e.target.value))}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">Maximum time allowed for batch processing</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Priority
              </label>
              <select
                value={config.priority}
                onChange={(e) => handleInputChange('priority', e.target.value)}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              >
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
              </select>
              <p className="mt-1 text-xs text-gray-500">Processing priority for this batch</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Notification Webhook (Optional)
              </label>
              <input
                type="url"
                value={config.notification_webhook}
                onChange={(e) => handleInputChange('notification_webhook', e.target.value)}
                placeholder="https://your-webhook-url.com/batch-complete"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              />
              <p className="mt-1 text-xs text-gray-500">URL to notify when batch completes</p>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="retry-failed"
                checked={config.retry_failed_items}
                onChange={(e) => handleInputChange('retry_failed_items', e.target.checked)}
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label htmlFor="retry-failed" className="ml-2 block text-sm text-gray-900">
                Retry failed items
              </label>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
          <Button
            type="button"
            variant="outline"
            onClick={onClose}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            loading={startBatchMutation.isLoading}
          >
            Start Batch
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default BatchConfig;
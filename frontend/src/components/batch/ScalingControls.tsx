import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AdjustmentsHorizontalIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import { batchAPI } from '../../services/batchAPI';
import Button from '../ui/Button';
import Modal from '../ui/Modal';

interface ScalingControlsProps {
  isOpen: boolean;
  onClose: () => void;
  currentConfig?: any;
}

const ScalingControls: React.FC<ScalingControlsProps> = ({
  isOpen,
  onClose,
  currentConfig
}) => {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState({
    enabled: currentConfig?.enabled || false,
    min_batch_size: currentConfig?.min_batch_size || 10,
    max_batch_size: currentConfig?.max_batch_size || 200,
    target_confidence: currentConfig?.target_confidence || 0.85,
    scaling_factor: currentConfig?.scaling_factor || 1.2
  });

  const configureScalingMutation = useMutation({
    mutationFn: (config: any) => batchAPI.configureScaling(config),
    onSuccess: () => {
      toast.success('Scaling configuration updated successfully');
      queryClient.invalidateQueries(['batches', 'scaling-status']);
      onClose();
    },
    onError: (error: any) => {
      toast.error(`Failed to update scaling configuration: ${error.message}`);
    }
  });

  const toggleScalingMutation = useMutation({
    mutationFn: (enabled: boolean) => 
      enabled ? batchAPI.enableScaling() : batchAPI.disableScaling(),
    onSuccess: (data, enabled) => {
      toast.success(`Dynamic scaling ${enabled ? 'enabled' : 'disabled'}`);
      queryClient.invalidateQueries(['batches', 'scaling-status']);
    },
    onError: (error: any) => {
      toast.error(`Failed to toggle scaling: ${error.message}`);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    configureScalingMutation.mutate(config);
  };

  const handleToggleScaling = () => {
    const newEnabled = !config.enabled;
    setConfig(prev => ({ ...prev, enabled: newEnabled }));
    toggleScalingMutation.mutate(newEnabled);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Scaling Configuration">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Enable/Disable Toggle */}
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-gray-900">Dynamic Scaling</h4>
            <p className="text-sm text-gray-500">
              Automatically adjust batch size based on performance
            </p>
          </div>
          <button
            type="button"
            onClick={handleToggleScaling}
            className={`
              relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent 
              transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
              ${config.enabled ? 'bg-indigo-600' : 'bg-gray-200'}
            `}
          >
            <span
              className={`
                pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 
                transition duration-200 ease-in-out
                ${config.enabled ? 'translate-x-5' : 'translate-x-0'}
              `}
            />
          </button>
        </div>

        {config.enabled && (
          <>
            {/* Batch Size Limits */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">Batch Size Limits</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Minimum Size
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="1000"
                    value={config.min_batch_size}
                    onChange={(e) => setConfig(prev => ({ 
                      ...prev, 
                      min_batch_size: parseInt(e.target.value) 
                    }))}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Maximum Size
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="1000"
                    value={config.max_batch_size}
                    onChange={(e) => setConfig(prev => ({ 
                      ...prev, 
                      max_batch_size: parseInt(e.target.value) 
                    }))}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Performance Targets */}
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-3">Performance Targets</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Target Confidence
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.01"
                    value={config.target_confidence}
                    onChange={(e) => setConfig(prev => ({ 
                      ...prev, 
                      target_confidence: parseFloat(e.target.value) 
                    }))}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                  <p className="mt-1 text-xs text-gray-500">0.0 - 1.0</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Scaling Factor
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="2"
                    step="0.1"
                    value={config.scaling_factor}
                    onChange={(e) => setConfig(prev => ({ 
                      ...prev, 
                      scaling_factor: parseFloat(e.target.value) 
                    }))}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                  <p className="mt-1 text-xs text-gray-500">Multiplier for scaling up/down</p>
                </div>
              </div>
            </div>
          </>
        )}

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
            loading={configureScalingMutation.isLoading}
            disabled={!config.enabled}
          >
            Save Configuration
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default ScalingControls;
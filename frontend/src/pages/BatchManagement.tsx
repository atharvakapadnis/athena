import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PlusIcon, AdjustmentsHorizontalIcon } from '@heroicons/react/24/outline';

import BatchQueue from '../components/batch/BatchQueue';
import BatchHistory from '../components/batch/BatchHistory';
import BatchConfig from '../components/batch/BatchConfig';
import ScalingControls from '../components/batch/ScalingControls';
import { batchAPI } from '../services/batchAPI';
import Button from '../components/ui/Button';
import MetricsCard from '../components/dashboard/MetricsCard';

const BatchManagement: React.FC = () => {
  const [showBatchConfig, setShowBatchConfig] = useState(false);
  const [showScalingControls, setShowScalingControls] = useState(false);

  // Fetch batch statistics
  const { data: scalingStatus } = useQuery({
    queryKey: ['batches', 'scaling-status'],
    queryFn: batchAPI.getScalingStatus,
    refetchInterval: 10000, // Refetch every 10 seconds
  });

  const scalingData = scalingStatus?.data;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-start border-b border-gray-200 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Batch Management</h1>
          <p className="mt-2 text-sm text-gray-600">
            Monitor and control batch processing operations
          </p>
        </div>
        <div className="flex space-x-3">
          <Button
            variant="outline"
            onClick={() => setShowScalingControls(true)}
          >
            <AdjustmentsHorizontalIcon className="w-4 h-4 mr-2" />
            Scaling Settings
          </Button>
          <Button onClick={() => setShowBatchConfig(true)}>
            <PlusIcon className="w-4 h-4 mr-2" />
            Start New Batch
          </Button>
        </div>
      </div>

      {/* Scaling Status Cards */}
      {scalingData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <MetricsCard
            title="Dynamic Scaling"
            value={scalingData.enabled ? 'Enabled' : 'Disabled'}
            description={`Current batch size: ${scalingData.current_batch_size}`}
            changeType={scalingData.enabled ? 'increase' : 'neutral'}
          />
          <MetricsCard
            title="Scaling Efficiency"
            value={`${(scalingData.efficiency_score * 100).toFixed(1)}%`}
            description="Overall scaling performance"
            change={scalingData.efficiency_change}
            changeType={scalingData.efficiency_change > 0 ? 'increase' : 'decrease'}
          />
          <MetricsCard
            title="Recommended Size"
            value={scalingData.recommended_batch_size.toString()}
            description={`Confidence: ${(scalingData.recommendation_confidence * 100).toFixed(1)}%`}
            changeType={scalingData.recommended_batch_size > scalingData.current_batch_size ? 'increase' : 'decrease'}
          />
        </div>
      )}

      {/* Batch Queue */}
      <BatchQueue />

      {/* Batch History */}
      <BatchHistory />

      {/* Modals */}
      <BatchConfig
        isOpen={showBatchConfig}
        onClose={() => setShowBatchConfig(false)}
      />

      <ScalingControls
        isOpen={showScalingControls}
        onClose={() => setShowScalingControls(false)}
        currentConfig={scalingData}
      />
    </div>
  );
};

export default BatchManagement;
import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  WrenchScrewdriverIcon,
  TrashIcon,
  ArrowPathIcon,
  MagnifyingGlassIcon,
  ArrowUpIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import { systemAPI } from '../../services/systemAPI';
import Button from '../ui/Button';
import Card from '../ui/Card';

const MaintenancePanel: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedTask, setSelectedTask] = useState<string>('');

  const maintenanceMutation = useMutation({
    mutationFn: (taskType: string) => systemAPI.performMaintenance({ task_type: taskType }),
    onSuccess: (data, taskType) => {
      toast.success(`${taskType} completed successfully`);
      queryClient.invalidateQueries(['system']);
    },
    onError: (error: any, taskType) => {
      toast.error(`Failed to complete ${taskType}: ${error.message}`);
    }
  });

  const maintenanceTasks = [
    {
      id: 'cleanup',
      name: 'System Cleanup',
      description: 'Remove temporary files and clear caches',
      icon: TrashIcon,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      id: 'optimize',
      name: 'System Optimization',
      description: 'Optimize data structures and performance',
      icon: ArrowPathIcon,
      color: 'text-green-600',
      bgColor: 'bg-green-100'
    },
    {
      id: 'check_integrity',
      name: 'Data Integrity Check',
      description: 'Verify data consistency and repair issues',
      icon: MagnifyingGlassIcon,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100'
    },
    {
      id: 'update_dependencies',
      name: 'Update Dependencies',
      description: 'Check and recommend dependency updates',
      icon: ArrowUpIcon,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100'
    }
  ];

  const handleRunTask = (taskId: string) => {
    setSelectedTask(taskId);
    maintenanceMutation.mutate(taskId);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">System Maintenance</h2>
        <p className="mt-2 text-sm text-gray-600">
          Perform routine maintenance tasks to keep your system running optimally.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {maintenanceTasks.map((task) => {
          const Icon = task.icon;
          const isRunning = maintenanceMutation.isLoading && selectedTask === task.id;

          return (
            <Card key={task.id} className="p-6">
              <div className="flex items-start space-x-4">
                <div className={`p-3 rounded-lg ${task.bgColor}`}>
                  <Icon className={`w-6 h-6 ${task.color}`} />
                </div>
                
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900">
                    {task.name}
                  </h3>
                  <p className="mt-1 text-sm text-gray-600">
                    {task.description}
                  </p>
                  
                  <div className="mt-4">
                    <Button
                      onClick={() => handleRunTask(task.id)}
                      loading={isRunning}
                      disabled={maintenanceMutation.isLoading && selectedTask !== task.id}
                      size="sm"
                    >
                      {isRunning ? 'Running...' : 'Run Task'}
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Recent Maintenance History */}
      <Card className="p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Maintenance Activity</h3>
        <div className="text-sm text-gray-500">
          <p>Maintenance history will be displayed here once tasks are completed.</p>
          <p className="mt-2">
            For detailed logs, check the System Logs tab or the logs directory on the server.
          </p>
        </div>
      </Card>
    </div>
  );
};

export default MaintenancePanel;
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CogIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import { systemAPI } from '../../services/systemAPI';
import Card from '../ui/Card';
import Button from '../ui/Button';
import LoadingSpinner from '../ui/LoadingSpinner';

const ConfigurationPanel: React.FC = () => {
  const queryClient = useQueryClient();
  const [editMode, setEditMode] = useState(false);
  const [configData, setConfigData] = useState<any>({});

  const { data: config, isLoading } = useQuery({
    queryKey: ['system', 'configuration'],
    queryFn: systemAPI.getConfiguration,
    onSuccess: (data) => {
      setConfigData(data.data);
    }
  });

  const updateConfigMutation = useMutation({
    mutationFn: (newConfig: any) => systemAPI.updateConfiguration(newConfig),
    onSuccess: () => {
      toast.success('Configuration updated successfully');
      setEditMode(false);
      queryClient.invalidateQueries(['system', 'configuration']);
    },
    onError: (error: any) => {
      toast.error(`Failed to update configuration: ${error.message}`);
    }
  });

  const handleSave = () => {
    updateConfigMutation.mutate({ configuration: configData });
  };

  const handleCancel = () => {
    setConfigData(config?.data || {});
    setEditMode(false);
  };

  const handleInputChange = (section: string, key: string, value: any) => {
    setConfigData((prev: any) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
  };

  if (isLoading) return <LoadingSpinner />;

  const configSections = [
    {
      title: 'System Settings',
      key: 'system',
      icon: CogIcon,
      fields: [
        { key: 'data_directory', label: 'Data Directory', type: 'text' },
        { key: 'log_level', label: 'Log Level', type: 'select', options: ['DEBUG', 'INFO', 'WARNING', 'ERROR'] },
        { key: 'batch_size', label: 'Default Batch Size', type: 'number', min: 1, max: 1000 },
        { key: 'max_workers', label: 'Max Workers', type: 'number', min: 1, max: 16 }
      ]
    },
    {
      title: 'AI Configuration',
      key: 'ai',
      icon: CogIcon,
      fields: [
        { key: 'openai_model', label: 'OpenAI Model', type: 'select', options: ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'] },
        { key: 'confidence_threshold', label: 'Confidence Threshold', type: 'number', min: 0, max: 1, step: 0.1 },
        { key: 'analysis_enabled', label: 'AI Analysis Enabled', type: 'boolean' }
      ]
    },
    {
      title: 'Web Interface',
      key: 'web',
      icon: CogIcon,
      fields: [
        { key: 'host', label: 'Host', type: 'text', readonly: true }, // Internal network only
        { key: 'port', label: 'Port', type: 'number', min: 1024, max: 65535 },
        { key: 'auto_refresh_interval', label: 'Auto Refresh (seconds)', type: 'number', min: 5, max: 300 }
      ]
    },
    {
      title: 'Security',
      key: 'security',
      icon: CogIcon,
      fields: [
        { key: 'session_timeout', label: 'Session Timeout (seconds)', type: 'number', min: 300, max: 86400 },
        { key: 'max_login_attempts', label: 'Max Login Attempts', type: 'number', min: 3, max: 100 }
      ]
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">System Configuration</h2>
        <div className="flex space-x-3">
          {editMode ? (
            <>
              <Button
                variant="outline"
                onClick={handleCancel}
              >
                <XMarkIcon className="w-4 h-4 mr-2" />
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                loading={updateConfigMutation.isLoading}
              >
                <CheckIcon className="w-4 h-4 mr-2" />
                Save Changes
              </Button>
            </>
          ) : (
            <Button onClick={() => setEditMode(true)}>
              <CogIcon className="w-4 h-4 mr-2" />
              Edit Configuration
            </Button>
          )}
        </div>
      </div>

      {/* Configuration Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {configSections.map((section) => (
          <Card key={section.key} className="p-6">
            <div className="flex items-center space-x-3 mb-4">
              <section.icon className="w-5 h-5 text-indigo-600" />
              <h3 className="text-lg font-medium text-gray-900">{section.title}</h3>
            </div>

            <div className="space-y-4">
              {section.fields.map((field) => (
                <div key={field.key}>
                  <label className="block text-sm font-medium text-gray-700">
                    {field.label}
                  </label>
                  
                  {field.type === 'text' && (
                    <input
                      type="text"
                      value={configData[section.key]?.[field.key] || ''}
                      onChange={(e) => handleInputChange(section.key, field.key, e.target.value)}
                      disabled={!editMode || field.readonly}
                      className={`
                        mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm
                        ${!editMode || field.readonly ? 'bg-gray-50 text-gray-500' : ''}
                      `}
                    />
                  )}

                  {field.type === 'number' && (
                    <input
                      type="number"
                      value={configData[section.key]?.[field.key] || ''}
                      onChange={(e) => handleInputChange(section.key, field.key, parseFloat(e.target.value) || 0)}
                      disabled={!editMode}
                      min={field.min}
                      max={field.max}
                      step={field.step}
                      className={`
                        mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm
                        ${!editMode ? 'bg-gray-50 text-gray-500' : ''}
                      `}
                    />
                  )}

                  {field.type === 'select' && (
                    <select
                      value={configData[section.key]?.[field.key] || ''}
                      onChange={(e) => handleInputChange(section.key, field.key, e.target.value)}
                      disabled={!editMode}
                      className={`
                        mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm
                        ${!editMode ? 'bg-gray-50 text-gray-500' : ''}
                      `}
                    >
                      {field.options?.map((option) => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                  )}

                  {field.type === 'boolean' && (
                    <div className="mt-1">
                      <label className="inline-flex items-center">
                        <input
                          type="checkbox"
                          checked={configData[section.key]?.[field.key] || false}
                          onChange={(e) => handleInputChange(section.key, field.key, e.target.checked)}
                          disabled={!editMode}
                          className="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                        />
                        <span className="ml-2 text-sm text-gray-600">
                          {configData[section.key]?.[field.key] ? 'Enabled' : 'Disabled'}
                        </span>
                      </label>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>

      {/* Internal Network Notice */}
      <Card className="p-4 bg-blue-50 border-blue-200">
        <div className="flex items-center space-x-2">
          <div className="flex-shrink-0">
            <CogIcon className="w-5 h-5 text-blue-400" />
          </div>
          <div className="flex-1">
            <h4 className="text-sm font-medium text-blue-800">Internal Network Deployment</h4>
            <p className="text-sm text-blue-600">
              This system is configured for internal network use only. Security settings are optimized for trusted environments
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ConfigurationPanel;
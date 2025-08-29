import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  LightBulbIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

import { aiAPI } from '../../services/aiAPI';
import Card from '../ui/Card';
import LoadingSpinner from '../ui/LoadingSpinner';

const AnalysisResults: React.FC = () => {
  const { data: suggestions, isLoading } = useQuery({
    queryKey: ['ai', 'suggestions'],
    queryFn: () => aiAPI.getAISuggestions(),
    refetchInterval: 30000,
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'pending':
        return <ClockIcon className="w-5 h-5 text-yellow-500" />;
      case 'rejected':
        return <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <LightBulbIcon className="w-5 h-5 text-blue-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'text-green-700 bg-green-100';
      case 'pending':
        return 'text-yellow-700 bg-yellow-100';
      case 'rejected':
        return 'text-red-700 bg-red-100';
      default:
        return 'text-blue-700 bg-blue-100';
    }
  };

  if (isLoading) return <LoadingSpinner />;

  const suggestionsList = suggestions?.data || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">
          AI Suggestions ({suggestionsList.length})
        </h3>
      </div>

      {suggestionsList.length === 0 ? (
        <Card className="p-6 text-center">
          <LightBulbIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No AI Suggestions</h3>
          <p className="mt-1 text-sm text-gray-500">
            Run AI analysis on recent batches to generate suggestions.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {suggestionsList.map((suggestion, index) => (
            <Card key={suggestion.id || index} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  {getStatusIcon(suggestion.status)}
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-gray-900">
                      {suggestion.title || suggestion.type || 'AI Suggestion'}
                    </h4>
                    <p className="mt-1 text-sm text-gray-600">
                      {suggestion.description || suggestion.reasoning}
                    </p>
                    
                    {suggestion.pattern && (
                      <div className="mt-2 p-2 bg-gray-50 rounded text-xs font-mono">
                        Pattern: {suggestion.pattern}
                        {suggestion.replacement && (
                          <span> → {suggestion.replacement}</span>
                        )}
                      </div>
                    )}

                    {suggestion.examples && suggestion.examples.length > 0 && (
                      <div className="mt-2">
                        <span className="text-xs text-gray-500">Examples:</span>
                        <div className="mt-1 space-y-1">
                          {suggestion.examples.slice(0, 2).map((example, idx) => (
                            <div key={idx} className="text-xs bg-gray-100 p-1 rounded">
                              {example}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex flex-col items-end space-y-2">
                  <span className={`
                    inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium
                    ${getStatusColor(suggestion.status)}
                  `}>
                    {suggestion.status || 'pending'}
                  </span>
                  
                  {suggestion.confidence && (
                    <span className="text-xs text-gray-500">
                      {(suggestion.confidence * 100).toFixed(0)}% confidence
                    </span>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default AnalysisResults;
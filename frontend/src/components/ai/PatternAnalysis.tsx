import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  MagnifyingGlassIcon,
  ChartBarIcon,
  LightBulbIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

import { aiAPI } from '../../services/aiAPI';
import Card from '../ui/Card';
import LoadingSpinner from '../ui/LoadingSpinner';
import { PatternAnalysisResponse } from '../../types/ai';

interface PatternAnalysisProps {
  days?: number;
  patternType?: string;
  minConfidence?: number;
}

const PatternAnalysis: React.FC<PatternAnalysisProps> = ({
  days = 30,
  patternType,
  minConfidence = 0.6
}) => {
  const { data: patterns, isLoading, error } = useQuery({
    queryKey: ['ai', 'patterns', days, patternType, minConfidence],
    queryFn: () => aiAPI.getPatternAnalysis(days, patternType, minConfidence),
    refetchInterval: 60000, // Refetch every minute
  });

  const getPatternTypeIcon = (type: string) => {
    switch (type) {
      case 'company':
        return <MagnifyingGlassIcon className="w-5 h-5" />;
      case 'measurement':
        return <ChartBarIcon className="w-5 h-5" />;
      case 'material':
        return <LightBulbIcon className="w-5 h-5" />;
      default:
        return <ExclamationTriangleIcon className="w-5 h-5" />;
    }
  };

  const getPatternTypeColor = (type: string) => {
    switch (type) {
      case 'company':
        return 'text-blue-600 bg-blue-100';
      case 'measurement':
        return 'text-green-600 bg-green-100';
      case 'material':
        return 'text-purple-600 bg-purple-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.9) {
      return 'bg-green-100 text-green-800';
    } else if (confidence >= 0.7) {
      return 'bg-blue-100 text-blue-800';
    } else {
      return 'bg-yellow-100 text-yellow-800';
    }
  };

  if (isLoading) return <LoadingSpinner />;

  if (error) {
    return (
      <Card className="p-6">
        <div className="text-center">
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Error Loading Patterns</h3>
          <p className="mt-1 text-sm text-gray-500">
            Failed to load pattern analysis data.
          </p>
        </div>
      </Card>
    );
  }

  const patternsList = patterns?.data || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">
          Pattern Analysis ({patternsList.length} patterns found)
        </h3>
        <div className="text-sm text-gray-500">
          Last {days} days • Min confidence: {(minConfidence * 100).toFixed(0)}%
        </div>
      </div>

      {patternsList.length === 0 ? (
        <Card className="p-6 text-center">
          <MagnifyingGlassIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No Patterns Found</h3>
          <p className="mt-1 text-sm text-gray-500">
            No patterns meeting the confidence threshold were detected.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {patternsList.map((pattern: PatternAnalysisResponse) => (
            <Card key={pattern.pattern_id} className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${getPatternTypeColor(pattern.pattern_type)}`}>
                    {getPatternTypeIcon(pattern.pattern_type)}
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 capitalize">
                      {pattern.pattern_type} Pattern
                    </h4>
                    <p className="text-xs text-gray-500">
                      Found {pattern.frequency} times
                    </p>
                  </div>
                </div>
                <span className={`
                  inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium
                  ${getConfidenceBadge(pattern.confidence)}
                `}>
                  {(pattern.confidence * 100).toFixed(0)}% confidence
                </span>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700">Pattern</label>
                  <code className="block text-sm bg-gray-100 p-2 rounded font-mono mt-1">
                    {pattern.pattern}
                  </code>
                </div>

                {pattern.examples && pattern.examples.length > 0 && (
                  <div>
                    <label className="block text-xs font-medium text-gray-700">
                      Examples ({pattern.examples.length})
                    </label>
                    <div className="mt-1 space-y-1">
                      {pattern.examples.slice(0, 2).map((example, index) => (
                        <div key={index} className="text-xs bg-gray-50 p-2 rounded font-mono">
                          {example}
                        </div>
                      ))}
                      {pattern.examples.length > 2 && (
                        <p className="text-xs text-gray-500">
                          +{pattern.examples.length - 2} more examples
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {pattern.suggested_rule && (
                  <div>
                    <label className="block text-xs font-medium text-gray-700">
                      Suggested Rule
                    </label>
                    <div className="mt-1 p-2 bg-blue-50 rounded text-xs">
                      <p className="font-medium text-blue-900">
                        {pattern.suggested_rule.rule_type}: {pattern.suggested_rule.pattern}
                      </p>
                      <p className="text-blue-700">
                        → {pattern.suggested_rule.replacement}
                      </p>
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>Impact: {pattern.impact_assessment}</span>
                  <span>
                    Discovered: {new Date(pattern.discovered_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default PatternAnalysis;
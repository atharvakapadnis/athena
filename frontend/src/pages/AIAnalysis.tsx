import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  MagnifyingGlassIcon,
  ChartBarIcon,
  ChatBubbleBottomCenterTextIcon,
  CpuChipIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline';

import PatternAnalysis from '../components/ai/PatternAnalysis';
import FeedbackForm from '../components/ai/FeedbackForm';
import ConfidenceViewer from '../components/ai/ConfidenceViewer';
import AnalysisResults from '../components/ai/AnalysisResults';
import { aiAPI } from '../services/aiAPI';
import MetricsCard from '../components/dashboard/MetricsCard';

const AIAnalysis: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'patterns' | 'confidence' | 'feedback' | 'suggestions'>('patterns');
  const [analysisFilters, setAnalysisFilters] = useState({
    days: 30,
    patternType: undefined,
    minConfidence: 0.6
  });

  // Fetch AI statistics
  const { data: suggestions } = useQuery({
    queryKey: ['ai', 'suggestions'],
    queryFn: () => aiAPI.getAISuggestions(),
  });

  const { data: patterns } = useQuery({
    queryKey: ['ai', 'patterns', analysisFilters.days],
    queryFn: () => aiAPI.getPatternAnalysis(analysisFilters.days),
  });

  const suggestionsList = suggestions?.data || [];
  const patternsList = patterns?.data || [];

  const tabs = [
    { id: 'patterns', name: 'Pattern Analysis', count: patternsList.length, icon: MagnifyingGlassIcon },
    { id: 'confidence', name: 'Confidence Analysis', icon: ChartBarIcon },
    { id: 'suggestions', name: 'AI Suggestions', count: suggestionsList.length, icon: LightBulbIcon },
    { id: 'feedback', name: 'Submit Feedback', icon: ChatBubbleBottomCenterTextIcon },
  ];

  const highConfidencePatterns = patternsList.filter(p => p.confidence >= 0.8).length;
  const pendingSuggestions = suggestionsList.filter(s => s.status === 'pending').length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-gray-200 pb-4">
        <div className="flex items-center space-x-3">
          <CpuChipIcon className="w-8 h-8 text-indigo-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">AI Analysis</h1>
            <p className="mt-2 text-sm text-gray-600">
              AI-powered insights and pattern analysis for continuous improvement
            </p>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricsCard
          title="Patterns Detected"
          value={patternsList.length}
          description={`${highConfidencePatterns} high confidence`}
          changeType={highConfidencePatterns > 0 ? 'increase' : 'neutral'}
        />
        <MetricsCard
          title="AI Suggestions"
          value={suggestionsList.length}
          description={`${pendingSuggestions} pending review`}
          changeType="increase"
        />
        <MetricsCard
          title="Avg Confidence"
          value={`${((patternsList.reduce((sum, p) => sum + p.confidence, 0) / patternsList.length) * 100 || 0).toFixed(1)}%`}
          description="Pattern confidence score"
          change={2.3}
          changeType="increase"
        />
        <MetricsCard
          title="Feedback Items"
          value="47"
          description="This month"
          change={15.2}
          changeType="increase"
        />
      </div>

      {/* Analysis Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Analysis Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-700">Time Period</label>
            <select
              value={analysisFilters.days}
              onChange={(e) => setAnalysisFilters(prev => ({ ...prev, days: parseInt(e.target.value) }))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700">Pattern Type</label>
            <select
              value={analysisFilters.patternType || ''}
              onChange={(e) => setAnalysisFilters(prev => ({ ...prev, patternType: e.target.value || undefined }))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            >
              <option value="">All Types</option>
              <option value="company">Company Names</option>
              <option value="measurement">Measurements</option>
              <option value="material">Materials</option>
              <option value="formatting">Formatting</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700">Min Confidence</label>
            <select
              value={analysisFilters.minConfidence}
              onChange={(e) => setAnalysisFilters(prev => ({ ...prev, minConfidence: parseFloat(e.target.value) }))}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            >
              <option value={0.3}>30%+</option>
              <option value={0.5}>50%+</option>
              <option value={0.6}>60%+</option>
              <option value={0.8}>80%+</option>
            </select>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`
                  flex items-center py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap
                  ${activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon className="w-4 h-4 mr-2" />
                {tab.name}
                {tab.count !== undefined && (
                  <span className={`
                    ml-2 py-0.5 px-2 rounded-full text-xs font-medium
                    ${activeTab === tab.id
                      ? 'bg-indigo-100 text-indigo-600'
                      : 'bg-gray-100 text-gray-600'
                    }
                  `}>
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-[500px]">
        {activeTab === 'patterns' && (
          <PatternAnalysis
            days={analysisFilters.days}
            patternType={analysisFilters.patternType}
            minConfidence={analysisFilters.minConfidence}
          />
        )}
        
        {activeTab === 'confidence' && (
          <ConfidenceViewer days={analysisFilters.days} />
        )}
        
        {activeTab === 'suggestions' && (
          <AnalysisResults />
        )}
        
        {activeTab === 'feedback' && (
          <div className="max-w-4xl">
            <FeedbackForm />
          </div>
        )}
      </div>
    </div>
  );
};

export default AIAnalysis;
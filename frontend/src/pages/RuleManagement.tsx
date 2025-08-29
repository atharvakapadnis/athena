import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  PlusIcon, 
  EyeIcon,
  ChartBarIcon,
  ClipboardDocumentListIcon
} from '@heroicons/react/24/outline';

import RuleReview from '../components/rules/RuleReview';
import RuleEditor from '../components/rules/RuleEditor';
import RuleHistory from '../components/rules/RuleHistory';
import RulePerformance from '../components/rules/RulePerformance';
import { ruleAPI } from '../services/ruleAPI';
import Button from '../components/ui/Button';
import MetricsCard from '../components/dashboard/MetricsCard';

const RuleManagement: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'review' | 'active' | 'performance' | 'history'>('review');
  const [showRuleEditor, setShowRuleEditor] = useState(false);

  // Fetch rule statistics
  const { data: suggestions } = useQuery({
    queryKey: ['rules', 'suggestions'],
    queryFn: ruleAPI.getPendingSuggestions,
  });

  const { data: activeRules } = useQuery({
    queryKey: ['rules', 'active'],
    queryFn: ruleAPI.getActiveRules,
  });

  const suggestionsList = suggestions?.data || [];
  const activeRulesList = activeRules?.data || [];

  const tabs = [
    { id: 'review', name: 'Rule Review', count: suggestionsList.length, icon: EyeIcon },
    { id: 'active', name: 'Active Rules', count: activeRulesList.length, icon: ClipboardDocumentListIcon },
    { id: 'performance', name: 'Performance', icon: ChartBarIcon },
    { id: 'history', name: 'History', icon: ClipboardDocumentListIcon },
  ];

  const highPrioritySuggestions = suggestionsList.filter(s => s.priority >= 8).length;
  const highConfidenceSuggestions = suggestionsList.filter(s => s.confidence >= 0.8).length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-start border-b border-gray-200 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Rule Management</h1>
          <p className="mt-2 text-sm text-gray-600">
            Review AI suggestions and manage active rules
          </p>
        </div>
        <Button onClick={() => setShowRuleEditor(true)}>
          <PlusIcon className="w-4 h-4 mr-2" />
          Create Manual Rule
        </Button>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricsCard
          title="Pending Suggestions"
          value={suggestionsList.length}
          description={`${highPrioritySuggestions} high priority`}
          changeType={highPrioritySuggestions > 0 ? 'increase' : 'neutral'}
        />
        <MetricsCard
          title="High Confidence"
          value={highConfidenceSuggestions}
          description={`${((highConfidenceSuggestions / suggestionsList.length) * 100 || 0).toFixed(1)}% of suggestions`}
          changeType="increase"
        />
        <MetricsCard
          title="Active Rules"
          value={activeRulesList.length}
          description="Currently in use"
        />
        <MetricsCard
          title="Avg Performance"
          value="94.2%"
          description="Rule success rate"
          change={2.1}
          changeType="increase"
        />
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
        {activeTab === 'review' && <RuleReview />}
        {activeTab === 'active' && (
          <div>
            {/* Active Rules component would go here */}
            <div className="text-center py-12">
              <ClipboardDocumentListIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">Active Rules View</h3>
              <p className="mt-1 text-sm text-gray-500">
                Component to be implemented in next iteration
              </p>
            </div>
          </div>
        )}
        {activeTab === 'performance' && <RulePerformance />}
        {activeTab === 'history' && <RuleHistory />}
      </div>

      {/* Rule Editor Modal */}
      <RuleEditor
        isOpen={showRuleEditor}
        onClose={() => setShowRuleEditor(false)}
      />
    </div>
  );
};

export default RuleManagement;
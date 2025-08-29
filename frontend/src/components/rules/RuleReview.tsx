import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
 CheckIcon, 
 XMarkIcon, 
 PencilIcon,
 ClockIcon,
 ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

import { ruleAPI } from '../../services/ruleAPI';
import { RuleSuggestionResponse, RuleDecisionRequest } from '../../types/rule';
import Button from '../ui/Button';
import Card from '../ui/Card';
import Modal from '../ui/Modal';
import LoadingSpinner from '../ui/LoadingSpinner';

const RuleReview: React.FC = () => {
 const queryClient = useQueryClient();
 const [selectedSuggestion, setSelectedSuggestion] = useState<RuleSuggestionResponse | null>(null);
 const [showDecisionModal, setShowDecisionModal] = useState(false);
 const [decisionData, setDecisionData] = useState<RuleDecisionRequest>({
   decision: 'approve',
   reasoning: '',
   modifications: {}
 });

 const { data: suggestions, isLoading } = useQuery({
   queryKey: ['rules', 'suggestions'],
   queryFn: ruleAPI.getPendingSuggestions,
   refetchInterval: 30000, // Refetch every 30 seconds
 });

 const decisionMutation = useMutation({
   mutationFn: ({ suggestionId, decision }: { suggestionId: string, decision: RuleDecisionRequest }) =>
     ruleAPI.makeRuleDecision(suggestionId, decision),
   onSuccess: (data, variables) => {
     const action = variables.decision.decision;
     toast.success(`Rule suggestion ${action}d successfully`);
     queryClient.invalidateQueries(['rules']);
     setShowDecisionModal(false);
     setSelectedSuggestion(null);
   },
   onError: (error: any) => {
     toast.error(`Failed to process decision: ${error.message}`);
   }
 });

 const getPriorityBadge = (priority: number) => {
   if (priority >= 8) {
     return (
       <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">
         High Priority
       </span>
     );
   } else if (priority >= 5) {
     return (
       <span className="inline-flex items-center rounded-full bg-yellow-100 px-2.5 py-0.5 text-xs font-medium text-yellow-800">
         Medium Priority
       </span>
     );
   } else {
     return (
       <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
         Low Priority
       </span>
     );
   }
 };

 const getConfidenceBadge = (confidence: number) => {
   if (confidence >= 0.8) {
     return (
       <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
         High Confidence
       </span>
     );
   } else if (confidence >= 0.6) {
     return (
       <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
         Medium Confidence
       </span>
     );
   } else {
     return (
       <span className="inline-flex items-center rounded-full bg-orange-100 px-2.5 py-0.5 text-xs font-medium text-orange-800">
         Low Confidence
       </span>
     );
   }
 };

 const handleQuickDecision = (suggestion: RuleSuggestionResponse, decision: 'approve' | 'reject') => {
   const decisionRequest: RuleDecisionRequest = {
     decision,
     reasoning: decision === 'approve' ? 'Quick approval' : 'Quick rejection',
     modifications: {}
   };

   decisionMutation.mutate({
     suggestionId: suggestion.id,
     decision: decisionRequest
   });
 };

 const handleDetailedReview = (suggestion: RuleSuggestionResponse) => {
   setSelectedSuggestion(suggestion);
   setDecisionData({
     decision: 'approve',
     reasoning: '',
     modifications: {}
   });
   setShowDecisionModal(true);
 };

 const handleSubmitDecision = () => {
   if (!selectedSuggestion) return;

   decisionMutation.mutate({
     suggestionId: selectedSuggestion.id,
     decision: decisionData
   });
 };

 if (isLoading) {
   return <LoadingSpinner />;
 }

 const suggestionList = suggestions?.data || [];

 return (
   <div className="space-y-6">
     <div className="flex justify-between items-center">
       <h2 className="text-lg font-medium text-gray-900">
         Pending Rule Suggestions ({suggestionList.length})
       </h2>
       {suggestionList.length > 0 && (
         <div className="text-sm text-gray-500">
           {suggestionList.filter(s => s.priority >= 8).length} high priority suggestions
         </div>
       )}
     </div>

     {suggestionList.length === 0 ? (
       <Card className="text-center py-12">
         <ClockIcon className="mx-auto h-12 w-12 text-gray-400" />
         <h3 className="mt-2 text-sm font-medium text-gray-900">No pending suggestions</h3>
         <p className="mt-1 text-sm text-gray-500">
           All AI-generated rule suggestions have been reviewed.
         </p>
       </Card>
     ) : (
       <div className="space-y-4">
         {suggestionList.map((suggestion) => (
           <Card key={suggestion.id} className="p-6">
             <div className="flex items-start justify-between">
               <div className="flex-1 min-w-0">
                 {/* Header */}
                 <div className="flex items-center space-x-3 mb-3">
                   <h3 className="text-lg font-medium text-gray-900">
                     {suggestion.rule_type.charAt(0).toUpperCase() + suggestion.rule_type.slice(1)} Rule
                   </h3>
                   {getPriorityBadge(suggestion.priority)}
                   {getConfidenceBadge(suggestion.confidence)}
                 </div>

                 {/* Rule Details */}
                 <div className="bg-gray-50 rounded-lg p-4 mb-4">
                   <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                     <div>
                       <label className="block text-sm font-medium text-gray-700 mb-1">
                         Pattern
                       </label>
                       <code className="block text-sm bg-white border rounded px-2 py-1 font-mono">
                         {suggestion.pattern}
                       </code>
                     </div>
                     <div>
                       <label className="block text-sm font-medium text-gray-700 mb-1">
                         Replacement
                       </label>
                       <code className="block text-sm bg-white border rounded px-2 py-1 font-mono">
                         {suggestion.replacement}
                       </code>
                     </div>
                   </div>
                 </div>

                 {/* AI Reasoning */}
                 <div className="mb-4">
                   <label className="block text-sm font-medium text-gray-700 mb-2">
                     AI Reasoning
                   </label>
                   <p className="text-sm text-gray-600 bg-blue-50 p-3 rounded-lg">
                     {suggestion.reasoning}
                   </p>
                 </div>

                 {/* Examples */}
                 {suggestion.examples && suggestion.examples.length > 0 && (
                   <div className="mb-4">
                     <label className="block text-sm font-medium text-gray-700 mb-2">
                       Examples ({suggestion.examples.length})
                     </label>
                     <div className="space-y-2">
                       {suggestion.examples.slice(0, 3).map((example, index) => (
                         <div key={index} className="text-sm bg-gray-100 p-2 rounded font-mono">
                           {example}
                         </div>
                       ))}
                       {suggestion.examples.length > 3 && (
                         <p className="text-xs text-gray-500">
                           +{suggestion.examples.length - 3} more examples
                         </p>
                       )}
                     </div>
                   </div>
                 )}

                 {/* Metadata */}
                 <div className="flex items-center space-x-6 text-xs text-gray-500">
                   <span>Confidence: {(suggestion.confidence * 100).toFixed(1)}%</span>
                   <span>Priority: {suggestion.priority}/10</span>
                   <span>Created: {new Date(suggestion.timestamp).toLocaleString()}</span>
                 </div>
               </div>

               {/* Action Buttons */}
               <div className="flex flex-col space-y-2 ml-6">
                 <Button
                   size="sm"
                   onClick={() => handleQuickDecision(suggestion, 'approve')}
                   loading={decisionMutation.isLoading}
                   className="bg-green-600 hover:bg-green-700"
                 >
                   <CheckIcon className="w-4 h-4 mr-1" />
                   Approve
                 </Button>
                 
                 <Button
                   size="sm"
                   variant="outline"
                   onClick={() => handleDetailedReview(suggestion)}
                 >
                   <PencilIcon className="w-4 h-4 mr-1" />
                   Review
                 </Button>
                 
                 <Button
                   size="sm"
                   variant="outline"
                   onClick={() => handleQuickDecision(suggestion, 'reject')}
                   loading={decisionMutation.isLoading}
                   className="text-red-600 border-red-300 hover:bg-red-50"
                 >
                   <XMarkIcon className="w-4 h-4 mr-1" />
                   Reject
                 </Button>
               </div>
             </div>
           </Card>
         ))}
       </div>
     )}

     {/* Detailed Review Modal */}
     <Modal
       isOpen={showDecisionModal}
       onClose={() => setShowDecisionModal(false)}
       title={`Review Rule Suggestion`}
     >
       {selectedSuggestion && (
         <div className="space-y-6">
           {/* Rule Summary */}
           <div className="bg-gray-50 p-4 rounded-lg">
             <h4 className="font-medium text-gray-900 mb-2">Rule Summary</h4>
             <div className="text-sm text-gray-600">
               <p><span className="font-medium">Type:</span> {selectedSuggestion.rule_type}</p>
               <p><span className="font-medium">Pattern:</span> <code>{selectedSuggestion.pattern}</code></p>
               <p><span className="font-medium">Replacement:</span> <code>{selectedSuggestion.replacement}</code></p>
               <p><span className="font-medium">Confidence:</span> {(selectedSuggestion.confidence * 100).toFixed(1)}%</p>
             </div>
           </div>

           {/* Decision */}
           <div>
             <label className="block text-sm font-medium text-gray-700 mb-2">
               Decision
             </label>
             <div className="space-y-2">
               <label className="flex items-center">
                 <input
                   type="radio"
                   name="decision"
                   value="approve"
                   checked={decisionData.decision === 'approve'}
                   onChange={(e) => setDecisionData(prev => ({ ...prev, decision: e.target.value as any }))}
                   className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                 />
                 <span className="ml-2 text-sm text-gray-700">Approve as-is</span>
               </label>
               <label className="flex items-center">
                 <input
                   type="radio"
                   name="decision"
                   value="modify"
                   checked={decisionData.decision === 'modify'}
                   onChange={(e) => setDecisionData(prev => ({ ...prev, decision: e.target.value as any }))}
                   className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                 />
                 <span className="ml-2 text-sm text-gray-700">Approve with modifications</span>
               </label>
               <label className="flex items-center">
                 <input
                   type="radio"
                   name="decision"
                   value="reject"
                   checked={decisionData.decision === 'reject'}
                   onChange={(e) => setDecisionData(prev => ({ ...prev, decision: e.target.value as any }))}
                   className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                 />
                 <span className="ml-2 text-sm text-gray-700">Reject</span>
               </label>
             </div>
           </div>

           {/* Modifications (if modify selected) */}
           {decisionData.decision === 'modify' && (
             <div className="space-y-4">
               <div>
                 <label className="block text-sm font-medium text-gray-700">
                   Modified Pattern
                 </label>
                 <input
                   type="text"
                   defaultValue={selectedSuggestion.pattern}
                   onChange={(e) => setDecisionData(prev => ({
                     ...prev,
                     modifications: { ...prev.modifications, pattern: e.target.value }
                   }))}
                   className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm font-mono"
                 />
               </div>
               <div>
                 <label className="block text-sm font-medium text-gray-700">
                   Modified Replacement
                 </label>
                 <input
                   type="text"
                   defaultValue={selectedSuggestion.replacement}
                   onChange={(e) => setDecisionData(prev => ({
                     ...prev,
                     modifications: { ...prev.modifications, replacement: e.target.value }
                   }))}
                   className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm font-mono"
                 />
               </div>
             </div>
           )}

           {/* Reasoning */}
           <div>
             <label className="block text-sm font-medium text-gray-700">
               Reasoning for Decision
             </label>
             <textarea
               value={decisionData.reasoning}
               onChange={(e) => setDecisionData(prev => ({ ...prev, reasoning: e.target.value }))}
               rows={3}
               className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
               placeholder="Explain your decision..."
             />
           </div>

           {/* Action Buttons */}
           <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
             <Button
               variant="outline"
               onClick={() => setShowDecisionModal(false)}
             >
               Cancel
             </Button>
             <Button
               onClick={handleSubmitDecision}
               loading={decisionMutation.isLoading}
               disabled={!decisionData.reasoning.trim()}
             >
               Submit Decision
             </Button>
           </div>
         </div>
       )}
     </Modal>
   </div>
 );
};

export default RuleReview;
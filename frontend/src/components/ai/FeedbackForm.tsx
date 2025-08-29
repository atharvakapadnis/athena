import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import { aiAPI } from '../../services/aiAPI';
import { FeedbackRequest } from '../../types/ai';
import Button from '../ui/Button';
import Card from '../ui/Card';

interface FeedbackFormProps {
  productId?: string;
  originalDescription?: string;
  generatedDescription?: string;
  onSubmit?: () => void;
}

const FeedbackForm: React.FC<FeedbackFormProps> = ({
  productId = '',
  originalDescription = '',
  generatedDescription = '',
  onSubmit
}) => {
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState<FeedbackRequest>({
    product_id: productId,
    original_description: originalDescription,
    generated_description: generatedDescription,
    feedback_text: '',
    rating: 3,
    feedback_type: 'quality',
    suggestions: ''
  });

  const submitFeedback = useMutation({
    mutationFn: (feedback: FeedbackRequest) => aiAPI.submitFeedback(feedback),
    onSuccess: () => {
      toast.success('Feedback submitted successfully!');
      queryClient.invalidateQueries(['ai']);

      // Reset form
      setFormData({
        ...formData,
        feedback_text: '',
        suggestions: '',
        rating: 3
      });

      onSubmit?.();
    },
    onError: (error: any) => {
      toast.error(`Failed to submit feedback: ${error.message}`);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    submitFeedback.mutate(formData);
  };

  const handleInputChange = (field: keyof FeedbackRequest, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Card className="p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Submit Feedback</h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Product Context */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Product ID
            </label>
            <input
              type="text"
              value={formData.product_id}
              onChange={(e) => handleInputChange('product_id', e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="Enter product ID..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Feedback Type
            </label>
            <select
              value={formData.feedback_type}
              onChange={(e) => handleInputChange('feedback_type', e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
              <option value="quality">Quality</option>
              <option value="accuracy">Accuracy</option>
              <option value="completeness">Completeness</option>
              <option value="formatting">Formatting</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>

        {/* Description Context */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Original Description
            </label>
            <textarea
              value={formData.original_description}
              onChange={(e) => handleInputChange('original_description', e.target.value)}
              rows={2}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="Original product description..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Generated Description
            </label>
            <textarea
              value={formData.generated_description}
              onChange={(e) => handleInputChange('generated_description', e.target.value)}
              rows={2}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="AI-generated description..."
            />
          </div>
        </div>

        {/* Rating */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Rating (1-5 stars)
          </label>
          <div className="flex items-center space-x-1">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => handleInputChange('rating', star)}
                className={`
                  p-1 rounded-full transition-colors
                  ${star <= formData.rating
                    ? 'text-yellow-400 hover:text-yellow-500'
                    : 'text-gray-300 hover:text-gray-400'
                  }
                `}
              >
                <svg className="w-6 h-6 fill-current" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </button>
            ))}
            <span className="ml-2 text-sm text-gray-600">
              {formData.rating}/5 stars
            </span>
          </div>
        </div>

        {/* Feedback Text */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Detailed Feedback
          </label>
          <textarea
            value={formData.feedback_text}
            onChange={(e) => handleInputChange('feedback_text', e.target.value)}
            rows={4}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="Please provide detailed feedback about the generated description..."
            required
          />
        </div>

        {/* Suggestions */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Improvement Suggestions (Optional)
          </label>
          <textarea
            value={formData.suggestions}
            onChange={(e) => handleInputChange('suggestions', e.target.value)}
            rows={3}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            placeholder="What specific improvements would you suggest?"
          />
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <Button
            type="submit"
            loading={submitFeedback.isLoading}
            disabled={!formData.feedback_text.trim()}
          >
            Submit Feedback
          </Button>
        </div>
      </form>
    </Card>
  );
};

export default FeedbackForm;

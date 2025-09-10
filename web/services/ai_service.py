from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import json

# Import existing AI analysis functionality
from src.ai_analysis.analysis_aggregator import AnalysisAggregator
from src.ai_analysis.pattern_analyzer import PatternAnalyzer
from src.ai_analysis.rule_suggester import RuleSuggester
from src.ai_analysis.ai_client import AIClient
from src.batch_processor.feedback_loop import FeedbackLoopManager
from src.utils.config import get_project_settings

from ..models.ai import (
    AnalysisResponse, PatternAnalysisResponse, ConfidenceAnalysisResponse,
    FeedbackResponse
)

class AIService:
    """Service layer for AI analysis operations"""
    
    def __init__(self):
        self.settings = get_project_settings()
        self.data_dir = self.settings.get('data_dir', 'data')
        
        # Initialize existing AI components
        try:
            self.ai_client = AIClient()
        except Exception:
            # Use mock client if API key not available
            self.ai_client = None
            
        self.pattern_analyzer = PatternAnalyzer()
        self.rule_suggester = RuleSuggester(self.ai_client) if self.ai_client else None
        self.analysis_aggregator = AnalysisAggregator(
            self.pattern_analyzer, self.rule_suggester
        ) if self.rule_suggester else None
        self.feedback_manager = FeedbackLoopManager(self.data_dir)
        
        # Cache for performance
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    async def analyze_batch(self, batch_id: str, analysis_types: List[str], user_id: str) -> AnalysisResponse:
        """Perform AI analysis on a batch"""
        try:
            analysis_results = {}
            
            # Pattern Analysis
            if 'patterns' in analysis_types:
                patterns = await self._analyze_patterns(batch_id)
                analysis_results['patterns'] = patterns
            
            # Quality Analysis
            if 'quality' in analysis_types:
                quality = await self._analyze_quality(batch_id)
                analysis_results['quality'] = quality
            
            # Suggestions
            if 'suggestions' in analysis_types and self.rule_suggester:
                suggestions = await self._generate_suggestions(batch_id)
                analysis_results['suggestions'] = suggestions
            
            return AnalysisResponse(
                analysis_id=f"analysis_{batch_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                batch_id=batch_id,
                analysis_types=analysis_types,
                results=analysis_results,
                confidence_score=self._calculate_overall_confidence(analysis_results),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                status="completed"
            )
            
        except Exception as e:
            return AnalysisResponse(
                analysis_id=f"analysis_{batch_id}_failed",
                batch_id=batch_id,
                analysis_types=analysis_types,
                results={},
                confidence_score=0.0,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                status="failed",
                error_message=str(e)
            )

    async def get_pattern_analysis(self, days: int, pattern_type: Optional[str], min_confidence: float) -> List[PatternAnalysisResponse]:
        """Get pattern analysis results"""
        cache_key = f"patterns_{days}_{pattern_type}_{min_confidence}"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]['data']
        
        # Use existing pattern analyzer
        patterns = self.pattern_analyzer.analyze_recent_patterns(
            days_back=days,
            pattern_type=pattern_type,
            min_confidence=min_confidence
        )
        
        # Convert to API response format
        pattern_responses = []
        for pattern in patterns:
            pattern_responses.append(PatternAnalysisResponse(
                pattern_id=pattern.get('id', f"pattern_{len(pattern_responses)}"),
                pattern_type=pattern.get('type', 'unknown'),
                pattern=pattern.get('pattern', ''),
                frequency=pattern.get('frequency', 0),
                confidence=pattern.get('confidence', 0.0),
                examples=pattern.get('examples', []),
                suggested_rule=pattern.get('suggested_rule'),
                impact_assessment=pattern.get('impact_assessment', 'Medium'),
                discovered_at=pattern.get('discovered_at', datetime.utcnow().isoformat())
            ))
        
        # Cache results
        self._cache[cache_key] = {
            'data': pattern_responses,
            'timestamp': datetime.utcnow()
        }
        
        return pattern_responses

    async def get_confidence_analysis(self, batch_id: Optional[str], days: int) -> ConfidenceAnalysisResponse:
        """Get detailed confidence analysis"""
        # Implementation using existing confidence scoring system
        from src.confidence_scoring import ConfidenceScoringSystem
        
        confidence_system = ConfidenceScoringSystem()
        
        if batch_id:
            # Analysis for specific batch
            analysis = confidence_system.analyze_batch_confidence(batch_id)
        else:
            # Analysis for recent batches
            analysis = confidence_system.analyze_recent_confidence(days)
        
        return ConfidenceAnalysisResponse(
            analysis_id=f"conf_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            batch_id=batch_id,
            time_period_days=days,
            overall_confidence=analysis.get('overall_confidence', 0.0),
            confidence_distribution=analysis.get('distribution', {}),
            confidence_trends=analysis.get('trends', []),
            low_confidence_patterns=analysis.get('low_confidence_patterns', []),
            improvement_suggestions=analysis.get('suggestions', []),
            generated_at=datetime.utcnow()
        )

    async def submit_feedback(self, feedback, user_id: str) -> FeedbackResponse:
        """Submit manual feedback"""
        # Use existing feedback manager
        feedback_item = self.feedback_manager.create_feedback_item(
            product_id=feedback.product_id,
            original_description=feedback.original_description,
            generated_description=feedback.generated_description,
            user_feedback=feedback.feedback_text,
            rating=feedback.rating,
            user_id=user_id
        )
        
        # Process the feedback
        processing_result = self.feedback_manager.process_feedback_item(feedback_item)
        
        return FeedbackResponse(
            feedback_id=feedback_item.get('id'),
            status="processed",
            processing_result=processing_result,
            message="Feedback submitted and processed successfully"
        )

    # async def get_ai_suggestions(self, batch_id: Optional[str], status: Optional[str], confidence_threshold: float) -> List[Dict]:
    #     """Get AI suggestions"""
    #     if not self.rule_suggester:
    #         return []
        
    #     suggestions = self.rule_suggester.get_suggestions(
    #         batch_id=batch_id,
    #         status=status,
    #         min_confidence=confidence_threshold
    #     )
        
    #     return suggestions

    # async def get_analysis_history(self, page: int, page_size: int, analysis_type: Optional[str]):
    #     """Get analysis history"""
    #     # Implementation would query analysis history from storage
    #     # For now, return mock data structure
    #     analyses = []
        
    #     # This would be replaced with actual database/file queries
    #     mock_analyses = [
    #         {
    #             'analysis_id': f'analysis_{i}',
    #             'batch_id': f'batch_{i}',
    #             'analysis_type': analysis_type or 'patterns',
    #             'confidence': 0.85 + (i * 0.02),
    #             'created_at': (datetime.utcnow() - timedelta(days=i)).isoformat(),
    #             'status': 'completed'
    #         }
    #         for i in range(10)
    #     ]
        
    #     # Apply pagination
    #     start_idx = (page - 1) * page_size
    #     end_idx = start_idx + page_size
    #     paginated_analyses = mock_analyses[start_idx:end_idx]
        
    #     return {
    #         'items': paginated_analyses,
    #         'total': len(mock_analyses),
    #         'page': page,
    #         'page_size': page_size,
    #         'total_pages': (len(mock_analyses) + page_size - 1) // page_size,
    #         'has_next': end_idx < len(mock_analyses),
    #         'has_previous': page > 1
    #     }

    # Helper methods
    async def _analyze_patterns(self, batch_id: str) -> Dict:
        """Analyze patterns for a specific batch"""
        patterns = self.pattern_analyzer.analyze_batch_patterns(batch_id)
        return {
            'total_patterns': len(patterns),
            'high_confidence_patterns': len([p for p in patterns if p.get('confidence', 0) > 0.8]),
            'pattern_types': list(set([p.get('type') for p in patterns])),
            'patterns': patterns[:10]  # Top 10 patterns
        }

    async def _analyze_quality(self, batch_id: str) -> Dict:
        """Analyze quality for a specific batch"""
        # This would use existing quality analysis components
        return {
            'overall_quality_score': 0.85,
            'quality_issues': [
                {'type': 'inconsistent_formatting', 'frequency': 12, 'severity': 'medium'},
                {'type': 'missing_details', 'frequency': 8, 'severity': 'high'}
            ],
            'improvement_potential': 0.15,
            'recommendations': [
                'Standardize measurement units',
                'Add material specifications'
            ]
        }

    async def _generate_suggestions(self, batch_id: str) -> List[Dict]:
        """Generate AI suggestions for improvement"""
        if not self.rule_suggester:
            return []
        
        suggestions = self.rule_suggester.generate_batch_suggestions(batch_id)
        return suggestions

    def _calculate_overall_confidence(self, results: Dict) -> float:
        """Calculate overall confidence from analysis results"""
        confidences = []
        
        for analysis_type, result in results.items():
            if isinstance(result, dict) and 'confidence' in result:
                confidences.append(result['confidence'])
            elif isinstance(result, list):
                for item in result:
                    if isinstance(item, dict) and 'confidence' in item:
                        confidences.append(item['confidence'])
        
        return sum(confidences) / len(confidences) if confidences else 0.0

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid"""
        if key not in self._cache:
            return False
        
        cache_entry = self._cache[key]
        elapsed = (datetime.utcnow() - cache_entry['timestamp']).seconds
        return elapsed < self._cache_ttl
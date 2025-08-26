# src/batch_processor/scaling_predictor.py
import numpy as np
from typing import Dict, Tuple, List, Optional
from datetime import datetime, timedelta
import math

try:
    from ..utils.logger import get_logger
except ImportError:
    # Fallback for when running as script
    from utils.logger import get_logger

logger = get_logger(__name__)

class ScalingPredictor:
    """Predicts optimal batch sizes based on historical performance data"""
    
    def __init__(self):
        self.performance_history: List[Dict] = []
        self.min_batch_size = 10
        self.max_batch_size = 200
        
    def predict_optimal_batch_size(self, 
                                 current_performance: Dict,
                                 target_confidence_rate: float = 0.9,
                                 target_processing_time: float = 2.0) -> int:
        """Predict optimal batch size based on current performance and targets"""
        current_batch_size = current_performance.get('batch_size', 50)
        current_confidence_rate = current_performance.get('high_confidence_rate', 0.0)
        current_processing_time = current_performance.get('avg_processing_time', 0.0)
        stability_score = current_performance.get('stability_score', 1.0)
        
        logger.debug(f"Predicting optimal batch size - Current: {current_batch_size}, "
                    f"Confidence: {current_confidence_rate:.2f}, "
                    f"Time: {current_processing_time:.2f}s")
        
        # Calculate performance score (0.0 to 1.0)
        performance_score = self._calculate_performance_score(
            current_confidence_rate, current_processing_time, 
            target_confidence_rate, target_processing_time, stability_score
        )
        
        # Predict optimal size based on performance score
        if performance_score > 0.8:
            # Performance is excellent, can increase
            optimal_size = int(current_batch_size * 1.3)
        elif performance_score > 0.6:
            # Good performance, slight increase
            optimal_size = int(current_batch_size * 1.1)
        elif performance_score > 0.4:
            # Acceptable performance, maintain
            optimal_size = current_batch_size
        elif performance_score > 0.2:
            # Poor performance, decrease
            optimal_size = int(current_batch_size * 0.8)
        else:
            # Very poor performance, significant decrease
            optimal_size = int(current_batch_size * 0.6)
        
        # Apply constraints
        optimal_size = max(self.min_batch_size, min(optimal_size, self.max_batch_size))
        
        logger.debug(f"Predicted optimal batch size: {optimal_size} "
                    f"(performance score: {performance_score:.2f})")
        
        return optimal_size
    
    def should_scale_now(self, performance_trend: Dict, 
                        min_confidence_threshold: float = 0.8) -> Tuple[bool, str]:
        """Determine if scaling should happen now based on trends and stability"""
        trend_status = performance_trend.get('status', 'unknown')
        
        if trend_status == 'insufficient_data':
            return False, "Insufficient data for scaling decision"
        
        confidence_trend = performance_trend.get('confidence_trend', 'stable')
        time_trend = performance_trend.get('time_trend', 'stable')
        latest_confidence = performance_trend.get('latest_confidence_rate', 0.0)
        stability_score = performance_trend.get('stability_score', 1.0)
        
        # Don't scale if performance is unstable
        if stability_score < 0.6:
            return False, f"Performance too unstable (stability: {stability_score:.2f})"
        
        # Don't scale if confidence is critically low
        if latest_confidence < min_confidence_threshold * 0.5:
            return False, f"Confidence too low for scaling ({latest_confidence:.1%})"
        
        # Scale if there's a clear trend and system is stable
        if confidence_trend == 'improving' and time_trend in ['improving', 'stable'] and stability_score > 0.7:
            return True, "Improving performance trend with good stability"
        
        if confidence_trend == 'declining' or time_trend == 'declining':
            return True, "Declining performance requires adjustment"
        
        # For stable trends, scale less frequently
        if confidence_trend == 'stable' and time_trend == 'stable':
            # Only scale if performance is very good or very poor
            if latest_confidence > 0.95:
                return True, "Very high confidence allows for scaling up"
            elif latest_confidence < min_confidence_threshold * 0.7:
                return True, "Low confidence requires scaling down"
        
        return False, "No clear scaling trigger identified"
    
    def analyze_batch_size_efficiency(self, performance_data: List[Dict]) -> Dict:
        """Analyze efficiency of different batch sizes from historical data"""
        if not performance_data:
            return {'status': 'no_data'}
        
        # Group performance by batch size
        batch_size_performance = {}
        
        for data in performance_data:
            batch_size = data.get('batch_size', 50)
            if batch_size not in batch_size_performance:
                batch_size_performance[batch_size] = []
            
            batch_size_performance[batch_size].append({
                'confidence_rate': data.get('high_confidence_rate', 0.0),
                'processing_time': data.get('avg_processing_time', 0.0),
                'success_rate': data.get('success_rate', 0.0)
            })
        
        # Calculate average performance for each batch size
        efficiency_analysis = {}
        for batch_size, performances in batch_size_performance.items():
            if len(performances) >= 2:  # Need at least 2 data points
                avg_confidence = sum(p['confidence_rate'] for p in performances) / len(performances)
                avg_time = sum(p['processing_time'] for p in performances) / len(performances)
                avg_success = sum(p['success_rate'] for p in performances) / len(performances)
                
                # Calculate efficiency score (higher is better)
                efficiency_score = (avg_confidence * 0.5 + avg_success * 0.3) / max(avg_time, 0.1) * 0.2
                
                efficiency_analysis[batch_size] = {
                    'avg_confidence_rate': avg_confidence,
                    'avg_processing_time': avg_time,
                    'avg_success_rate': avg_success,
                    'efficiency_score': efficiency_score,
                    'sample_count': len(performances)
                }
        
        if not efficiency_analysis:
            return {'status': 'insufficient_data'}
        
        # Find most efficient batch size
        best_batch_size = max(efficiency_analysis.keys(), 
                             key=lambda x: efficiency_analysis[x]['efficiency_score'])
        
        return {
            'status': 'analyzed',
            'efficiency_by_batch_size': efficiency_analysis,
            'recommended_batch_size': best_batch_size,
            'best_efficiency_score': efficiency_analysis[best_batch_size]['efficiency_score']
        }
    
    def predict_processing_time(self, batch_size: int, 
                              recent_performance: Dict) -> float:
        """Predict processing time for a given batch size"""
        current_batch_size = recent_performance.get('batch_size', 50)
        current_time = recent_performance.get('avg_processing_time', 1.0)
        
        if current_batch_size <= 0:
            return batch_size * 0.02  # Fallback: 20ms per item
        
        # Assume linear relationship with some overhead
        time_per_item = current_time / current_batch_size
        overhead = current_time * 0.1  # 10% fixed overhead
        
        predicted_time = batch_size * time_per_item + overhead
        
        # Add complexity factor for larger batches
        if batch_size > current_batch_size * 1.5:
            complexity_factor = 1 + (batch_size / current_batch_size - 1) * 0.1
            predicted_time *= complexity_factor
        
        return max(predicted_time, 0.1)  # Minimum 0.1 seconds
    
    def get_scaling_recommendation(self, current_performance: Dict, 
                                 historical_data: List[Dict]) -> Dict:
        """Get comprehensive scaling recommendation"""
        current_batch_size = current_performance.get('batch_size', 50)
        
        # Get optimal batch size prediction
        optimal_size = self.predict_optimal_batch_size(current_performance)
        
        # Analyze historical efficiency
        efficiency_analysis = self.analyze_batch_size_efficiency(historical_data)
        
        # Predict processing time for optimal size
        predicted_time = self.predict_processing_time(optimal_size, current_performance)
        
        # Calculate confidence in recommendation
        confidence_score = self._calculate_recommendation_confidence(
            current_performance, optimal_size, historical_data
        )
        
        # Determine action
        if optimal_size > current_batch_size * 1.1:
            action = 'increase'
            reason = f"Performance allows scaling up to {optimal_size}"
        elif optimal_size < current_batch_size * 0.9:
            action = 'decrease'
            reason = f"Performance requires scaling down to {optimal_size}"
        else:
            action = 'maintain'
            reason = f"Current batch size {current_batch_size} is optimal"
        
        return {
            'action': action,
            'current_batch_size': current_batch_size,
            'recommended_batch_size': optimal_size,
            'predicted_processing_time': predicted_time,
            'confidence_score': confidence_score,
            'reason': reason,
            'efficiency_analysis': efficiency_analysis,
            'performance_score': self._calculate_performance_score(
                current_performance.get('high_confidence_rate', 0.0),
                current_performance.get('avg_processing_time', 0.0)
            )
        }
    
    def _calculate_performance_score(self, confidence_rate: float, processing_time: float,
                                   target_confidence: float = 0.9, 
                                   target_time: float = 2.0,
                                   stability_score: float = 1.0) -> float:
        """Calculate overall performance score (0.0 to 1.0)"""
        # Confidence score (0.0 to 1.0)
        confidence_score = min(confidence_rate / target_confidence, 1.0)
        
        # Time score (1.0 for times <= target, decreasing for higher times)
        if processing_time <= target_time:
            time_score = 1.0
        else:
            # Exponential decay for longer times
            time_score = max(0.1, math.exp(-(processing_time - target_time) / target_time))
        
        # Combine scores with weights
        performance_score = (confidence_score * 0.6 + time_score * 0.3 + stability_score * 0.1)
        
        return min(performance_score, 1.0)
    
    def _calculate_recommendation_confidence(self, current_performance: Dict,
                                          recommended_size: int,
                                          historical_data: List[Dict]) -> float:
        """Calculate confidence in the scaling recommendation"""
        current_batch_size = current_performance.get('batch_size', 50)
        
        # Base confidence on data availability
        confidence = min(len(historical_data) / 10.0, 1.0)  # Full confidence with 10+ data points
        
        # Reduce confidence for large changes
        size_change_ratio = abs(recommended_size - current_batch_size) / current_batch_size
        if size_change_ratio > 0.5:
            confidence *= 0.7  # Reduce confidence for >50% changes
        elif size_change_ratio > 0.2:
            confidence *= 0.9  # Slight reduction for >20% changes
        
        # Reduce confidence if current performance is poor
        current_confidence_rate = current_performance.get('high_confidence_rate', 0.0)
        if current_confidence_rate < 0.5:
            confidence *= 0.8
        
        return min(confidence, 1.0)

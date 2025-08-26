# src/batch_processor/dynamic_scaling_controller.py
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    from .scaling_manager import ScalingManager, ScalingConfig, ScalingDecision
    from .scaling_predictor import ScalingPredictor
    from .progress_tracker import ProgressTracker
    from .batch_manager import BatchManager
    from .processor import BatchResult
    from ..utils.logger import get_logger
except ImportError:
    # Fallback for when running as script
    from batch_processor.scaling_manager import ScalingManager, ScalingConfig, ScalingDecision
    from batch_processor.scaling_predictor import ScalingPredictor
    from batch_processor.progress_tracker import ProgressTracker
    from batch_processor.batch_manager import BatchManager
    from batch_processor.processor import BatchResult
    from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ScalingEvent:
    """Record of a scaling event"""
    timestamp: datetime
    previous_batch_size: int
    new_batch_size: int
    trigger_reason: str
    performance_metrics: Dict
    success: bool
    error_message: Optional[str] = None

class DynamicScalingController:
    """Central controller for dynamic batch size scaling"""
    
    def __init__(self, 
                 batch_manager: BatchManager,
                 progress_tracker: ProgressTracker,
                 scaling_config: Optional[ScalingConfig] = None,
                 data_dir: Optional[Path] = None):
        
        self.batch_manager = batch_manager
        self.progress_tracker = progress_tracker
        self.scaling_manager = ScalingManager(scaling_config, data_dir)
        self.scaling_predictor = ScalingPredictor()
        
        # Configuration
        self.enabled = True
        self.evaluation_frequency = 3  # Evaluate scaling every N batches
        self.batch_count_since_evaluation = 0
        
        # Event tracking
        self.scaling_events: List[ScalingEvent] = []
        
        logger.info("DynamicScalingController initialized with dynamic scaling enabled")
    
    def process_batch_completion(self, batch_result: BatchResult) -> bool:
        """Process completion of a batch and evaluate scaling if needed"""
        if not self.enabled:
            return False
        
        logger.debug(f"Processing batch completion for scaling evaluation: {batch_result.batch_id}")
        
        self.batch_count_since_evaluation += 1
        
        # Check if it's time to evaluate scaling
        if self.batch_count_since_evaluation >= self.evaluation_frequency:
            return self.evaluate_and_apply_scaling()
        
        return False
    
    def evaluate_and_apply_scaling(self) -> bool:
        """Evaluate current performance and apply scaling if needed"""
        logger.info("Evaluating dynamic scaling...")
        
        try:
            # Reset counter
            self.batch_count_since_evaluation = 0
            
            # Check if we have enough data for scaling decisions
            if not self.progress_tracker.should_trigger_scaling_evaluation():
                logger.debug("Insufficient data for scaling evaluation")
                return False
            
            # Get recent performance data
            recent_batches = self._get_recent_batch_results()
            if not recent_batches:
                logger.debug("No recent batch results available for scaling")
                return False
            
            # Convert to format expected by ScalingManager
            recent_batch_results = self._convert_to_batch_results(recent_batches)
            
            # Get scaling decision
            scaling_decision = self.scaling_manager.evaluate_scaling(recent_batch_results)
            
            # Get prediction analysis
            current_performance = self._build_current_performance_dict(recent_batches)
            prediction = self.scaling_predictor.get_scaling_recommendation(
                current_performance, recent_batches
            )
            
            # Log analysis
            logger.info(f"Scaling analysis - Decision: {scaling_decision.action.value}, "
                       f"Current size: {self.batch_manager.get_current_batch_size()}, "
                       f"Recommended: {scaling_decision.new_batch_size}")
            logger.info(f"Prediction confidence: {prediction.get('confidence_score', 0.0):.2f}")
            
            # Apply scaling decision
            success = self._apply_scaling_decision(scaling_decision, current_performance)
            
            # Record scaling event
            self._record_scaling_event(scaling_decision, current_performance, success)
            
            return success
            
        except Exception as e:
            logger.error(f"Error during scaling evaluation: {e}")
            self._record_scaling_event(
                ScalingDecision(
                    action=scaling_decision.action if 'scaling_decision' in locals() else None,
                    new_batch_size=self.batch_manager.get_current_batch_size(),
                    reason=f"Error during evaluation: {e}",
                    confidence_threshold=0.0,
                    performance_metrics={},
                    timestamp=datetime.now()
                ),
                {},
                False,
                str(e)
            )
            return False
    
    def force_scaling_evaluation(self) -> Dict:
        """Force an immediate scaling evaluation and return results"""
        logger.info("Forcing scaling evaluation...")
        
        # Get comprehensive analysis
        recent_batches = self._get_recent_batch_results()
        current_performance = self._build_current_performance_dict(recent_batches)
        
        # Get scaling decision
        recent_batch_results = self._convert_to_batch_results(recent_batches)
        scaling_decision = self.scaling_manager.evaluate_scaling(recent_batch_results)
        
        # Get prediction analysis
        prediction = self.scaling_predictor.get_scaling_recommendation(
            current_performance, recent_batches
        )
        
        # Get trend analysis
        trend_analysis = self.progress_tracker.get_scaling_trend_analysis()
        
        return {
            'current_batch_size': self.batch_manager.get_current_batch_size(),
            'scaling_decision': {
                'action': scaling_decision.action.value,
                'new_batch_size': scaling_decision.new_batch_size,
                'reason': scaling_decision.reason,
                'confidence_threshold': scaling_decision.confidence_threshold
            },
            'prediction': prediction,
            'trend_analysis': trend_analysis,
            'current_performance': current_performance,
            'scaling_active': self.batch_manager.is_dynamic_scaling_active()
        }
    
    def apply_recommended_scaling(self) -> bool:
        """Apply the currently recommended scaling"""
        return self.evaluate_and_apply_scaling()
    
    def enable_scaling(self):
        """Enable dynamic scaling"""
        self.enabled = True
        logger.info("Dynamic scaling enabled")
    
    def disable_scaling(self):
        """Disable dynamic scaling"""
        self.enabled = False
        logger.info("Dynamic scaling disabled")
    
    def get_scaling_status(self) -> Dict:
        """Get current scaling status and statistics"""
        scaling_summary = self.scaling_manager.get_scaling_summary()
        
        # Calculate scaling event statistics
        total_events = len(self.scaling_events)
        successful_events = sum(1 for event in self.scaling_events if event.success)
        
        recent_events = [event for event in self.scaling_events 
                        if (datetime.now() - event.timestamp).days <= 7]
        
        return {
            'enabled': self.enabled,
            'current_batch_size': self.batch_manager.get_current_batch_size(),
            'dynamic_scaling_active': self.batch_manager.is_dynamic_scaling_active(),
            'evaluation_frequency': self.evaluation_frequency,
            'batches_until_next_evaluation': self.evaluation_frequency - self.batch_count_since_evaluation,
            'scaling_summary': scaling_summary,
            'event_statistics': {
                'total_events': total_events,
                'successful_events': successful_events,
                'success_rate': successful_events / total_events if total_events > 0 else 0.0,
                'recent_events_7_days': len(recent_events)
            },
            'last_event': self.scaling_events[-1] if self.scaling_events else None
        }
    
    def _get_recent_batch_results(self, count: int = 5) -> List[Dict]:
        """Get recent batch results for analysis"""
        return self.progress_tracker.get_recent_batch_results_for_scaling(count)
    
    def _convert_to_batch_results(self, batch_data: List[Dict]) -> List[BatchResult]:
        """Convert batch data to BatchResult objects for ScalingManager"""
        batch_results = []
        
        for data in batch_data:
            # Create a mock BatchResult object with the data we have
            batch_result = type('BatchResult', (), {
                'batch_id': data.get('batch_id', 'unknown'),
                'total_items': data.get('total_items', 0),
                'successful_items': data.get('successful_items', 0),
                'failed_items': data.get('failed_items', 0),
                'processing_time': data.get('processing_time', 0.0),
                'confidence_distribution': data.get('confidence_distribution', {'High': 0, 'Medium': 0, 'Low': 0}),
                'results': [],  # Not needed for scaling decisions
                'summary': {}   # Not needed for scaling decisions
            })()
            
            batch_results.append(batch_result)
        
        return batch_results
    
    def _build_current_performance_dict(self, recent_batches: List[Dict]) -> Dict:
        """Build current performance dictionary for predictions"""
        if not recent_batches:
            return {
                'batch_size': self.batch_manager.get_current_batch_size(),
                'high_confidence_rate': 0.0,
                'avg_processing_time': 0.0,
                'success_rate': 0.0,
                'stability_score': 0.0
            }
        
        # Get performance metrics from progress tracker
        performance_metrics = self.progress_tracker.get_scaling_performance_metrics(len(recent_batches))
        performance_metrics['batch_size'] = self.batch_manager.get_current_batch_size()
        
        return performance_metrics
    
    def _apply_scaling_decision(self, decision: ScalingDecision, 
                              current_performance: Dict) -> bool:
        """Apply the scaling decision to the batch manager"""
        try:
            # Apply the decision in scaling manager first
            changed = self.scaling_manager.apply_scaling_decision(decision)
            
            if changed:
                # Update batch manager with new size
                new_size = self.scaling_manager.get_current_batch_size()
                self.batch_manager.set_dynamic_batch_size(new_size)
                
                logger.info(f"Applied scaling decision: {decision.action.value} to {new_size}")
                return True
            else:
                logger.debug(f"No scaling change applied: {decision.reason}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to apply scaling decision: {e}")
            return False
    
    def _record_scaling_event(self, decision: ScalingDecision, 
                            performance_metrics: Dict, 
                            success: bool,
                            error_message: Optional[str] = None):
        """Record a scaling event for tracking"""
        event = ScalingEvent(
            timestamp=datetime.now(),
            previous_batch_size=self.batch_manager.get_current_batch_size(),
            new_batch_size=decision.new_batch_size,
            trigger_reason=decision.reason,
            performance_metrics=performance_metrics.copy(),
            success=success,
            error_message=error_message
        )
        
        self.scaling_events.append(event)
        
        # Keep only last 50 events to prevent memory issues
        if len(self.scaling_events) > 50:
            self.scaling_events = self.scaling_events[-50:]
        
        logger.debug(f"Recorded scaling event: {event.trigger_reason} -> {success}")

# src/batch_processor/__init__.py
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import asdict

try:
    from .batch_manager import BatchManager, BatchConfig, BatchStatus
    from .processor import BatchProcessor, ProcessingResult, BatchResult
    from .progress_tracker import ProgressTracker
    from .feedback_loop import FeedbackLoopManager, FeedbackItem, FeedbackSummary, RefinementAction
    from .dynamic_scaling_controller import DynamicScalingController
    from .scaling_manager import ScalingConfig
    from ..utils.logger import get_logger
except ImportError:
    # Fallback for when running as script
    try:
        from .batch_manager import BatchManager, BatchConfig, BatchStatus
        from .processor import BatchProcessor, ProcessingResult, BatchResult
        from .progress_tracker import ProgressTracker
        from .feedback_loop import FeedbackLoopManager, FeedbackItem, FeedbackSummary, RefinementAction
        from .dynamic_scaling_controller import DynamicScalingController
        from .scaling_manager import ScalingConfig
        from utils.logger import get_logger
    except ImportError:
        # Final fallback for pytest
        from src.batch_processor.batch_manager import BatchManager, BatchConfig, BatchStatus
        from src.batch_processor.processor import BatchProcessor, ProcessingResult, BatchResult
        from src.batch_processor.progress_tracker import ProgressTracker
        from src.batch_processor.feedback_loop import FeedbackLoopManager, FeedbackItem, FeedbackSummary, RefinementAction
        from src.batch_processor.dynamic_scaling_controller import DynamicScalingController
        from src.batch_processor.scaling_manager import ScalingConfig
        from src.utils.logger import get_logger

logger = get_logger(__name__)

class BatchProcessingSystem:
    """Main interface for batch processing system"""
    
    def __init__(self, data_loader, description_generator, settings, 
                 enable_dynamic_scaling: bool = True,
                 scaling_config: Optional[ScalingConfig] = None):
        self.batch_manager = BatchManager(data_loader, settings)
        self.batch_processor = BatchProcessor(description_generator)
        self.progress_tracker = ProgressTracker(Path(settings['data_dir']))
        self.settings = settings
        
        # Initialize dynamic scaling if enabled
        if enable_dynamic_scaling:
            self.dynamic_scaling_controller = DynamicScalingController(
                batch_manager=self.batch_manager,
                progress_tracker=self.progress_tracker,
                scaling_config=scaling_config,
                data_dir=Path(settings['data_dir'])
            )
            logger.info("BatchProcessingSystem initialized with dynamic scaling enabled")
        else:
            self.dynamic_scaling_controller = None
            logger.info("BatchProcessingSystem initialized with dynamic scaling disabled")
    
    def run_batch(self, config: BatchConfig) -> BatchResult:
        """Run a complete batch processing cycle"""
        # Create batch
        batch_id = self.batch_manager.create_batch(config)
        
        # Load batch data
        batch_data, batch_metadata = self.batch_manager.load_batch(batch_id)
        
        # Initialize status
        status = BatchStatus(
            batch_id=batch_id,
            status='processing',
            total_items=len(batch_data),
            processed_items=0,
            successful_items=0,
            failed_items=0,
            high_confidence_count=0,
            medium_confidence_count=0,
            low_confidence_count=0,
            start_time=datetime.now()
        )
        
        self.batch_manager.update_batch_status(batch_id, status)
        
        try:
            # Process batch
            batch_result = self.batch_processor.process_batch(batch_data, config)
            batch_result.batch_id = batch_id  # Ensure correct batch ID
            
            # Update final status
            status.status = 'completed'
            status.end_time = datetime.now()
            status.processed_items = batch_result.total_items
            status.successful_items = batch_result.successful_items
            status.failed_items = batch_result.failed_items
            status.high_confidence_count = batch_result.confidence_distribution['High']
            status.medium_confidence_count = batch_result.confidence_distribution['Medium']
            status.low_confidence_count = batch_result.confidence_distribution['Low']
            
            self.batch_manager.update_batch_status(batch_id, status)
            
            # Update progress tracking
            self.progress_tracker.update_progress(batch_id, asdict(status))
            
            # Add to history with correct batch_id
            history_data = batch_result.summary.copy()
            history_data['batch_id'] = batch_id
            self.progress_tracker.add_to_history(history_data)
            
            # Trigger dynamic scaling evaluation if enabled
            if self.dynamic_scaling_controller:
                try:
                    scaling_applied = self.dynamic_scaling_controller.process_batch_completion(batch_result)
                    if scaling_applied:
                        logger.info(f"Dynamic scaling applied after batch {batch_id}")
                except Exception as e:
                    logger.error(f"Error in dynamic scaling evaluation: {e}")
            
            logger.info(f"Batch {batch_id} completed successfully")
            return batch_result
            
        except Exception as e:
            # Update failed status
            status.status = 'failed'
            status.end_time = datetime.now()
            status.error_message = str(e)
            
            self.batch_manager.update_batch_status(batch_id, status)
            
            # Update progress tracking for failed batch
            self.progress_tracker.update_progress(batch_id, asdict(status))
            
            logger.error(f"Batch {batch_id} failed: {e}")
            raise
    
    def get_progress(self) -> Dict[str, any]:
        """Get overall progress"""
        return self.progress_tracker.get_overall_progress()
    
    def list_batches(self) -> List[Dict]:
        """List all batches"""
        return self.batch_manager.list_batches()
    
    def get_performance_metrics(self):
        """Get performance metrics as DataFrame"""
        return self.progress_tracker.get_batch_performance_metrics()
    
    def get_recent_performance(self, days: int = 7):
        """Get recent performance trends"""
        return self.progress_tracker.get_recent_performance_trend(days)
    
    def get_batch_results(self, batch_id: str) -> Optional[BatchResult]:
        """Get detailed results for a specific batch"""
        try:
            batch_data, batch_metadata = self.batch_manager.load_batch(batch_id)
            status = self.batch_manager.get_batch_status(batch_id)
            
            if status and status.status == 'completed':
                # This is a simplified version - in a real implementation, 
                # you might want to save and load the full BatchResult
                return {
                    'batch_id': batch_id,
                    'metadata': batch_metadata,
                    'status': status,
                    'data_summary': {
                        'total_items': status.total_items,
                        'successful_items': status.successful_items,
                        'failed_items': status.failed_items,
                        'confidence_distribution': {
                            'High': status.high_confidence_count,
                            'Medium': status.medium_confidence_count,
                            'Low': status.low_confidence_count
                        }
                    }
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting batch results for {batch_id}: {e}")
            return None
    
    # Dynamic Scaling Methods
    def get_scaling_status(self) -> Optional[Dict]:
        """Get current dynamic scaling status"""
        if self.dynamic_scaling_controller:
            return self.dynamic_scaling_controller.get_scaling_status()
        return None
    
    def force_scaling_evaluation(self) -> Optional[Dict]:
        """Force an immediate scaling evaluation"""
        if self.dynamic_scaling_controller:
            return self.dynamic_scaling_controller.force_scaling_evaluation()
        return None
    
    def enable_dynamic_scaling(self) -> bool:
        """Enable dynamic scaling"""
        if self.dynamic_scaling_controller:
            self.dynamic_scaling_controller.enable_scaling()
            return True
        return False
    
    def disable_dynamic_scaling(self) -> bool:
        """Disable dynamic scaling"""
        if self.dynamic_scaling_controller:
            self.dynamic_scaling_controller.disable_scaling()
            return True
        return False
    
    def apply_recommended_scaling(self) -> bool:
        """Apply currently recommended scaling"""
        if self.dynamic_scaling_controller:
            return self.dynamic_scaling_controller.apply_recommended_scaling()
        return False
    
    def is_dynamic_scaling_enabled(self) -> bool:
        """Check if dynamic scaling is enabled"""
        return self.dynamic_scaling_controller is not None

# Export main classes and functions
__all__ = [
    'BatchProcessingSystem',
    'BatchConfig', 
    'BatchStatus',
    'BatchManager',
    'BatchProcessor',
    'ProgressTracker',
    'ProcessingResult',
    'BatchResult',
    'FeedbackLoopManager',
    'FeedbackItem',
    'FeedbackSummary',
    'RefinementAction',
    'DynamicScalingController',
    'ScalingConfig'
]

# src/batch_processor/processor.py
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import time

try:
    from ..utils.smart_description_generator import SmartDescriptionGenerator, DescriptionResult
    from ..utils.logger import get_logger
except ImportError:
    # Fallback for when running as script
    from utils.smart_description_generator import SmartDescriptionGenerator, DescriptionResult
    from utils.logger import get_logger
try:
    from .batch_manager import BatchStatus, BatchConfig
except ImportError:
    # Fallback for when running as script
    from batch_processor.batch_manager import BatchStatus, BatchConfig

logger = get_logger(__name__)

@dataclass
class ProcessingResult:
    """Result of processing a single item"""
    item_id: str
    original_description: str
    enhanced_description: str
    confidence_score: float
    confidence_level: str
    extracted_features: Dict[str, str]
    processing_time: float
    success: bool
    error_message: Optional[str] = None

@dataclass
class BatchResult:
    """Result of processing an entire batch"""
    batch_id: str
    total_items: int
    successful_items: int
    failed_items: int
    processing_time: float
    confidence_distribution: Dict[str, int]
    results: List[ProcessingResult]
    summary: Dict[str, any]

class BatchProcessor:
    """Processes batches of products with confidence scoring"""
    
    def __init__(self, description_generator: SmartDescriptionGenerator):
        self.generator = description_generator
        self.logger = logger
    
    def process_batch(self, batch_data: List[Dict], config: BatchConfig) -> BatchResult:
        """Process a batch of products"""
        start_time = time.time()
        
        results = []
        successful_items = 0
        failed_items = 0
        confidence_distribution = {'High': 0, 'Medium': 0, 'Low': 0}
        
        self.logger.info(f"Starting batch processing with {len(batch_data)} items")
        
        for i, product_data in enumerate(batch_data):
            item_start_time = time.time()
            
            try:
                # Generate description
                description_result = self.generator.generate_description(product_data)
                
                # Create processing result
                processing_time = time.time() - item_start_time
                
                result = ProcessingResult(
                    item_id=product_data.get('item_id', f'item_{i}'),
                    original_description=description_result.original_description,
                    enhanced_description=description_result.enhanced_description,
                    confidence_score=description_result.confidence_score,
                    confidence_level=description_result.confidence_level,
                    extracted_features=description_result.extracted_features,
                    processing_time=processing_time,
                    success=True
                )
                
                successful_items += 1
                confidence_distribution[description_result.confidence_level] += 1
                
                self.logger.debug(f"Processed item {i+1}/{len(batch_data)}: {result.confidence_level}")
                
            except Exception as e:
                processing_time = time.time() - item_start_time
                
                result = ProcessingResult(
                    item_id=product_data.get('item_id', f'item_{i}'),
                    original_description=product_data.get('item_description', ''),
                    enhanced_description='',
                    confidence_score=0.0,
                    confidence_level='Low',
                    extracted_features={},
                    processing_time=processing_time,
                    success=False,
                    error_message=str(e)
                )
                
                failed_items += 1
                confidence_distribution['Low'] += 1
                
                self.logger.error(f"Failed to process item {i+1}/{len(batch_data)}: {e}")
            
            results.append(result)
        
        total_processing_time = time.time() - start_time
        
        # Create batch result
        batch_result = BatchResult(
            batch_id=f"batch_{int(start_time)}",
            total_items=len(batch_data),
            successful_items=successful_items,
            failed_items=failed_items,
            processing_time=total_processing_time,
            confidence_distribution=confidence_distribution,
            results=results,
            summary=self._create_summary(results, confidence_distribution)
        )
        
        self.logger.info(f"Batch processing completed: {successful_items} successful, {failed_items} failed")
        self.logger.info(f"Confidence distribution: {confidence_distribution}")
        
        return batch_result
    
    def _create_summary(self, results: List[ProcessingResult], confidence_distribution: Dict[str, int]) -> Dict[str, any]:
        """Create summary statistics for the batch"""
        total_items = len(results)
        successful_items = sum(1 for r in results if r.success)
        
        # Calculate average confidence score
        confidence_scores = [r.confidence_score for r in results if r.success]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Calculate processing time statistics
        processing_times = [r.processing_time for r in results]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
        
        # Calculate success rate
        success_rate = successful_items / total_items if total_items > 0 else 0.0
        
        # Calculate high confidence rate
        high_confidence_rate = confidence_distribution['High'] / total_items if total_items > 0 else 0.0
        
        return {
            'total_items': total_items,
            'successful_items': successful_items,
            'failed_items': total_items - successful_items,
            'success_rate': success_rate,
            'avg_confidence_score': avg_confidence,
            'avg_processing_time': avg_processing_time,
            'high_confidence_rate': high_confidence_rate,
            'confidence_distribution': confidence_distribution
        }

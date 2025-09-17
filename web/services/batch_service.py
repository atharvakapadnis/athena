from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import json
from pathlib import Path
import asyncio
import logging
import json

# Import existing Athena components
from src.batch_processor import BatchProcessingSystem, BatchConfig, BatchManager
from src.batch_processor.processor import BatchProcessor, BatchResult
from src.batch_processor.dynamic_scaling_controller import DynamicScalingController
from src.utils.data_loader import DataLoader
from src.utils.smart_description_generator import SmartDescriptionGenerator
from src.utils.config import get_project_settings
from src.utils.logger import get_logger

from ..models.batch import (
    BatchConfigRequest, BatchResponse, BatchStatus, 
    BatchHistoryResponse
)

logger = get_logger(__name__)

class BatchService:
    """Service layer for batch operations - Full implementation integrating with existing Athena system"""
    
    def __init__(self):
        self.settings = get_project_settings()
        self.data_dir = Path(self.settings.get('data_dir', 'data'))
        
        # Initialize existing Athena components
        try:
            # Initialize data loader and description generator
            self.data_loader = DataLoader()
            
            # Try to load HTS data for description generator
            try:
                hts_data = self.data_loader.load_hts_reference()
                from src.utils.hts_hierarchy import HTSHierarchy
                hts_hierarchy = HTSHierarchy(hts_data)
                self.description_generator = SmartDescriptionGenerator(hts_hierarchy)
            except Exception as e:
                logger.warning(f"Could not initialize HTS hierarchy: {e}. Using fallback generator.")
                # Create a mock generator for testing
                self.description_generator = self._create_mock_generator()
            
            # Initialize batch processing system
            self.batch_system = BatchProcessingSystem(
                self.data_loader,
                self.description_generator,
                self.settings
            )
            
            # Initialize batch manager
            self.batch_manager = self.batch_system.batch_manager
            
            # Initialize dynamic scaling if available
            self.dynamic_scaling = self.batch_system.dynamic_scaling_controller
            
            logger.info("BatchService initialized with full Athena integration")
            
        except Exception as e:
            logger.error(f"Error initializing BatchService: {e}")
            # Fallback initialization
            self.batch_system = None
            self.batch_manager = None
            self.dynamic_scaling = None
            logger.warning("BatchService initialized in fallback mode")
    
    async def start_batch(self, config: BatchConfigRequest, user_id: str) -> BatchResponse:
        """Start a new batch using the existing batch processing system"""
        try:
            if not self.batch_system:
                raise Exception("Batch system not properly initialized")
            
            # Convert web request to Athena BatchConfig
            batch_config = BatchConfig(
                batch_size=config.batch_size,
                start_index=config.start_index,
                confidence_threshold_high=config.confidence_threshold_high,
                confidence_threshold_medium=config.confidence_threshold_medium,
                retry_failed_items=config.retry_failed_items,
                save_intermediate_results=True
                #max_processing_time=config.max_processing_time
            )
            
            # Create batch using existing system
            batch_id = self.batch_manager.create_batch(batch_config)
            
            logger.info(f"Created batch {batch_id} for user {user_id}")
            
            # Start batch processing in background
            asyncio.create_task(self._process_batch_background(batch_id, config))
            
            # Return initial batch response
            return BatchResponse(
                batch_id=batch_id,
                status=BatchStatus.RUNNING,
                batch_size=config.batch_size,
                items_processed=0,
                total_items=config.batch_size,
                progress_percentage=0.0,
                success_rate=0.0,
                average_confidence=0.0,
                created_at=datetime.utcnow(),
                created_by=user_id
            )
            
        except Exception as e:
            logger.error(f"Error starting batch: {e}")
            raise Exception(f"Failed to start batch: {str(e)}")
    
    async def get_batch_queue(self) -> List[BatchResponse]:
        """Get current batch processing queue from existing system"""
        try:
            if not self.batch_manager:
                return []
            
            # Get active batches from batch manager
            active_batches = self.batch_manager.list_batches()
            queue = []
            
            for batch_id in active_batches:
                batch_info = self.batch_manager.get_batch_status(batch_id)
                if batch_info and batch_info.status in ['running', 'pending', 'paused']:
                    batch_response = self._convert_to_batch_response(batch_id, batch_info)
                    if batch_response:
                        queue.append(batch_response)
            
            return queue
            
        except Exception as e:
            logger.error(f"Error getting batch queue: {e}")
            return []
    
    async def get_batch_history(self, page: int, page_size: int, status_filter: Optional[BatchStatus]) -> Dict:
        """Get batch history with pagination from existing system"""
        try:
            if not self.batch_manager:
                return self._empty_paginated_response(page, page_size)
            
            # Get all batches from batch manager
            all_batches = self.batch_manager.list_batches()
            
             # CORRECTED LOGGING
            logger.info(f"==================== BATCH HISTORY DEBUG ====================")
            logger.info(f"Retrieved {len(all_batches)} batches from manager")
            
            # Check if we have any batches
            if len(all_batches) > 0:
                # Log first 3 batches for debugging
                for i in range(min(3, len(all_batches))):
                    batch = all_batches[i]
                    logger.info(f"Batch {i}: batch_id={batch.get('batch_id', 'MISSING')}")
                    logger.info(f"  - status present: {batch.get('status') is not None}")
                    if batch.get('status'):
                        status_obj = batch.get('status')
                        logger.info(f"  - status type: {type(status_obj).__name__}")
                        # Try to get status string
                        if hasattr(status_obj, 'status'):
                            logger.info(f"  - status.status value: {status_obj.status}")
            else:
                logger.info("No batches found in batch manager")
                
            logger.info(f"==============================================================")

            history_items = []
            
            for batch_data in all_batches:
                batch_id = batch_data['batch_id']
                batch_info = batch_data['status']

                if batch_info:
                    # Filter by status if specified
                    if status_filter:
                        batch_status = self._convert_status(batch_info.status)
                        if batch_status != status_filter:
                            continue
                    
                    history_item = self._convert_to_history_response(batch_id, batch_info)
                    if history_item:
                        history_items.append(history_item)
            
            # NEW LOGGING After processing and before sorting
            logger.info(f"Converted {len(history_items)} batch items for response")
            if len(history_items) > 0:
                logger.info(f"Latest batch in history: {history_items[0].batch_id if history_items else 'None'}")

            # Sort by creation date (most recent first)
            history_items.sort(key=lambda x: x.created_at, reverse=True)
            
            # Apply pagination
            total = len(history_items)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_items = history_items[start_idx:end_idx]
            
            # NEW LOGGING for pagination results
            logger.info(f"Returning {len(paginated_items)} items in page {page} (total: {total})")
            if paginated_items:
                logger.info(f"First item in page: {paginated_items[0].batch_id}")
            logger.info(f"==============================================================")
            
            return {
                'items': [item.dict() for item in paginated_items],
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
                'has_next': end_idx < total,
                'has_previous': page > 1
            }
            
        except Exception as e:
            logger.error(f"Error getting batch history: {e}")
            return self._empty_paginated_response(page, page_size)
    
    async def get_batch_details(self, batch_id: str) -> Optional[BatchResponse]:
        """Get detailed batch information from existing system"""
        try:
            if not self.batch_manager:
                return None
            
            batch_info = self.batch_manager.get_batch_status(batch_id)
            if not batch_info:
                return None
            
            return self._convert_to_batch_response(batch_id, batch_info)
            
        except Exception as e:
            logger.error(f"Error getting batch details for {batch_id}: {e}")
            return None
    
    async def get_batch_enhanced_results(self, batch_id: str) -> Optional[Dict]:
        """Get enhanced results for a completed batch"""
        try:
            if not self.batch_manager:
                return None

            # Check if enhanced results exist
            if not self.batch_manager.has_enhanced_results(batch_id):
                return None

            enhanced_results, metadata = self.batch_manager.load_batch_results(batch_id)

            return {
                'batch_id': batch_id,
                'results': enhanced_results,
                'metadata': metadata,
                'total_items': len(enhanced_results),
                'enhanced': True
            }
        
        except Exception as e:
            logger.error(f"Error getting enhanced results for {batch_id}: {e}")
            return None

    # async def get_batch_details_with_results(self, batch_id: str) -> Optional[Dict]:
    #     """Get batch details including enhanced results if available"""
    #     try:
    #         #Get basic batch info
    #         batch_response = await self.get_batch_details(batch_id)
    #         if not batch_response:
    #             return None

    #         #get enhanced results if available
    #         enhanced_results = await self.get_batch_enhanced_results(batch_id)

    #         return {
    #             'batch_info': batch_response,
    #             'enhanced_results': enhanced_results,
    #             'has_enhanced_results': enhanced_results is not None
    #         }

    #     except Exception as e:
    #         logger.error(f"Error getting complete batch details for {batch_id}: {e}")
    #         return None

    async def pause_batch(self, batch_id: str, user_id: str) -> Dict:
        """Pause a batch using existing system"""
        try:
            if not self.batch_system:
                raise Exception("Batch system not available")
            
            # Use existing batch management functionality
            success = self.batch_system.pause_batch(batch_id)
            
            if success:
                logger.info(f"Batch {batch_id} paused by user {user_id}")
                return {'success': True, 'message': f'Batch {batch_id} paused successfully'}
            else:
                raise Exception("Failed to pause batch")
                
        except Exception as e:
            logger.error(f"Error pausing batch {batch_id}: {e}")
            raise Exception(f"Failed to pause batch: {str(e)}")
    
    async def resume_batch(self, batch_id: str, user_id: str) -> Dict:
        """Resume a batch using existing system"""
        try:
            if not self.batch_system:
                raise Exception("Batch system not available")
            
            # Use existing batch management functionality
            success = self.batch_system.resume_batch(batch_id)
            
            if success:
                logger.info(f"Batch {batch_id} resumed by user {user_id}")
                return {'success': True, 'message': f'Batch {batch_id} resumed successfully'}
            else:
                raise Exception("Failed to resume batch")
                
        except Exception as e:
            logger.error(f"Error resuming batch {batch_id}: {e}")
            raise Exception(f"Failed to resume batch: {str(e)}")
    
    async def cancel_batch(self, batch_id: str, user_id: str, reason: Optional[str]) -> Dict:
        """Cancel a batch using existing system"""
        try:
            if not self.batch_system:
                raise Exception("Batch system not available")
            
            # Use existing batch management functionality
            success = self.batch_system.cancel_batch(batch_id, reason)
            
            if success:
                logger.info(f"Batch {batch_id} cancelled by user {user_id}. Reason: {reason}")
                return {
                    'success': True, 
                    'message': f'Batch {batch_id} cancelled successfully',
                    'reason': reason
                }
            else:
                raise Exception("Failed to cancel batch")
                
        except Exception as e:
            logger.error(f"Error cancelling batch {batch_id}: {e}")
            raise Exception(f"Failed to cancel batch: {str(e)}")
    
    # async def get_scaling_status(self) -> Dict:
    #     """Get dynamic scaling status from existing system"""
    #     try:
    #         if not self.dynamic_scaling:
    #             return {
    #                 'enabled': False,
    #                 'current_batch_size': self.settings.get('batch_size', 50),
    #                 'efficiency_score': 0.0,
    #                 'efficiency_change': 0.0,
    #                 'recommended_batch_size': self.settings.get('batch_size', 50),
    #                 'recommendation_confidence': 0.0,
    #                 'message': 'Dynamic scaling not available'
    #             }
            
    #         # Get scaling status from existing controller
    #         status = self.dynamic_scaling.get_scaling_status()
            
    #         if status:
    #             return {
    #                 'enabled': status.get('enabled', False),
    #                 'current_batch_size': status.get('current_batch_size', 50),
    #                 'efficiency_score': status.get('efficiency_score', 0.0),
    #                 'efficiency_change': status.get('efficiency_change', 0.0),
    #                 'recommended_batch_size': status.get('recommended_batch_size', 50),
    #                 'recommendation_confidence': status.get('recommendation_confidence', 0.0),
    #                 'last_scaling_event': status.get('last_scaling_event'),
    #                 'scaling_history': status.get('recent_events', [])
    #             }
    #         else:
    #             return {
    #                 'enabled': False,
    #                 'current_batch_size': 50,
    #                 'efficiency_score': 0.0,
    #                 'efficiency_change': 0.0,
    #                 'recommended_batch_size': 50,
    #                 'recommendation_confidence': 0.0
    #             }
                
    #     except Exception as e:
    #         logger.error(f"Error getting scaling status: {e}")
    #         return {
    #             'enabled': False,
    #             'current_batch_size': 50,
    #             'efficiency_score': 0.0,
    #             'efficiency_change': 0.0,
    #             'recommended_batch_size': 50,
    #             'recommendation_confidence': 0.0,
    #             'error': str(e)
    #         }
    
    # async def configure_scaling(self, config: ScalingConfigRequest, user_id: str) -> Dict:
    #     """Configure scaling parameters using existing system"""
    #     try:
    #         if not self.dynamic_scaling:
    #             raise Exception("Dynamic scaling not available")
            
    #         # Convert web config to system config
    #         scaling_config = {
    #             'enabled': config.enabled,
    #             'min_batch_size': config.min_batch_size,
    #             'max_batch_size': config.max_batch_size,
    #             'target_confidence': config.target_confidence,
    #             'scaling_factor': config.scaling_factor
    #         }
            
    #         # Apply configuration using existing controller
    #         success = self.dynamic_scaling.update_configuration(scaling_config)
            
    #         if success:
    #             logger.info(f"Scaling configuration updated by user {user_id}: {scaling_config}")
    #             return {
    #                 'success': True, 
    #                 'message': 'Scaling configuration updated successfully',
    #                 'configuration': scaling_config
    #             }
    #         else:
    #             raise Exception("Failed to update scaling configuration")
                
    #     except Exception as e:
    #         logger.error(f"Error configuring scaling: {e}")
    #         raise Exception(f"Failed to configure scaling: {str(e)}")
    
    # async def enable_scaling(self, user_id: str) -> Dict:
    #     """Enable dynamic scaling using existing system"""
    #     try:
    #         if not self.dynamic_scaling:
    #             raise Exception("Dynamic scaling not available")
            
    #         success = self.dynamic_scaling.enable_scaling()
            
    #         if success:
    #             logger.info(f"Dynamic scaling enabled by user {user_id}")
    #             return {'success': True, 'message': 'Dynamic scaling enabled successfully'}
    #         else:
    #             raise Exception("Failed to enable scaling")
                
    #     except Exception as e:
    #         logger.error(f"Error enabling scaling: {e}")
    #         raise Exception(f"Failed to enable scaling: {str(e)}")
    
    # async def disable_scaling(self, user_id: str) -> Dict:
    #     """Disable dynamic scaling using existing system"""
    #     try:
    #         if not self.dynamic_scaling:
    #             raise Exception("Dynamic scaling not available")
            
    #         success = self.dynamic_scaling.disable_scaling()
            
    #         if success:
    #             logger.info(f"Dynamic scaling disabled by user {user_id}")
    #             return {'success': True, 'message': 'Dynamic scaling disabled successfully'}
    #         else:
    #             raise Exception("Failed to disable scaling")
                
    #     except Exception as e:
    #         logger.error(f"Error disabling scaling: {e}")
    #         raise Exception(f"Failed to disable scaling: {str(e)}")
    
    async def monitor_batch(self, batch_id: str):
        """Background task to monitor batch progress using existing system"""
        try:
            logger.info(f"Starting background monitoring for batch {batch_id}")
            
            # Monitor batch progress
            while True:
                if not self.batch_manager:
                    break
                
                batch_info = self.batch_manager.get_batch_status(batch_id)
                if not batch_info:
                    logger.warning(f"Batch {batch_id} no longer exists, stopping monitoring")
                    break
                
                status = batch_info.status if batch_info else 'unknown'
                
                # Check if batch is complete
                if status in ['completed', 'failed', 'cancelled']:
                    logger.info(f"Batch {batch_id} finished with status: {status}")
                    break
                
                # Log progress
                progress = getattr(batch_info, 'progress_percentage', 0) if batch_info else 0
                logger.debug(f"Batch {batch_id} progress: {progress}%")
                
                # Wait before next check
                await asyncio.sleep(10)  # Check every 10 seconds
                
        except Exception as e:
            logger.error(f"Error monitoring batch {batch_id}: {e}")
    
    # Helper methods
    async def _process_batch_background(self, batch_id: str, config: BatchConfigRequest):
        """Process batch in background using exisiting batch system"""
        try:
            if not self.batch_system:
                logger.error(f"Cannot process batch {batch_id}: batch system not initialized")
                return

            logger.info(f"Starting background processing for {batch_id}")

            #Load the exisiting batch data that was already created
            batch_data, batch_metadata = self.batch_manager.load_batch(batch_id)

            #Update the batch status to processing
            from src.batch_processor.batch_manager import BatchStatus
            processing_status = BatchStatus(
                batch_id=batch_id,
                status='processing',
                total_items=len(batch_data),
                processed_items=0,
                successful_items=0,
                failed_items=0,
                high_confidence_count=0,
                medium_confidence_count=0,
                low_confidence_count=0,
            )

            self.batch_manager.update_batch_status(batch_id, processing_status)

            # Process the existing batch data using the processor
            result = self.batch_system.batch_processor.process_batch(batch_data, batch_metadata)
            logger.info(f"Batch results type: {type(result)}")
            logger.info(f"Sample result: {result.results[0].__dict__ if result.results else 'No results'}")

            # Update to completed status with results
            completed_status = BatchStatus(
                batch_id=batch_id,
                status='completed',
                total_items=result.total_items,
                processed_items=result.total_items,
                successful_items=result.successful_items,
                failed_items=result.failed_items,
                high_confidence_count=result.confidence_distribution.get('High', 0),
                medium_confidence_count=result.confidence_distribution.get('Medium', 0),
                low_confidence_count=result.confidence_distribution.get('Low', 0),
            )

            self.batch_manager.update_batch_status(batch_id, completed_status)

            # Save the enhanced results to a seperate file
            enhanced_data_file = self.batch_manager.batches_dir / f"{batch_id}_results.json"
            with open(enhanced_data_file, 'w') as f:
                # Convert results to a serializable format
                serializable_results = []
                for processing_result in result.results:
                    serializable_results.append({
                        'item_id': processing_result.item_id,
                        'original_description': processing_result.original_description,
                        'enhanced_description': processing_result.enhanced_description,
                        'confidence_score': processing_result.confidence_score,
                        'confidence_level': processing_result.confidence_level,
                        'extracted_features': processing_result.extracted_features,
                        'processing_time': processing_result.processing_time,
                        'success': processing_result.success,
                        'error_message': processing_result.error_message
                    })

                json.dump({
                    'batch_id': batch_id,
                    'total_items': result.total_items,
                    'successful_items': result.successful_items,
                    'failed_items': result.failed_items,
                    'confidence_distribution': result.confidence_distribution,
                    'results': serializable_results,
                }, f, indent=2, default=str)

            logger.info(f"Batch {batch_id} processing completed successfully")
            logger.info(f"Enhanced results saved to: {enhanced_data_file}")

            #Handle notification if webhook is provided
            if config.notification_webhook and config.notification_webhook != "string":
                await self._send_webhook_notification(config.notification_webhook, batch_id, result)
        
        except Exception as e:
            logger.error(f"Error in background processing for batch {batch_id}: {e}")
            # Mark batch as failed
            try:
                from src.batch_processor.batch_manager import BatchStatus
                failed_status = BatchStatus(
                    batch_id=batch_id,
                    status='failed',
                    total_items=0,
                    processed_items=0,
                    successful_items=0,
                    failed_items=0,
                    high_confidence_count=0,
                    medium_confidence_count=0,
                    low_confidence_count=0,
                    error_message=str(e)
                )
                self.batch_manager.update_batch_status(batch_id, failed_status)
            except Exception as status_error:
                logger.error(f"Failed to update batch status: {status_error}")
    
    async def _send_webhook_notification(self, webhook_url: str, batch_id: str, result: BatchResult):
        """Send webhook notification for batch completion"""
        try:
            import aiohttp
            
            notification_data = {
                'batch_id': batch_id,
                'status': 'completed' if result.successful_items > 0 else 'failed',
                'total_items': result.total_items,
                'successful_items': result.successful_items,
                'failed_items': result.failed_items,
                'processing_time': result.processing_time,
                'confidence_distribution': result.confidence_distribution,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=notification_data, timeout=10) as response:
                    if response.status == 200:
                        logger.info(f"Webhook notification sent successfully for batch {batch_id}")
                    else:
                        logger.warning(f"Webhook notification failed for batch {batch_id}: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error sending webhook notification for batch {batch_id}: {e}")
    
    def _convert_to_batch_response(self, batch_id: str, batch_info) -> Optional[BatchResponse]:
        """Convert batch info from existing system to BatchResponse"""
        try:
            
            #Temporary debug logging
            # logger.info(f"DEBUG - BatchStatus attributes: {dir(batch_info)}")
            # logger.info(f"DEBUG - batch_size value: {getattr(batch_info, 'batch_size', 'MISSING')}")
            # logger.info(f"DEBUG - successful_items value: {getattr(batch_info, 'successful_items', 'MISSING')}")
            # logger.info(f"DEBUG - failed_items value: {getattr(batch_info, 'failed_items', 'MISSING')}")

            #Calculate metrics based off of available metrics
            total_items = getattr(batch_info, 'total_items', 0)
            successful_items = getattr(batch_info, 'successful_items', 0)
            failed_items = getattr(batch_info, 'failed_items', 0)

            #Calculate success rate
            success_rate = (successful_items / total_items) if total_items > 0 else 0.0

            #Calculate average confidence from confidence distribution
            high_count = getattr(batch_info, 'high_confidence_count', 0)
            medium_count = getattr(batch_info, 'medium_confidence_count', 0)
            low_count = getattr(batch_info, 'low_confidence_count', 0)

            # Average confidence High=0.9, Medium=0.7, Low=0.4
            total_confidence_items = high_count + medium_count + low_count
            avg_confidence = 0.0
            if total_confidence_items > 0:
                avg_confidence = (high_count * 0.9 + medium_count * 0.7 + low_count * 0.4) / total_confidence_items

            #Calculate processing duration
            start_time = getattr(batch_info, 'start_time', None)
            end_time = getattr(batch_info, 'end_time', None)
            processing_duration = None
            if start_time and end_time:
                processing_duration = (end_time - start_time).total_seconds()

            return BatchResponse(
                batch_id=batch_id,
                status=self._convert_status(batch_info.status),
                batch_size=total_items,
                items_processed=getattr(batch_info, 'processed_items', 0),
                total_items=total_items,
                progress_percentage=100.0 if batch_info.status == 'completed' else 0.0,
                success_rate=success_rate,
                average_confidence=avg_confidence,
                processing_duration=processing_duration,
                created_at=datetime.fromisoformat(getattr(batch_info, 'start_time', datetime.utcnow()).isoformat()) if hasattr(getattr(batch_info, 'start_time', None), 'isoformat') else datetime.utcnow(),
                created_by=getattr(batch_info, 'created_by', 'system'),
                completed_at=datetime.fromisoformat(getattr(batch_info, 'end_time', None).isoformat()) if getattr(batch_info, 'end_time', None) and hasattr(getattr(batch_info, 'end_time', None), 'isoformat') else None,
                error_message=getattr(batch_info, 'error_message', None)
            )
        except Exception as e:
            logger.error(f"Error converting batch info for {batch_id}: {e}")
            return None
    
    def _convert_to_history_response(self, batch_id: str, batch_info) -> Optional[BatchHistoryResponse]:
        """Convert batch info to history response"""
        try:
            # Safely get values with defaults
            total_items = getattr(batch_info, 'total_items', 0) or 0
            successful_items = getattr(batch_info, 'successful_items', 0) or 0
            processed_items = getattr(batch_info, 'processed_items', 0) or 0
            
            # Calculate success rate
            success_rate = 0.0
            if processed_items > 0:
                success_rate = successful_items / processed_items
            elif total_items > 0 and successful_items > 0:
                success_rate = successful_items / total_items
            
            # Calculate average confidence - FIX THE NONE ADDITION ERROR HERE
            high_count = getattr(batch_info, 'high_confidence_count', 0) or 0
            medium_count = getattr(batch_info, 'medium_confidence_count', 0) or 0
            low_count = getattr(batch_info, 'low_confidence_count', 0) or 0
            
            # Ensure these are integers, not None
            high_count = int(high_count) if high_count is not None else 0
            medium_count = int(medium_count) if medium_count is not None else 0
            low_count = int(low_count) if low_count is not None else 0
            
            total_confidence_items = high_count + medium_count + low_count
            avg_confidence = 0.0
            if total_confidence_items > 0:
                avg_confidence = (high_count * 0.9 + medium_count * 0.7 + low_count * 0.4) / total_confidence_items

            # Handle datetime fields safely
            start_time = getattr(batch_info, 'start_time', None)
            end_time = getattr(batch_info, 'end_time', None)
            processing_duration = None
            
            if start_time and end_time:
                try:
                    if isinstance(start_time, datetime) and isinstance(end_time, datetime):
                        processing_duration = (end_time - start_time).total_seconds()
                except Exception as e:
                    logger.debug(f"Could not calculate duration for {batch_id}: {e}")
            
            # Handle created_at
            created_at = None
            if start_time:
                if isinstance(start_time, datetime):
                    created_at = start_time
                elif isinstance(start_time, str):
                    try:
                        created_at = datetime.fromisoformat(start_time)
                    except:
                        pass

            if not created_at:
                logger.warning(f"Batch {batch_id} has no valid starttime, skipping")
                return None
            
            # Handle completed_at
            completed_at = None
            if end_time and isinstance(end_time, datetime):
                completed_at = end_time

            return BatchHistoryResponse(
                batch_id=batch_id,
                status=self._convert_status(batch_info.status),
                batch_size=total_items,
                items_processed=processed_items,
                total_items=total_items,
                success_rate=success_rate,
                average_confidence=avg_confidence,
                created_at=created_at,
                completed_at=completed_at,
                processing_duration=processing_duration
            )
        except Exception as e:
            logger.error(f"Error converting batch history for {batch_id}: {e}", exc_info=True)
            return None
    
    def _convert_status(self, status_str: str) -> BatchStatus:
        """Convert status string to BatchStatus enum"""
        status_mapping = {
            'pending': BatchStatus.PENDING,
            'running': BatchStatus.RUNNING,
            'paused': BatchStatus.PAUSED,
            'completed': BatchStatus.COMPLETED,
            'failed': BatchStatus.FAILED,
            'cancelled': BatchStatus.CANCELLED
        }
        return status_mapping.get(status_str.lower(), BatchStatus.PENDING)
    
    def _empty_paginated_response(self, page: int, page_size: int) -> Dict:
        """Return empty paginated response"""
        return {
            'items': [],
            'total': 0,
            'page': page,
            'page_size': page_size,
            'total_pages': 0,
            'has_next': False,
            'has_previous': False
        }
    
    def _create_mock_generator(self):
        """Create a mock description generator for testing"""
        class MockDescriptionGenerator:
            def generate_description(self, product_data):
                from src.utils.smart_description_generator import DescriptionResult
                return DescriptionResult(
                    original_description=product_data.get('item_description', ''),
                    enhanced_description=f"Enhanced: {product_data.get('item_description', '')}",
                    confidence_score=0.8,
                    confidence_level="High",
                    extracted_features={},
                    processing_time=0.1,
                    success=True
                )
        
        return MockDescriptionGenerator()
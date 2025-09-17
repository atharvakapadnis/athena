# src/batch_processor/batch_manager.py
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

try:
    from ..utils.logger import get_logger
    from ..utils.config import get_project_settings
except ImportError:
    # Fallback for when running as script
    from utils.logger import get_logger
    from utils.config import get_project_settings

logger = get_logger(__name__)

@dataclass
class BatchConfig:
    """Configuration for batch processing"""
    batch_size: int = 50
    start_index: int = 0
    max_batches: Optional[int] = None
    confidence_threshold_high: float = 0.8
    confidence_threshold_medium: float = 0.6
    save_intermediate_results: bool = True
    retry_failed_items: bool = True

@dataclass
class BatchStatus:
    """Status tracking for a batch"""
    batch_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    high_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None

class BatchManager:
    """Manages batch creation, tracking, and state management"""
    
    def __init__(self, data_loader, settings: Optional[Dict] = None):
        self.data_loader = data_loader
        self.settings = settings or get_project_settings()
        self.batches_dir = Path(self.settings['batches_dir'])
        self.batches_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_batch_id = None
        self.batch_history = []
        
        # Dynamic batch size tracking
        self.dynamic_batch_size = None  # Will override config.batch_size if set
    
    def create_batch(self, config: BatchConfig) -> str:
        """Create a new batch from the dataset"""
        batch_id = str(uuid.uuid4())
        
        # Load product data
        df = self.data_loader.load_product_data()
        
        # Use dynamic batch size if set, otherwise use config batch size
        effective_batch_size = self.dynamic_batch_size if self.dynamic_batch_size is not None else config.batch_size
        
        # Calculate batch indices
        start_idx = config.start_index
        end_idx = min(start_idx + effective_batch_size, len(df))
        
        # Extract batch data
        batch_df = df.iloc[start_idx:end_idx].copy()
        
        # Create batch metadata
        batch_metadata = {
            'batch_id': batch_id,
            'config': asdict(config),
            'effective_batch_size': effective_batch_size,
            'dynamic_scaling_active': self.dynamic_batch_size is not None,
            'data_indices': {'start': start_idx, 'end': end_idx},
            'created_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        # Save batch data and metadata
        batch_data_file = self.batches_dir / f"{batch_id}_data.json"
        batch_metadata_file = self.batches_dir / f"{batch_id}_metadata.json"
        
        # Convert DataFrame to records for JSON serialization
        batch_records = batch_df.to_dict('records')
        
        with open(batch_data_file, 'w') as f:
            json.dump(batch_records, f, indent=2, default=str)
        
        with open(batch_metadata_file, 'w') as f:
            json.dump(batch_metadata, f, indent=2, default=str)
        
        logger.info(f"Created batch {batch_id} with {len(batch_records)} items")
        
        return batch_id
    
    def load_batch(self, batch_id: str) -> Tuple[List[Dict], Dict]:
        """Load batch data and metadata"""
        batch_data_file = self.batches_dir / f"{batch_id}_data.json"
        batch_metadata_file = self.batches_dir / f"{batch_id}_metadata.json"
        
        if not batch_data_file.exists() or not batch_metadata_file.exists():
            raise FileNotFoundError(f"Batch {batch_id} not found")
        
        with open(batch_data_file, 'r') as f:
            batch_data = json.load(f)
        
        with open(batch_metadata_file, 'r') as f:
            batch_metadata = json.load(f)
        
        return batch_data, batch_metadata

    def load_batch_results(self, batch_id: str) -> Tuple[List[Dict], Dict]:
        """Load enhanced batch results instead of the original data for completed batches"""
        results_file = self.batches_dir / f"{batch_id}_results.json"
        metadata_file = self.batches_dir / f"{batch_id}_metadata.json"

        if results_file.exists() and metadata_file.exists():
            #Load enhacned results if available
            with open(results_file, 'r') as f:
                results_data = json.load(f)

            with open(metadata_file, 'r') as f:
                batch_metadata = json.load(f)

            # Extract the enhacned resutlts from the file structure
            enhanced_results = results_data.get('results', [])
            return enhanced_results, batch_metadata
        
        else:
            #Fall back to original data if enhacned results don't exist
            return self.load_batch(batch_id)

    def has_enhanced_results(self, batch_id: str) -> bool:
        """Check if batch has enhanced results available"""
        results_file = self.batches_dir / f"{batch_id}_results.json"
        return results_file.exists()

    def update_batch_status(self, batch_id: str, status: BatchStatus):
        """Update batch status"""
        # Adding logging
        if batch_id != self.current_batch_id:
            logger.info(f"Updating status for non current batch: {batch_id}")

        status_file = self.batches_dir / f"{batch_id}_status.json"
        
        # Convert datetime objects to ISO format strings for JSON serialization
        status_data = asdict(status)
        for time_field in ['start_time', 'end_time']:
            if status_data.get(time_field) and isinstance(status_data[time_field], datetime):
                status_data[time_field] = status_data[time_field].isoformat()
        
        # ADD THIS LOGGING
        logger.info(f"Saving batch status for {batch_id} to {status_file}")
        logger.info(f"Status data: status={status.status}, processed={status.processed_items}/{status.total_items}")
        
        with open(status_file, 'w') as f:
            json.dump(asdict(status), f, indent=2, default=str)
        
        logger.info(f"Updated batch {batch_id} status: {status.status}")
    
    def get_batch_status(self, batch_id: str) -> Optional[BatchStatus]:
        """Get current batch status"""
        status_file = self.batches_dir / f"{batch_id}_status.json"
        
        if not status_file.exists():
            return None
        
        with open(status_file, 'r') as f:
            status_data = json.load(f)
        
        # Convert datetime strings back to datetime objects if they exist
        for time_field in ['start_time', 'end_time']:
            if status_data.get(time_field):
                status_data[time_field] = datetime.fromisoformat(status_data[time_field])
        
        return BatchStatus(**status_data)
    
    def list_batches(self) -> List[Dict]:
        """List all batches with their status"""
        batches = []
        
        # Adding debug logging
        logger.info(f"Scanning directory: {self.batches_dir}")
        all_files = list(self.batches_dir.glob("*"))
        logger.info(f"Found {len(all_files)} files in batches directory")
        
        metadata_files = list(self.batches_dir.glob("*_metadata.json"))
        logger.info(f"Found {len(metadata_files)} metadata files")
        if len(metadata_files) > 0:
            logger.info(f"First metadata file: {metadata_files[0].name}")
            
        for metadata_file in self.batches_dir.glob("*_metadata.json"):
            batch_id = metadata_file.stem.replace("_metadata", "")
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            status = self.get_batch_status(batch_id)
            
            batch_info = {
                'batch_id': batch_id,
                'metadata': metadata,
                'status': status
            }
            batches.append(batch_info)
        
        return batches
    
    def set_dynamic_batch_size(self, batch_size: int):
        """Set dynamic batch size that overrides config batch size"""
        if batch_size <= 0:
            raise ValueError("Batch size must be positive")
        
        old_size = self.dynamic_batch_size
        self.dynamic_batch_size = batch_size
        
        logger.info(f"Dynamic batch size updated: {old_size} → {batch_size}")
    
    def get_current_batch_size(self) -> int:
        """Get the current effective batch size"""
        return self.dynamic_batch_size if self.dynamic_batch_size is not None else self.settings.get('batch_size', 50)
    
    def clear_dynamic_batch_size(self):
        """Clear dynamic batch size and return to config-based sizing"""
        old_size = self.dynamic_batch_size
        self.dynamic_batch_size = None
        
        logger.info(f"Dynamic batch size cleared: {old_size} → config-based")
    
    def is_dynamic_scaling_active(self) -> bool:
        """Check if dynamic scaling is currently active"""
        return self.dynamic_batch_size is not None

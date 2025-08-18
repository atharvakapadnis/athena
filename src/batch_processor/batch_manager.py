# src/batch_processor/batch_manager.py
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

try:
    from utils.logger import get_logger
    from utils.config import get_project_settings
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
    
    def create_batch(self, config: BatchConfig) -> str:
        """Create a new batch from the dataset"""
        batch_id = str(uuid.uuid4())
        
        # Load product data
        df = self.data_loader.load_product_data()
        
        # Calculate batch indices
        start_idx = config.start_index
        end_idx = min(start_idx + config.batch_size, len(df))
        
        # Extract batch data
        batch_df = df.iloc[start_idx:end_idx].copy()
        
        # Create batch metadata
        batch_metadata = {
            'batch_id': batch_id,
            'config': asdict(config),
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
    
    def update_batch_status(self, batch_id: str, status: BatchStatus):
        """Update batch status"""
        status_file = self.batches_dir / f"{batch_id}_status.json"
        
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

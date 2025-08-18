# src/batch_processor/progress_tracker.py
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd

try:
    from ..utils.logger import get_logger
except ImportError:
    # Fallback for when running as script
    from utils.logger import get_logger

logger = get_logger(__name__)

class ProgressTracker:
    """Tracks batch processing progress and metrics"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.metrics_dir = data_dir / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        self.progress_file = self.metrics_dir / "batch_progress.json"
        self.history_file = self.metrics_dir / "processing_history.json"
    
    def update_progress(self, batch_id: str, status: Dict):
        """Update progress for a specific batch"""
        progress_data = self._load_progress()
        
        progress_data[batch_id] = {
            **status,
            'last_updated': datetime.now().isoformat()
        }
        
        self._save_progress(progress_data)
        logger.info(f"Updated progress for batch {batch_id}")
    
    def add_to_history(self, batch_result: Dict):
        """Add batch result to processing history"""
        history = self._load_history()
        
        history_entry = {
            **batch_result,
            'timestamp': datetime.now().isoformat()
        }
        
        history.append(history_entry)
        
        # Keep only last 100 entries
        if len(history) > 100:
            history = history[-100:]
        
        self._save_history(history)
        logger.info(f"Added batch {batch_result.get('batch_id')} to history")
    
    def get_overall_progress(self) -> Dict[str, any]:
        """Get overall progress across all batches"""
        progress_data = self._load_progress()
        history = self._load_history()
        
        if not progress_data and not history:
            return {'status': 'no_data'}
        
        # Calculate overall statistics
        # Use the maximum of progress_data and history length for total batches
        # This handles cases where one source might be incomplete
        total_batches = max(len(progress_data), len(history))
        completed_batches = sum(1 for status in progress_data.values() if status.get('status') == 'completed')
        
        total_items = 0
        successful_items = 0
        high_confidence_items = 0
        
        for entry in history:
            total_items += entry.get('total_items', 0)
            successful_items += entry.get('successful_items', 0)
            high_confidence_items += entry.get('confidence_distribution', {}).get('High', 0)
        
        success_rate = successful_items / total_items if total_items > 0 else 0.0
        high_confidence_rate = high_confidence_items / total_items if total_items > 0 else 0.0
        
        return {
            'total_batches': total_batches,
            'completed_batches': completed_batches,
            'completion_rate': completed_batches / total_batches if total_batches > 0 else 0.0,
            'total_items_processed': total_items,
            'successful_items': successful_items,
            'success_rate': success_rate,
            'high_confidence_rate': high_confidence_rate,
            'last_updated': datetime.now().isoformat()
        }
    
    def get_batch_performance_metrics(self) -> pd.DataFrame:
        """Get performance metrics as a DataFrame for analysis"""
        history = self._load_history()
        
        if not history:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(history)
        
        # Add derived metrics
        df['success_rate'] = df['successful_items'] / df['total_items']
        df['high_confidence_rate'] = df['confidence_distribution'].apply(
            lambda x: x.get('High', 0) / sum(x.values()) if sum(x.values()) > 0 else 0
        )
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    def get_recent_performance_trend(self, days: int = 7) -> Dict[str, any]:
        """Get performance trend for recent days"""
        df = self.get_batch_performance_metrics()
        
        if df.empty:
            return {'status': 'no_data'}
        
        # Filter recent data
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_df = df[df['timestamp'] >= cutoff_date]
        
        if recent_df.empty:
            return {'status': 'no_recent_data'}
        
        # Calculate trends
        metrics = {
            'period_days': days,
            'batches_processed': len(recent_df),
            'avg_success_rate': recent_df['success_rate'].mean(),
            'avg_high_confidence_rate': recent_df['high_confidence_rate'].mean(),
            'avg_processing_time': recent_df['processing_time'].mean(),
            'total_items_processed': recent_df['total_items'].sum(),
            'trend_analysis': self._analyze_trends(recent_df)
        }
        
        return metrics
    
    def _analyze_trends(self, df: pd.DataFrame) -> Dict[str, str]:
        """Analyze performance trends"""
        if len(df) < 2:
            return {'status': 'insufficient_data'}
        
        # Sort by timestamp
        df_sorted = df.sort_values('timestamp')
        
        # Calculate simple trends (first half vs second half)
        mid_point = len(df_sorted) // 2
        first_half = df_sorted.iloc[:mid_point]
        second_half = df_sorted.iloc[mid_point:]
        
        trends = {}
        
        # Success rate trend
        first_success = first_half['success_rate'].mean()
        second_success = second_half['success_rate'].mean()
        if second_success > first_success * 1.05:
            trends['success_rate'] = 'improving'
        elif second_success < first_success * 0.95:
            trends['success_rate'] = 'declining'
        else:
            trends['success_rate'] = 'stable'
        
        # High confidence rate trend
        first_confidence = first_half['high_confidence_rate'].mean()
        second_confidence = second_half['high_confidence_rate'].mean()
        if second_confidence > first_confidence * 1.05:
            trends['high_confidence_rate'] = 'improving'
        elif second_confidence < first_confidence * 0.95:
            trends['high_confidence_rate'] = 'declining'
        else:
            trends['high_confidence_rate'] = 'stable'
        
        return trends
    
    def _load_progress(self) -> Dict:
        """Load progress data from file"""
        if not self.progress_file.exists():
            return {}
        
        try:
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading progress data: {e}")
            return {}
    
    def _save_progress(self, progress_data: Dict):
        """Save progress data to file"""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving progress data: {e}")
    
    def _load_history(self) -> List[Dict]:
        """Load processing history from file"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading history data: {e}")
            return []
    
    def _save_history(self, history: List[Dict]):
        """Save processing history to file"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving history data: {e}")

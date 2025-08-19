# src/batch_processor/scaling_manager.py
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
import json
from pathlib import Path

try:
    from .processor import BatchResult
    from utils.logger import get_logger
except ImportError:
    # Fallback for when running as script
    from batch_processor.processor import BatchResult
    from utils.logger import get_logger

logger = get_logger(__name__)

class ScalingAction(Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    MAINTAIN = "maintain"

@dataclass
class ScalingDecision:
    action: ScalingAction
    new_batch_size: int
    reason: str
    confidence_threshold: float
    performance_metrics: Dict
    timestamp: datetime

@dataclass
class ScalingConfig:
    """Configuration for dynamic scaling behavior"""
    initial_batch_size: int = 50
    min_batch_size: int = 10
    max_batch_size: int = 200
    scaling_factor: float = 1.5
    high_confidence_threshold: float = 0.9
    low_confidence_threshold: float = 0.7
    processing_time_threshold: float = 5.0
    stability_required: bool = True
    min_batches_for_scaling: int = 3

class ScalingManager:
    """Manages dynamic batch size scaling based on performance metrics"""
    
    def __init__(self, config: Optional[ScalingConfig] = None, data_dir: Optional[Path] = None):
        self.config = config or ScalingConfig()
        self.current_batch_size = self.config.initial_batch_size
        self.scaling_history: List[ScalingDecision] = []
        
        # Setup data persistence
        if data_dir:
            self.data_dir = Path(data_dir)
            self.scaling_history_file = self.data_dir / "metrics" / "scaling_history.json"
            self.scaling_history_file.parent.mkdir(parents=True, exist_ok=True)
            self._load_scaling_history()
        else:
            self.data_dir = None
            self.scaling_history_file = None
    
    def evaluate_scaling(self, recent_batches: List[BatchResult]) -> ScalingDecision:
        """Evaluate whether to scale batch size based on recent performance"""
        if len(recent_batches) < self.config.min_batches_for_scaling:
            return self._decide_maintain("Insufficient batch history for scaling decision")
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(recent_batches)
        
        # Make scaling decision based on performance
        high_confidence_rate = performance_metrics['high_confidence_rate']
        avg_processing_time = performance_metrics['avg_processing_time']
        success_rate = performance_metrics['success_rate']
        stability_score = performance_metrics['stability_score']
        
        logger.debug(f"Scaling evaluation - Confidence: {high_confidence_rate:.2f}, "
                    f"Time: {avg_processing_time:.2f}s, Success: {success_rate:.2f}, "
                    f"Stability: {stability_score:.2f}")
        
        # Scaling decision logic
        if self._should_increase_batch_size(high_confidence_rate, avg_processing_time, 
                                          success_rate, stability_score):
            return self._decide_increase(performance_metrics)
        elif self._should_decrease_batch_size(high_confidence_rate, avg_processing_time, 
                                            success_rate, stability_score):
            return self._decide_decrease(performance_metrics)
        else:
            return self._decide_maintain("Performance metrics within acceptable range", 
                                       performance_metrics)
    
    def apply_scaling_decision(self, decision: ScalingDecision) -> bool:
        """Apply the scaling decision and update batch size"""
        old_batch_size = self.current_batch_size
        
        if decision.action == ScalingAction.INCREASE:
            new_size = min(int(self.current_batch_size * self.config.scaling_factor), 
                          self.config.max_batch_size)
        elif decision.action == ScalingAction.DECREASE:
            new_size = max(int(self.current_batch_size / self.config.scaling_factor), 
                          self.config.min_batch_size)
        else:
            new_size = self.current_batch_size
        
        # Update batch size if changed
        if new_size != self.current_batch_size:
            self.current_batch_size = new_size
            decision.new_batch_size = new_size
            self.scaling_history.append(decision)
            
            logger.info(f"Batch size scaled {decision.action.value}: {old_batch_size} → {new_size}")
            logger.info(f"Scaling reason: {decision.reason}")
            
            # Save scaling history
            if self.scaling_history_file:
                self._save_scaling_history()
            
            return True
        
        # No change needed
        decision.new_batch_size = self.current_batch_size
        self.scaling_history.append(decision)
        
        logger.debug(f"Batch size maintained at {self.current_batch_size}: {decision.reason}")
        
        if self.scaling_history_file:
            self._save_scaling_history()
        
        return False
    
    def get_current_batch_size(self) -> int:
        """Get the current batch size"""
        return self.current_batch_size
    
    def get_scaling_summary(self) -> Dict:
        """Get summary of scaling activity"""
        if not self.scaling_history:
            return {
                "total_decisions": 0,
                "current_batch_size": self.current_batch_size,
                "scaling_activity": "No scaling history"
            }
        
        increases = sum(1 for d in self.scaling_history if d.action == ScalingAction.INCREASE)
        decreases = sum(1 for d in self.scaling_history if d.action == ScalingAction.DECREASE)
        maintains = sum(1 for d in self.scaling_history if d.action == ScalingAction.MAINTAIN)
        
        return {
            "total_decisions": len(self.scaling_history),
            "increases": increases,
            "decreases": decreases,
            "maintains": maintains,
            "current_batch_size": self.current_batch_size,
            "initial_batch_size": self.config.initial_batch_size,
            "last_decision": self.scaling_history[-1].reason if self.scaling_history else None,
            "last_decision_time": self.scaling_history[-1].timestamp.isoformat() if self.scaling_history else None
        }
    
    def _calculate_performance_metrics(self, recent_batches: List[BatchResult]) -> Dict:
        """Calculate performance metrics from recent batches"""
        if not recent_batches:
            return {
                'high_confidence_rate': 0.0,
                'avg_processing_time': 0.0,
                'success_rate': 0.0,
                'stability_score': 0.0,
                'total_items': 0
            }
        
        # Calculate rates
        total_items = sum(batch.total_items for batch in recent_batches)
        high_confidence_items = sum(
            batch.confidence_distribution.get('High', 0) for batch in recent_batches
        )
        successful_items = sum(batch.successful_items for batch in recent_batches)
        
        high_confidence_rate = high_confidence_items / total_items if total_items > 0 else 0.0
        success_rate = successful_items / total_items if total_items > 0 else 0.0
        
        # Calculate average processing time
        avg_processing_time = sum(batch.processing_time for batch in recent_batches) / len(recent_batches)
        
        # Calculate stability score (lower variance = higher stability)
        confidence_rates = [
            batch.confidence_distribution.get('High', 0) / batch.total_items 
            if batch.total_items > 0 else 0.0
            for batch in recent_batches
        ]
        
        if len(confidence_rates) > 1:
            variance = sum((rate - high_confidence_rate) ** 2 for rate in confidence_rates) / len(confidence_rates)
            stability_score = max(0.0, 1.0 - variance)
        else:
            stability_score = 1.0
        
        return {
            'high_confidence_rate': high_confidence_rate,
            'avg_processing_time': avg_processing_time,
            'success_rate': success_rate,
            'stability_score': stability_score,
            'total_items': total_items,
            'batch_count': len(recent_batches)
        }
    
    def _should_increase_batch_size(self, high_confidence_rate: float, avg_processing_time: float,
                                  success_rate: float, stability_score: float) -> bool:
        """Determine if batch size should be increased"""
        # Only increase if performance is excellent and stable
        return (
            high_confidence_rate > self.config.high_confidence_threshold and
            avg_processing_time < self.config.processing_time_threshold and
            success_rate > 0.95 and
            (not self.config.stability_required or stability_score > 0.8) and
            self.current_batch_size < self.config.max_batch_size
        )
    
    def _should_decrease_batch_size(self, high_confidence_rate: float, avg_processing_time: float,
                                  success_rate: float, stability_score: float) -> bool:
        """Determine if batch size should be decreased"""
        # Decrease if performance is poor or processing is too slow
        return (
            (high_confidence_rate < self.config.low_confidence_threshold or
             avg_processing_time > self.config.processing_time_threshold or
             success_rate < 0.8) and
            self.current_batch_size > self.config.min_batch_size
        )
    
    def _decide_increase(self, performance_metrics: Dict) -> ScalingDecision:
        """Create decision to increase batch size"""
        new_size = min(int(self.current_batch_size * self.config.scaling_factor), 
                      self.config.max_batch_size)
        
        reason = (f"High performance: {performance_metrics['high_confidence_rate']:.1%} confidence, "
                 f"{performance_metrics['avg_processing_time']:.1f}s processing time")
        
        return ScalingDecision(
            action=ScalingAction.INCREASE,
            new_batch_size=new_size,
            reason=reason,
            confidence_threshold=performance_metrics['high_confidence_rate'],
            performance_metrics=performance_metrics,
            timestamp=datetime.now()
        )
    
    def _decide_decrease(self, performance_metrics: Dict) -> ScalingDecision:
        """Create decision to decrease batch size"""
        new_size = max(int(self.current_batch_size / self.config.scaling_factor), 
                      self.config.min_batch_size)
        
        reason = (f"Poor performance: {performance_metrics['high_confidence_rate']:.1%} confidence, "
                 f"{performance_metrics['avg_processing_time']:.1f}s processing time")
        
        return ScalingDecision(
            action=ScalingAction.DECREASE,
            new_batch_size=new_size,
            reason=reason,
            confidence_threshold=performance_metrics['high_confidence_rate'],
            performance_metrics=performance_metrics,
            timestamp=datetime.now()
        )
    
    def _decide_maintain(self, reason: str, performance_metrics: Optional[Dict] = None) -> ScalingDecision:
        """Create decision to maintain current batch size"""
        return ScalingDecision(
            action=ScalingAction.MAINTAIN,
            new_batch_size=self.current_batch_size,
            reason=reason,
            confidence_threshold=performance_metrics.get('high_confidence_rate', 0.0) if performance_metrics else 0.0,
            performance_metrics=performance_metrics or {},
            timestamp=datetime.now()
        )
    
    def _save_scaling_history(self):
        """Save scaling history to file"""
        if not self.scaling_history_file:
            return
        
        try:
            history_data = []
            for decision in self.scaling_history:
                decision_dict = {
                    'action': decision.action.value,
                    'new_batch_size': decision.new_batch_size,
                    'reason': decision.reason,
                    'confidence_threshold': decision.confidence_threshold,
                    'performance_metrics': decision.performance_metrics,
                    'timestamp': decision.timestamp.isoformat()
                }
                history_data.append(decision_dict)
            
            with open(self.scaling_history_file, 'w') as f:
                json.dump({
                    'last_updated': datetime.now().isoformat(),
                    'current_batch_size': self.current_batch_size,
                    'scaling_history': history_data
                }, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving scaling history: {e}")
    
    def _load_scaling_history(self):
        """Load scaling history from file"""
        if not self.scaling_history_file or not self.scaling_history_file.exists():
            return
        
        try:
            with open(self.scaling_history_file, 'r') as f:
                data = json.load(f)
            
            # Restore current batch size
            self.current_batch_size = data.get('current_batch_size', self.config.initial_batch_size)
            
            # Restore scaling history
            for decision_data in data.get('scaling_history', []):
                decision = ScalingDecision(
                    action=ScalingAction(decision_data['action']),
                    new_batch_size=decision_data['new_batch_size'],
                    reason=decision_data['reason'],
                    confidence_threshold=decision_data['confidence_threshold'],
                    performance_metrics=decision_data['performance_metrics'],
                    timestamp=datetime.fromisoformat(decision_data['timestamp'])
                )
                self.scaling_history.append(decision)
            
            logger.info(f"Loaded scaling history: {len(self.scaling_history)} decisions, "
                       f"current batch size: {self.current_batch_size}")
                
        except Exception as e:
            logger.error(f"Error loading scaling history: {e}")

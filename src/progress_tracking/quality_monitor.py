# src/progress_tracking/quality_monitor.py
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from pathlib import Path
from dataclasses import dataclass
import statistics

try:
    from batch_processor.processor import BatchResult, ProcessingResult
    from batch_processor.feedback_loop import FeedbackItem, FeedbackSummary
    from utils.logger import get_logger
except ImportError:
    # Fallback for when running as script  
    from batch_processor.processor import BatchResult, ProcessingResult
    from batch_processor.feedback_loop import FeedbackItem, FeedbackSummary
    from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class QualityMetrics:
    """Quality metrics for a specific time period"""
    timestamp: str
    batch_id: str
    total_items: int
    confidence_distribution: Dict[str, int]
    average_confidence: float
    success_rate: float
    high_confidence_rate: float
    processing_time_avg: float
    improvement_rate: float = 0.0

@dataclass
class TrendAnalysis:
    """Analysis of quality trends over time"""
    period_start: str
    period_end: str
    total_batches: int
    overall_improvement: float
    confidence_trend: str  # 'improving', 'stable', 'declining'
    success_rate_trend: str
    quality_consistency: float
    recommendations: List[str]

class QualityMonitor:
    """Monitors and tracks quality metrics over time"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.metrics_dir = self.data_dir / "metrics"
        self.metrics_dir.mkdir(exist_ok=True)
        
        self.quality_history: List[QualityMetrics] = []
        self.baseline_metrics: Optional[QualityMetrics] = None
        
        # Load existing quality history
        self._load_quality_history()
    
    def track_confidence_distribution(self, batch_result: BatchResult) -> QualityMetrics:
        """Track confidence level distribution over time"""
        logger.debug(f"Tracking confidence distribution for batch {batch_result.batch_id}")
        
        # Calculate distribution
        distribution = batch_result.confidence_distribution.copy()
        
        # Calculate average confidence score
        confidence_scores = [r.confidence_score for r in batch_result.results if r.success]
        avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.0
        
        # Calculate processing time average
        processing_times = [r.processing_time for r in batch_result.results]
        avg_processing_time = statistics.mean(processing_times) if processing_times else 0.0
        
        # Calculate improvement rate
        improvement_rate = self._calculate_improvement_rate(avg_confidence)
        
        # Create quality metrics
        metrics = QualityMetrics(
            timestamp=datetime.now().isoformat(),
            batch_id=batch_result.batch_id,
            total_items=batch_result.total_items,
            confidence_distribution=distribution,
            average_confidence=round(avg_confidence, 3),
            success_rate=batch_result.summary.get('success_rate', 0.0),
            high_confidence_rate=batch_result.summary.get('high_confidence_rate', 0.0),
            processing_time_avg=round(avg_processing_time, 3),
            improvement_rate=improvement_rate
        )
        
        # Add to history
        self.quality_history.append(metrics)
        
        # Set baseline if first metrics
        if self.baseline_metrics is None:
            self.baseline_metrics = metrics
            logger.info("Set baseline quality metrics")
        
        # Save metrics
        self._save_quality_metrics(metrics)
        
        logger.info(f"Tracked quality metrics: {avg_confidence:.3f} avg confidence, "
                   f"{batch_result.summary.get('high_confidence_rate', 0):.1%} high confidence rate")
        
        return metrics
    
    def calculate_improvement_rate(self, window_size: int = 5) -> float:
        """Calculate improvement rate based on historical data"""
        if len(self.quality_history) < 2:
            return 0.0
        
        # Use recent window for calculation
        recent_metrics = self.quality_history[-window_size:] if len(self.quality_history) >= window_size else self.quality_history
        
        if len(recent_metrics) < 2:
            return 0.0
        
        # Calculate linear trend of average confidence
        x_values = list(range(len(recent_metrics)))
        y_values = [m.average_confidence for m in recent_metrics]
        
        # Simple linear regression slope
        n = len(recent_metrics)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        return round(slope, 4)
    
    def _calculate_improvement_rate(self, current_confidence: float) -> float:
        """Calculate improvement rate compared to baseline"""
        if self.baseline_metrics is None:
            return 0.0
        
        baseline_confidence = self.baseline_metrics.average_confidence
        if baseline_confidence == 0:
            return 0.0
        
        improvement = (current_confidence - baseline_confidence) / baseline_confidence
        return round(improvement, 4)
    
    def analyze_quality_trends(self, days: int = 30) -> TrendAnalysis:
        """Analyze quality trends over specified period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter metrics for the period
        period_metrics = [
            m for m in self.quality_history
            if datetime.fromisoformat(m.timestamp) >= cutoff_date
        ]
        
        if len(period_metrics) < 2:
            return TrendAnalysis(
                period_start=cutoff_date.isoformat(),
                period_end=datetime.now().isoformat(),
                total_batches=len(period_metrics),
                overall_improvement=0.0,
                confidence_trend="insufficient_data",
                success_rate_trend="insufficient_data",
                quality_consistency=0.0,
                recommendations=["Need more data for trend analysis"]
            )
        
        # Calculate trends
        confidence_values = [m.average_confidence for m in period_metrics]
        success_rates = [m.success_rate for m in period_metrics]
        
        # Overall improvement
        overall_improvement = confidence_values[-1] - confidence_values[0]
        
        # Trend analysis
        confidence_trend = self._analyze_trend(confidence_values)
        success_rate_trend = self._analyze_trend(success_rates)
        
        # Quality consistency (lower standard deviation = more consistent)
        quality_consistency = 1.0 - min(statistics.stdev(confidence_values), 1.0) if len(confidence_values) > 1 else 1.0
        
        # Generate recommendations
        recommendations = self._generate_recommendations(period_metrics, confidence_trend, success_rate_trend)
        
        return TrendAnalysis(
            period_start=period_metrics[0].timestamp,
            period_end=period_metrics[-1].timestamp,
            total_batches=len(period_metrics),
            overall_improvement=round(overall_improvement, 3),
            confidence_trend=confidence_trend,
            success_rate_trend=success_rate_trend,
            quality_consistency=round(quality_consistency, 3),
            recommendations=recommendations
        )
    
    def _analyze_trend(self, values: List[float]) -> str:
        """Analyze trend direction from list of values"""
        if len(values) < 3:
            return "insufficient_data"
        
        # Calculate trend using simple linear regression
        n = len(values)
        x_values = list(range(n))
        
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
        sum_x2 = sum(x * x for x in x_values)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return "stable"
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"
    
    def _generate_recommendations(self, metrics: List[QualityMetrics], 
                                confidence_trend: str, success_rate_trend: str) -> List[str]:
        """Generate improvement recommendations based on trends"""
        recommendations = []
        
        if confidence_trend == "declining":
            recommendations.append("Quality declining - review recent rule changes")
            recommendations.append("Consider increasing manual review threshold")
        
        if success_rate_trend == "declining":
            recommendations.append("Success rate declining - check for data quality issues")
        
        # Check for low high-confidence rates
        recent_high_conf_rates = [m.high_confidence_rate for m in metrics[-5:]]
        avg_high_conf_rate = statistics.mean(recent_high_conf_rates) if recent_high_conf_rates else 0
        
        if avg_high_conf_rate < 0.6:
            recommendations.append("Low high-confidence rate - consider rule refinements")
        
        # Check for processing time issues
        recent_proc_times = [m.processing_time_avg for m in metrics[-5:]]
        avg_proc_time = statistics.mean(recent_proc_times) if recent_proc_times else 0
        
        if avg_proc_time > 2.0:  # More than 2 seconds average
            recommendations.append("High processing times - optimize description generation")
        
        # Check consistency
        if len(metrics) > 5:
            recent_confidences = [m.average_confidence for m in metrics[-10:]]
            if statistics.stdev(recent_confidences) > 0.15:
                recommendations.append("High quality variance - review system stability")
        
        if not recommendations:
            recommendations.append("Quality metrics look good - continue current approach")
        
        return recommendations
    
    def get_quality_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive quality dashboard data"""
        if not self.quality_history:
            return {"no_data": True}
        
        recent_metrics = self.quality_history[-1]
        trend_analysis = self.analyze_quality_trends(days=14)
        
        # Calculate comparison with baseline
        baseline_comparison = {}
        if self.baseline_metrics:
            baseline_comparison = {
                'confidence_improvement': recent_metrics.average_confidence - self.baseline_metrics.average_confidence,
                'success_rate_improvement': recent_metrics.success_rate - self.baseline_metrics.success_rate,
                'high_confidence_improvement': recent_metrics.high_confidence_rate - self.baseline_metrics.high_confidence_rate
            }
        
        # Recent performance (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_week_metrics = [
            m for m in self.quality_history
            if datetime.fromisoformat(m.timestamp) >= week_ago
        ]
        
        week_stats = {}
        if recent_week_metrics:
            week_stats = {
                'avg_confidence': round(statistics.mean([m.average_confidence for m in recent_week_metrics]), 3),
                'avg_success_rate': round(statistics.mean([m.success_rate for m in recent_week_metrics]), 3),
                'avg_high_confidence_rate': round(statistics.mean([m.high_confidence_rate for m in recent_week_metrics]), 3),
                'batches_processed': len(recent_week_metrics),
                'total_items': sum(m.total_items for m in recent_week_metrics)
            }
        
        return {
            'current_metrics': {
                'average_confidence': recent_metrics.average_confidence,
                'success_rate': recent_metrics.success_rate,
                'high_confidence_rate': recent_metrics.high_confidence_rate,
                'confidence_distribution': recent_metrics.confidence_distribution,
                'last_updated': recent_metrics.timestamp
            },
            'baseline_comparison': baseline_comparison,
            'trend_analysis': {
                'confidence_trend': trend_analysis.confidence_trend,
                'success_rate_trend': trend_analysis.success_rate_trend,
                'overall_improvement': trend_analysis.overall_improvement,
                'quality_consistency': trend_analysis.quality_consistency
            },
            'recent_week_performance': week_stats,
            'recommendations': trend_analysis.recommendations,
            'total_batches_tracked': len(self.quality_history)
        }
    
    def detect_quality_alerts(self) -> List[Dict[str, str]]:
        """Detect quality issues that need attention"""
        alerts = []
        
        if len(self.quality_history) < 2:
            return alerts
        
        recent_metrics = self.quality_history[-1]
        previous_metrics = self.quality_history[-2] if len(self.quality_history) > 1 else None
        
        # Significant confidence drop
        if previous_metrics and (recent_metrics.average_confidence - previous_metrics.average_confidence) < -0.1:
            alerts.append({
                'type': 'confidence_drop',
                'severity': 'high',
                'message': f"Significant confidence drop: {previous_metrics.average_confidence:.3f} → {recent_metrics.average_confidence:.3f}",
                'timestamp': recent_metrics.timestamp
            })
        
        # Low success rate
        if recent_metrics.success_rate < 0.8:
            alerts.append({
                'type': 'low_success_rate',
                'severity': 'medium',
                'message': f"Low success rate: {recent_metrics.success_rate:.1%}",
                'timestamp': recent_metrics.timestamp
            })
        
        # Very low high-confidence rate
        if recent_metrics.high_confidence_rate < 0.4:
            alerts.append({
                'type': 'low_high_confidence',
                'severity': 'medium',
                'message': f"Low high-confidence rate: {recent_metrics.high_confidence_rate:.1%}",
                'timestamp': recent_metrics.timestamp
            })
        
        # High processing time
        if recent_metrics.processing_time_avg > 3.0:
            alerts.append({
                'type': 'high_processing_time',
                'severity': 'low',
                'message': f"High average processing time: {recent_metrics.processing_time_avg:.2f}s",
                'timestamp': recent_metrics.timestamp
            })
        
        return alerts
    
    def _save_quality_metrics(self, metrics: QualityMetrics):
        """Save quality metrics to file"""
        try:
            metrics_file = self.metrics_dir / f"quality_metrics_{metrics.batch_id}.json"
            
            data = {
                'timestamp': metrics.timestamp,
                'batch_id': metrics.batch_id,
                'total_items': metrics.total_items,
                'confidence_distribution': metrics.confidence_distribution,
                'average_confidence': metrics.average_confidence,
                'success_rate': metrics.success_rate,
                'high_confidence_rate': metrics.high_confidence_rate,
                'processing_time_avg': metrics.processing_time_avg,
                'improvement_rate': metrics.improvement_rate
            }
            
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Also save to consolidated history file
            self._save_quality_history()
            
        except Exception as e:
            logger.error(f"Error saving quality metrics: {e}")
    
    def _save_quality_history(self):
        """Save consolidated quality history"""
        try:
            history_file = self.metrics_dir / "quality_history.json"
            
            history_data = {
                'baseline_metrics': {
                    'timestamp': self.baseline_metrics.timestamp,
                    'average_confidence': self.baseline_metrics.average_confidence,
                    'success_rate': self.baseline_metrics.success_rate,
                    'high_confidence_rate': self.baseline_metrics.high_confidence_rate
                } if self.baseline_metrics else None,
                'metrics_history': [
                    {
                        'timestamp': m.timestamp,
                        'batch_id': m.batch_id,
                        'total_items': m.total_items,
                        'confidence_distribution': m.confidence_distribution,
                        'average_confidence': m.average_confidence,
                        'success_rate': m.success_rate,
                        'high_confidence_rate': m.high_confidence_rate,
                        'processing_time_avg': m.processing_time_avg,
                        'improvement_rate': m.improvement_rate
                    }
                    for m in self.quality_history[-50:]  # Keep last 50 entries
                ],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving quality history: {e}")
    
    def _load_quality_history(self):
        """Load existing quality history from file"""
        try:
            history_file = self.metrics_dir / "quality_history.json"
            
            if not history_file.exists():
                return
            
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load baseline metrics
            if data.get('baseline_metrics'):
                baseline_data = data['baseline_metrics']
                self.baseline_metrics = QualityMetrics(
                    timestamp=baseline_data['timestamp'],
                    batch_id='baseline',
                    total_items=0,
                    confidence_distribution={},
                    average_confidence=baseline_data['average_confidence'],
                    success_rate=baseline_data['success_rate'],
                    high_confidence_rate=baseline_data['high_confidence_rate'],
                    processing_time_avg=0.0
                )
            
            # Load metrics history
            for metric_data in data.get('metrics_history', []):
                metrics = QualityMetrics(
                    timestamp=metric_data['timestamp'],
                    batch_id=metric_data['batch_id'],
                    total_items=metric_data['total_items'],
                    confidence_distribution=metric_data['confidence_distribution'],
                    average_confidence=metric_data['average_confidence'],
                    success_rate=metric_data['success_rate'],
                    high_confidence_rate=metric_data['high_confidence_rate'],
                    processing_time_avg=metric_data['processing_time_avg'],
                    improvement_rate=metric_data.get('improvement_rate', 0.0)
                )
                self.quality_history.append(metrics)
            
            logger.info(f"Loaded {len(self.quality_history)} quality metrics from history")
            
        except Exception as e:
            logger.error(f"Error loading quality history: {e}")
    
    def export_quality_data(self, filepath: str, days: int = None):
        """Export quality data for external analysis"""
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            export_metrics = [
                m for m in self.quality_history
                if datetime.fromisoformat(m.timestamp) >= cutoff_date
            ]
        else:
            export_metrics = self.quality_history
        
        export_data = {
            'export_info': {
                'exported_at': datetime.now().isoformat(),
                'total_metrics': len(export_metrics),
                'period_days': days,
                'baseline_included': self.baseline_metrics is not None
            },
            'baseline_metrics': {
                'timestamp': self.baseline_metrics.timestamp,
                'average_confidence': self.baseline_metrics.average_confidence,
                'success_rate': self.baseline_metrics.success_rate,
                'high_confidence_rate': self.baseline_metrics.high_confidence_rate
            } if self.baseline_metrics else None,
            'quality_metrics': [
                {
                    'timestamp': m.timestamp,
                    'batch_id': m.batch_id,
                    'total_items': m.total_items,
                    'confidence_distribution': m.confidence_distribution,
                    'average_confidence': m.average_confidence,
                    'success_rate': m.success_rate,
                    'high_confidence_rate': m.high_confidence_rate,
                    'processing_time_avg': m.processing_time_avg,
                    'improvement_rate': m.improvement_rate
                }
                for m in export_metrics
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(export_metrics)} quality metrics to {filepath}")


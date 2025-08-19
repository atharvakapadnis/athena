# src/progress_tracking/performance_analyzer.py
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import statistics

try:
    from .metrics_collector import MetricsCollector, ProcessingMetrics, RuleMetrics
    from utils.logger import get_logger
except ImportError:
    # Fallback for when running as script
    from metrics_collector import MetricsCollector, ProcessingMetrics, RuleMetrics
    from utils.logger import get_logger

logger = get_logger(__name__)

class PerformanceAnalyzer:
    """Analyzes performance trends and identifies bottlenecks"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        
        # Thresholds for performance analysis
        self.confidence_threshold = 0.6
        self.success_rate_threshold = 0.8
        self.processing_time_threshold = 2.0  # seconds
        self.usage_threshold = 10  # minimum usage count for analysis
        
        logger.debug("PerformanceAnalyzer initialized")
    
    def calculate_trends(self, window_size: int = 10) -> Dict[str, float]:
        """Calculate performance trends over recent batches"""
        recent_metrics = self.metrics_collector.processing_history[-window_size:]
        
        if len(recent_metrics) < 2:
            logger.warning("Insufficient data for trend calculation")
            return {
                "success_rate_trend": 0.0,
                "processing_time_trend": 0.0,
                "confidence_trend": 0.0,
                "average_success_rate": 0.0,
                "success_rate_volatility": 0.0,
                "data_points": len(recent_metrics)
            }
        
        # Extract time series data
        success_rates = [m.success_rate for m in recent_metrics]
        processing_times = [m.processing_time for m in recent_metrics]
        confidence_scores = [m.average_confidence for m in recent_metrics]
        
        # Calculate linear trends using numpy polyfit
        x_values = np.array(range(len(recent_metrics)))
        
        success_trend = np.polyfit(x_values, success_rates, 1)[0] if len(success_rates) > 1 else 0.0
        time_trend = np.polyfit(x_values, processing_times, 1)[0] if len(processing_times) > 1 else 0.0
        confidence_trend = np.polyfit(x_values, confidence_scores, 1)[0] if len(confidence_scores) > 1 else 0.0
        
        # Calculate additional statistics
        avg_success_rate = np.mean(success_rates)
        success_volatility = np.std(success_rates) if len(success_rates) > 1 else 0.0
        
        trends = {
            "success_rate_trend": round(float(success_trend), 6),
            "processing_time_trend": round(float(time_trend), 6),
            "confidence_trend": round(float(confidence_trend), 6),
            "average_success_rate": round(float(avg_success_rate), 3),
            "success_rate_volatility": round(float(success_volatility), 3),
            "data_points": len(recent_metrics),
            "window_size": window_size
        }
        
        logger.debug(f"Calculated trends over {len(recent_metrics)} batches: "
                    f"success trend = {trends['success_rate_trend']:.6f}, "
                    f"confidence trend = {trends['confidence_trend']:.6f}")
        
        return trends
    
    def identify_bottlenecks(self) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks in the system"""
        bottlenecks = []
        
        # Analyze rule performance bottlenecks
        rule_bottlenecks = self._analyze_rule_bottlenecks()
        bottlenecks.extend(rule_bottlenecks)
        
        # Analyze processing performance bottlenecks
        processing_bottlenecks = self._analyze_processing_bottlenecks()
        bottlenecks.extend(processing_bottlenecks)
        
        # Analyze trend-based bottlenecks
        trend_bottlenecks = self._analyze_trend_bottlenecks()
        bottlenecks.extend(trend_bottlenecks)
        
        logger.info(f"Identified {len(bottlenecks)} performance bottlenecks")
        
        return bottlenecks
    
    def _analyze_rule_bottlenecks(self) -> List[Dict[str, Any]]:
        """Analyze rule-specific performance issues"""
        bottlenecks = []
        
        for rule_id, metrics in self.metrics_collector.rule_performance.items():
            # Low performing rules with sufficient usage
            if (metrics.usage_count >= self.usage_threshold and 
                metrics.average_confidence < self.confidence_threshold):
                
                bottlenecks.append({
                    "type": "low_performing_rule",
                    "severity": "medium",
                    "rule_id": rule_id,
                    "rule_name": metrics.rule_name,
                    "average_confidence": round(metrics.average_confidence, 3),
                    "usage_count": metrics.usage_count,
                    "success_rate": round(metrics.success_count / metrics.usage_count, 3),
                    "recommendation": f"Review and improve rule '{metrics.rule_name or rule_id}' - low confidence scores"
                })
            
            # Rules with very low success rates
            success_rate = metrics.success_count / metrics.usage_count if metrics.usage_count > 0 else 0
            if metrics.usage_count >= self.usage_threshold and success_rate < 0.5:
                bottlenecks.append({
                    "type": "failing_rule",
                    "severity": "high",
                    "rule_id": rule_id,
                    "rule_name": metrics.rule_name,
                    "success_rate": round(success_rate, 3),
                    "usage_count": metrics.usage_count,
                    "recommendation": f"Critical: Rule '{metrics.rule_name or rule_id}' failing frequently - immediate review needed"
                })
        
        return bottlenecks
    
    def _analyze_processing_bottlenecks(self) -> List[Dict[str, Any]]:
        """Analyze processing performance issues"""
        bottlenecks = []
        
        if not self.metrics_collector.processing_history:
            return bottlenecks
        
        recent_metrics = self.metrics_collector.processing_history[-5:]  # Last 5 batches
        
        # High processing times
        avg_processing_time = statistics.mean([m.processing_time for m in recent_metrics])
        if avg_processing_time > self.processing_time_threshold:
            bottlenecks.append({
                "type": "high_processing_time",
                "severity": "medium",
                "average_processing_time": round(avg_processing_time, 2),
                "threshold": self.processing_time_threshold,
                "affected_batches": len([m for m in recent_metrics if m.processing_time > self.processing_time_threshold]),
                "recommendation": "Optimize description generation pipeline - processing times are elevated"
            })
        
        # Low overall success rates
        avg_success_rate = statistics.mean([m.success_rate for m in recent_metrics])
        if avg_success_rate < self.success_rate_threshold:
            bottlenecks.append({
                "type": "low_success_rate",
                "severity": "high",
                "average_success_rate": round(avg_success_rate, 3),
                "threshold": self.success_rate_threshold,
                "affected_batches": len(recent_metrics),
                "recommendation": "Critical: Low success rate across batches - review data quality and processing logic"
            })
        
        # High variance in confidence scores
        confidence_scores = [m.average_confidence for m in recent_metrics if m.average_confidence > 0]
        if len(confidence_scores) > 1:
            confidence_std = statistics.stdev(confidence_scores)
            if confidence_std > 0.2:  # High variance threshold
                bottlenecks.append({
                    "type": "confidence_variance",
                    "severity": "low",
                    "confidence_std": round(confidence_std, 3),
                    "confidence_range": [round(min(confidence_scores), 3), round(max(confidence_scores), 3)],
                    "recommendation": "High variance in confidence scores - review system stability"
                })
        
        return bottlenecks
    
    def _analyze_trend_bottlenecks(self) -> List[Dict[str, Any]]:
        """Analyze trend-based performance issues"""
        bottlenecks = []
        
        if len(self.metrics_collector.processing_history) < 3:
            return bottlenecks
        
        trends = self.calculate_trends(window_size=10)
        
        # Declining success rate trend
        if trends["success_rate_trend"] < -0.01:  # Declining by more than 1% per batch
            bottlenecks.append({
                "type": "declining_success_trend",
                "severity": "high",
                "trend_slope": trends["success_rate_trend"],
                "current_average": trends["average_success_rate"],
                "recommendation": "Success rate is declining - investigate recent changes and data quality"
            })
        
        # Declining confidence trend
        if trends["confidence_trend"] < -0.01:  # Declining confidence
            bottlenecks.append({
                "type": "declining_confidence_trend",
                "severity": "medium",
                "trend_slope": trends["confidence_trend"],
                "recommendation": "Confidence scores are declining - review rule effectiveness and data patterns"
            })
        
        # Increasing processing time trend
        if trends["processing_time_trend"] > 0.1:  # Increasing by more than 0.1s per batch
            bottlenecks.append({
                "type": "increasing_processing_time",
                "severity": "medium",
                "trend_slope": trends["processing_time_trend"],
                "recommendation": "Processing times are increasing - check for performance degradation"
            })
        
        # High volatility in success rates
        if trends["success_rate_volatility"] > 0.15:  # High volatility
            bottlenecks.append({
                "type": "high_volatility",
                "severity": "low",
                "volatility": trends["success_rate_volatility"],
                "recommendation": "High variability in success rates - investigate system stability"
            })
        
        return bottlenecks
    
    def analyze_performance_regression(self, baseline_days: int = 30, 
                                     comparison_days: int = 7) -> Dict[str, Any]:
        """Analyze performance regression by comparing recent performance to baseline"""
        now = datetime.now()
        baseline_cutoff = now - timedelta(days=baseline_days)
        comparison_cutoff = now - timedelta(days=comparison_days)
        
        # Get baseline metrics (older period)
        baseline_metrics = [
            m for m in self.metrics_collector.processing_history
            if baseline_cutoff <= datetime.fromisoformat(m.timestamp.isoformat()) < comparison_cutoff
        ]
        
        # Get recent metrics (recent period)
        recent_metrics = [
            m for m in self.metrics_collector.processing_history
            if datetime.fromisoformat(m.timestamp.isoformat()) >= comparison_cutoff
        ]
        
        if not baseline_metrics or not recent_metrics:
            return {
                "status": "insufficient_data",
                "baseline_batches": len(baseline_metrics),
                "recent_batches": len(recent_metrics)
            }
        
        # Calculate baseline statistics
        baseline_stats = {
            "success_rate": statistics.mean([m.success_rate for m in baseline_metrics]),
            "confidence": statistics.mean([m.average_confidence for m in baseline_metrics]),
            "processing_time": statistics.mean([m.processing_time for m in baseline_metrics]),
            "high_confidence_rate": statistics.mean([
                m.high_confidence / m.total_items for m in baseline_metrics if m.total_items > 0
            ])
        }
        
        # Calculate recent statistics
        recent_stats = {
            "success_rate": statistics.mean([m.success_rate for m in recent_metrics]),
            "confidence": statistics.mean([m.average_confidence for m in recent_metrics]),
            "processing_time": statistics.mean([m.processing_time for m in recent_metrics]),
            "high_confidence_rate": statistics.mean([
                m.high_confidence / m.total_items for m in recent_metrics if m.total_items > 0
            ])
        }
        
        # Calculate changes
        changes = {
            "success_rate_change": recent_stats["success_rate"] - baseline_stats["success_rate"],
            "confidence_change": recent_stats["confidence"] - baseline_stats["confidence"],
            "processing_time_change": recent_stats["processing_time"] - baseline_stats["processing_time"],
            "high_confidence_rate_change": recent_stats["high_confidence_rate"] - baseline_stats["high_confidence_rate"]
        }
        
        # Determine regression status
        regression_indicators = []
        if changes["success_rate_change"] < -0.05:  # 5% drop
            regression_indicators.append("success_rate")
        if changes["confidence_change"] < -0.05:  # 5% drop
            regression_indicators.append("confidence")
        if changes["processing_time_change"] > 0.5:  # 0.5s increase
            regression_indicators.append("processing_time")
        if changes["high_confidence_rate_change"] < -0.05:  # 5% drop
            regression_indicators.append("high_confidence_rate")
        
        regression_status = "regression_detected" if regression_indicators else "no_regression"
        
        return {
            "status": regression_status,
            "baseline_period": f"{baseline_days} days",
            "comparison_period": f"{comparison_days} days",
            "baseline_batches": len(baseline_metrics),
            "recent_batches": len(recent_metrics),
            "baseline_stats": {k: round(v, 3) for k, v in baseline_stats.items()},
            "recent_stats": {k: round(v, 3) for k, v in recent_stats.items()},
            "changes": {k: round(v, 3) for k, v in changes.items()},
            "regression_indicators": regression_indicators,
            "severity": len(regression_indicators)
        }
    
    def get_performance_insights(self) -> Dict[str, Any]:
        """Get comprehensive performance insights"""
        insights = {
            "trends": self.calculate_trends(),
            "bottlenecks": self.identify_bottlenecks(),
            "regression_analysis": self.analyze_performance_regression(),
            "rule_performance": self.metrics_collector.get_rule_performance_summary(),
            "processing_performance": self.metrics_collector.get_processing_summary()
        }
        
        # Add summary insights
        insights["summary"] = self._generate_performance_summary(insights)
        
        return insights
    
    def _generate_performance_summary(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of key performance insights"""
        summary = {
            "overall_health": "good",
            "key_metrics": {},
            "priority_actions": [],
            "positive_trends": [],
            "concerns": []
        }
        
        # Analyze overall health
        bottleneck_count = len(insights["bottlenecks"])
        high_severity_bottlenecks = len([b for b in insights["bottlenecks"] if b.get("severity") == "high"])
        
        if high_severity_bottlenecks > 0:
            summary["overall_health"] = "critical"
        elif bottleneck_count > 3:
            summary["overall_health"] = "poor"
        elif bottleneck_count > 1:
            summary["overall_health"] = "fair"
        
        # Key metrics
        trends = insights["trends"]
        summary["key_metrics"] = {
            "current_success_rate": trends.get("average_success_rate", 0),
            "success_trend": "improving" if trends.get("success_rate_trend", 0) > 0.01 else "stable" if trends.get("success_rate_trend", 0) > -0.01 else "declining",
            "confidence_trend": "improving" if trends.get("confidence_trend", 0) > 0.01 else "stable" if trends.get("confidence_trend", 0) > -0.01 else "declining",
            "total_bottlenecks": bottleneck_count
        }
        
        # Priority actions from high-severity bottlenecks
        for bottleneck in insights["bottlenecks"]:
            if bottleneck.get("severity") == "high":
                summary["priority_actions"].append(bottleneck.get("recommendation", "Review high-severity issue"))
        
        # Positive trends
        if trends.get("success_rate_trend", 0) > 0.01:
            summary["positive_trends"].append("Success rate is improving")
        if trends.get("confidence_trend", 0) > 0.01:
            summary["positive_trends"].append("Confidence scores are improving")
        
        # Concerns from medium/low severity bottlenecks
        for bottleneck in insights["bottlenecks"]:
            if bottleneck.get("severity") in ["medium", "low"]:
                summary["concerns"].append(bottleneck.get("recommendation", "Monitor performance issue"))
        
        return summary

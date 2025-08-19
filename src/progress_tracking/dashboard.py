# src/progress_tracking/dashboard.py
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

try:
    from .metrics_collector import MetricsCollector
    from .performance_analyzer import PerformanceAnalyzer
    from utils.logger import get_logger
except ImportError:
    # Fallback for when running as script
    from metrics_collector import MetricsCollector
    from performance_analyzer import PerformanceAnalyzer
    from utils.logger import get_logger

logger = get_logger(__name__)

class ProgressDashboard:
    """Provides comprehensive progress dashboard and reporting functionality"""
    
    def __init__(self, metrics_collector: MetricsCollector, analyzer: PerformanceAnalyzer):
        self.metrics_collector = metrics_collector
        self.analyzer = analyzer
        
        logger.debug("ProgressDashboard initialized")
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate a comprehensive progress summary"""
        if not self.metrics_collector.processing_history:
            return {
                "status": "no_data",
                "message": "No processing data available",
                "timestamp": datetime.now().isoformat()
            }
        
        logger.debug("Generating comprehensive summary report")
        
        # Get latest metrics and analysis
        latest_metrics = self.metrics_collector.processing_history[-1]
        trends = self.analyzer.calculate_trends()
        bottlenecks = self.analyzer.identify_bottlenecks()
        regression_analysis = self.analyzer.analyze_performance_regression()
        performance_insights = self.analyzer.get_performance_insights()
        
        # Generate the comprehensive report
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "data_period": self._get_data_period(),
                "total_batches_analyzed": len(self.metrics_collector.processing_history)
            },
            
            "current_status": {
                "latest_batch": {
                    "batch_id": latest_metrics.batch_id,
                    "timestamp": latest_metrics.timestamp.isoformat(),
                    "total_items": latest_metrics.total_items,
                    "success_rate": round(latest_metrics.success_rate, 3),
                    "average_confidence": round(latest_metrics.average_confidence, 3),
                    "processing_time": round(latest_metrics.processing_time, 2)
                },
                "confidence_distribution": {
                    "high": latest_metrics.high_confidence,
                    "medium": latest_metrics.medium_confidence,
                    "low": latest_metrics.low_confidence,
                    "high_percentage": round(latest_metrics.high_confidence / latest_metrics.total_items * 100, 1) if latest_metrics.total_items > 0 else 0
                },
                "overall_health": performance_insights["summary"]["overall_health"]
            },
            
            "performance_trends": {
                "success_rate": {
                    "current": trends["average_success_rate"],
                    "trend_direction": "improving" if trends["success_rate_trend"] > 0.01 else "declining" if trends["success_rate_trend"] < -0.01 else "stable",
                    "trend_slope": trends["success_rate_trend"],
                    "volatility": trends["success_rate_volatility"]
                },
                "confidence_scores": {
                    "trend_direction": "improving" if trends["confidence_trend"] > 0.01 else "declining" if trends["confidence_trend"] < -0.01 else "stable",
                    "trend_slope": trends["confidence_trend"]
                },
                "processing_efficiency": {
                    "trend_direction": "improving" if trends["processing_time_trend"] < -0.01 else "declining" if trends["processing_time_trend"] > 0.01 else "stable",
                    "trend_slope": trends["processing_time_trend"]
                }
            },
            
            "issue_analysis": {
                "bottlenecks_found": len(bottlenecks),
                "high_priority_issues": len([b for b in bottlenecks if b.get("severity") == "high"]),
                "bottlenecks": bottlenecks,
                "regression_status": regression_analysis.get("status", "unknown"),
                "regression_indicators": regression_analysis.get("regression_indicators", [])
            },
            
            "rule_performance": self.metrics_collector.get_rule_performance_summary(),
            
            "historical_performance": self._get_historical_performance_summary(),
            
            "recommendations": self._generate_recommendations(trends, bottlenecks, performance_insights),
            
            "alerts": self._generate_alerts(bottlenecks, regression_analysis, latest_metrics)
        }
        
        logger.info(f"Generated summary report: {report['current_status']['overall_health']} health, "
                   f"{len(bottlenecks)} bottlenecks identified")
        
        return report
    
    def generate_executive_summary(self) -> Dict[str, Any]:
        """Generate a high-level executive summary"""
        full_report = self.generate_summary_report()
        
        if full_report.get("status") == "no_data":
            return full_report
        
        # Extract key executive-level insights
        current_status = full_report["current_status"]
        trends = full_report["performance_trends"]
        issues = full_report["issue_analysis"]
        
        # Determine overall status
        if issues["high_priority_issues"] > 0:
            overall_status = "critical_attention_needed"
        elif issues["bottlenecks_found"] > 2:
            overall_status = "monitoring_required"
        elif trends["success_rate"]["trend_direction"] == "declining":
            overall_status = "declining_performance"
        else:
            overall_status = "healthy"
        
        # Calculate key performance indicators
        kpis = self._calculate_kpis()
        
        executive_summary = {
            "summary_date": datetime.now().isoformat(),
            "overall_status": overall_status,
            "status_description": self._get_status_description(overall_status),
            
            "key_performance_indicators": kpis,
            
            "critical_metrics": {
                "current_success_rate": f"{current_status['latest_batch']['success_rate']:.1%}",
                "high_confidence_rate": f"{current_status['confidence_distribution']['high_percentage']:.1f}%",
                "total_items_processed": sum(m.total_items for m in self.metrics_collector.processing_history[-7:]),  # Last week
                "average_processing_time": f"{current_status['latest_batch']['processing_time']:.1f}s"
            },
            
            "trend_summary": {
                "success_rate_trend": trends["success_rate"]["trend_direction"],
                "confidence_trend": trends["confidence_scores"]["trend_direction"],
                "efficiency_trend": trends["processing_efficiency"]["trend_direction"]
            },
            
            "immediate_actions_required": [
                rec for rec in full_report["recommendations"] 
                if any(word in rec.lower() for word in ["critical", "immediate", "urgent", "fix"])
            ][:3],  # Top 3 critical actions
            
            "performance_highlights": self._get_performance_highlights(full_report),
            
            "next_review_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        return executive_summary
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for monitoring dashboards"""
        if not self.metrics_collector.processing_history:
            return {"status": "no_data", "timestamp": datetime.now().isoformat()}
        
        latest = self.metrics_collector.processing_history[-1]
        recent_batches = self.metrics_collector.processing_history[-5:]  # Last 5 batches
        
        # Calculate real-time aggregates
        recent_success_rate = sum(m.success_rate for m in recent_batches) / len(recent_batches)
        recent_avg_confidence = sum(m.average_confidence for m in recent_batches) / len(recent_batches)
        recent_processing_time = sum(m.processing_time for m in recent_batches) / len(recent_batches)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "last_updated": latest.timestamp.isoformat(),
            
            "current_metrics": {
                "success_rate": round(latest.success_rate, 3),
                "confidence_score": round(latest.average_confidence, 3),
                "processing_time": round(latest.processing_time, 2),
                "items_processed": latest.total_items,
                "batch_id": latest.batch_id
            },
            
            "recent_averages": {
                "success_rate": round(recent_success_rate, 3),
                "confidence_score": round(recent_avg_confidence, 3),
                "processing_time": round(recent_processing_time, 2),
                "batches_analyzed": len(recent_batches)
            },
            
            "confidence_breakdown": {
                "high": latest.high_confidence,
                "medium": latest.medium_confidence,
                "low": latest.low_confidence,
                "high_percentage": round(latest.high_confidence / latest.total_items * 100, 1) if latest.total_items > 0 else 0
            },
            
            "system_health": self._assess_system_health(),
            
            "alerts": len([alert for alert in self._generate_alerts([], {}, latest) if alert.get("severity") in ["high", "critical"]])
        }
    
    def export_dashboard_data(self, filepath: str, include_detailed: bool = True):
        """Export dashboard data for external use"""
        export_data = {
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "export_type": "dashboard_data",
                "includes_detailed_data": include_detailed
            },
            "summary_report": self.generate_summary_report(),
            "executive_summary": self.generate_executive_summary(),
            "real_time_metrics": self.get_real_time_metrics()
        }
        
        if include_detailed:
            export_data["detailed_metrics"] = {
                "processing_history": [
                    {
                        "batch_id": m.batch_id,
                        "timestamp": m.timestamp.isoformat(),
                        "total_items": m.total_items,
                        "success_rate": m.success_rate,
                        "average_confidence": m.average_confidence,
                        "processing_time": m.processing_time,
                        "confidence_distribution": {
                            "high": m.high_confidence,
                            "medium": m.medium_confidence,
                            "low": m.low_confidence
                        }
                    }
                    for m in self.metrics_collector.processing_history
                ],
                "rule_performance": self.metrics_collector.rule_performance
            }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Exported dashboard data to {filepath}")
    
    def _get_data_period(self) -> Dict[str, str]:
        """Get the data period covered by the metrics"""
        if not self.metrics_collector.processing_history:
            return {"start": "no_data", "end": "no_data"}
        
        start_date = self.metrics_collector.processing_history[0].timestamp
        end_date = self.metrics_collector.processing_history[-1].timestamp
        
        return {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "duration_days": (end_date - start_date).days
        }
    
    def _get_historical_performance_summary(self) -> Dict[str, Any]:
        """Get summary of historical performance"""
        if len(self.metrics_collector.processing_history) < 2:
            return {"status": "insufficient_data"}
        
        # Compare current week vs previous week
        now = datetime.now()
        current_week_start = now - timedelta(days=7)
        previous_week_start = now - timedelta(days=14)
        
        current_week_metrics = [
            m for m in self.metrics_collector.processing_history
            if datetime.fromisoformat(m.timestamp.isoformat()) >= current_week_start
        ]
        
        previous_week_metrics = [
            m for m in self.metrics_collector.processing_history
            if previous_week_start <= datetime.fromisoformat(m.timestamp.isoformat()) < current_week_start
        ]
        
        if not current_week_metrics and not previous_week_metrics:
            return {"status": "insufficient_recent_data"}
        
        def calc_averages(metrics_list):
            if not metrics_list:
                return {"success_rate": 0, "confidence": 0, "processing_time": 0}
            return {
                "success_rate": sum(m.success_rate for m in metrics_list) / len(metrics_list),
                "confidence": sum(m.average_confidence for m in metrics_list) / len(metrics_list),
                "processing_time": sum(m.processing_time for m in metrics_list) / len(metrics_list)
            }
        
        current_avg = calc_averages(current_week_metrics)
        previous_avg = calc_averages(previous_week_metrics)
        
        return {
            "current_week": {
                "batches": len(current_week_metrics),
                **{k: round(v, 3) for k, v in current_avg.items()}
            },
            "previous_week": {
                "batches": len(previous_week_metrics),
                **{k: round(v, 3) for k, v in previous_avg.items()}
            },
            "week_over_week_change": {
                "success_rate": round(current_avg["success_rate"] - previous_avg["success_rate"], 3),
                "confidence": round(current_avg["confidence"] - previous_avg["confidence"], 3),
                "processing_time": round(current_avg["processing_time"] - previous_avg["processing_time"], 3)
            } if previous_week_metrics else {}
        }
    
    def _generate_recommendations(self, trends: Dict, bottlenecks: List[Dict], insights: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Trend-based recommendations
        if trends.get("success_rate_trend", 0) < -0.01:
            recommendations.append("Critical: Success rate is declining. Review recent rule changes and data quality.")
        
        if trends.get("confidence_trend", 0) < -0.01:
            recommendations.append("Confidence scores are declining. Consider reviewing and updating rules.")
        
        if trends.get("processing_time_trend", 0) > 0.1:
            recommendations.append("Processing times are increasing. Optimize the description generation pipeline.")
        
        # High-priority bottleneck recommendations
        high_priority_bottlenecks = [b for b in bottlenecks if b.get("severity") == "high"]
        for bottleneck in high_priority_bottlenecks[:3]:  # Top 3 critical issues
            recommendations.append(f"High Priority: {bottleneck.get('recommendation', 'Address critical bottleneck')}")
        
        # Rule performance recommendations
        rule_summary = insights.get("rule_performance", {})
        if rule_summary.get("average_performance", 0) < 0.6:
            recommendations.append("Overall rule performance is low. Consider rule optimization or retraining.")
        
        # Success rate recommendations
        if trends.get("average_success_rate", 0) < 0.8:
            recommendations.append("Success rate is below target (80%). Investigate data quality and processing logic.")
        
        # High volatility recommendations
        if trends.get("success_rate_volatility", 0) > 0.15:
            recommendations.append("High variability in performance. Review system stability and data consistency.")
        
        # Default recommendation if none generated
        if not recommendations:
            if insights["summary"]["overall_health"] == "good":
                recommendations.append("System performance is stable. Continue monitoring and maintain current practices.")
            else:
                recommendations.append("Review recent performance metrics and consider system optimization.")
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _generate_alerts(self, bottlenecks: List[Dict], regression_analysis: Dict, latest_metrics) -> List[Dict[str, str]]:
        """Generate system alerts"""
        alerts = []
        
        # Critical bottleneck alerts
        critical_bottlenecks = [b for b in bottlenecks if b.get("severity") == "high"]
        for bottleneck in critical_bottlenecks:
            alerts.append({
                "type": "critical_bottleneck",
                "severity": "high",
                "message": f"Critical issue detected: {bottleneck.get('type', 'unknown')}",
                "recommendation": bottleneck.get("recommendation", "Immediate investigation required"),
                "timestamp": datetime.now().isoformat()
            })
        
        # Regression alerts
        if regression_analysis.get("status") == "regression_detected":
            severity_level = "high" if regression_analysis.get("severity", 0) >= 2 else "medium"
            alerts.append({
                "type": "performance_regression",
                "severity": severity_level,
                "message": f"Performance regression detected in: {', '.join(regression_analysis.get('regression_indicators', []))}",
                "recommendation": "Review recent changes and investigate performance decline",
                "timestamp": datetime.now().isoformat()
            })
        
        # Low success rate alert
        if latest_metrics.success_rate < 0.7:
            alerts.append({
                "type": "low_success_rate",
                "severity": "high",
                "message": f"Success rate critically low: {latest_metrics.success_rate:.1%}",
                "recommendation": "Immediate investigation of processing issues required",
                "timestamp": datetime.now().isoformat()
            })
        
        # High processing time alert
        if latest_metrics.processing_time > 5.0:
            alerts.append({
                "type": "high_processing_time",
                "severity": "medium",
                "message": f"Processing time elevated: {latest_metrics.processing_time:.1f}s",
                "recommendation": "Monitor system performance and consider optimization",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts
    
    def _calculate_kpis(self) -> Dict[str, Any]:
        """Calculate key performance indicators"""
        if not self.metrics_collector.processing_history:
            return {}
        
        # Last 30 days of data
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_metrics = [
            m for m in self.metrics_collector.processing_history
            if datetime.fromisoformat(m.timestamp.isoformat()) >= thirty_days_ago
        ]
        
        if not recent_metrics:
            recent_metrics = self.metrics_collector.processing_history[-10:]  # Fallback to last 10
        
        total_items = sum(m.total_items for m in recent_metrics)
        total_successful = sum(m.total_items * m.success_rate for m in recent_metrics)
        
        return {
            "overall_success_rate": round(total_successful / total_items if total_items > 0 else 0, 3),
            "average_confidence_score": round(sum(m.average_confidence for m in recent_metrics) / len(recent_metrics), 3),
            "average_processing_time": round(sum(m.processing_time for m in recent_metrics) / len(recent_metrics), 2),
            "total_items_processed": total_items,
            "batches_completed": len(recent_metrics),
            "high_confidence_rate": round(
                sum(m.high_confidence for m in recent_metrics) / total_items if total_items > 0 else 0, 3
            ),
            "period_analyzed": "last_30_days"
        }
    
    def _get_status_description(self, status: str) -> str:
        """Get human-readable status description"""
        descriptions = {
            "healthy": "System is performing optimally with no critical issues detected.",
            "declining_performance": "Performance metrics show a declining trend requiring attention.",
            "monitoring_required": "Several performance issues detected that need monitoring.",
            "critical_attention_needed": "Critical issues detected requiring immediate attention."
        }
        return descriptions.get(status, "Status assessment unavailable.")
    
    def _get_performance_highlights(self, report: Dict) -> List[str]:
        """Extract performance highlights from the report"""
        highlights = []
        
        current_status = report["current_status"]
        trends = report["performance_trends"]
        
        # Success rate highlights
        success_rate = current_status["latest_batch"]["success_rate"]
        if success_rate >= 0.95:
            highlights.append(f"Excellent success rate: {success_rate:.1%}")
        elif success_rate >= 0.85:
            highlights.append(f"Good success rate: {success_rate:.1%}")
        
        # Confidence highlights
        high_conf_pct = current_status["confidence_distribution"]["high_percentage"]
        if high_conf_pct >= 80:
            highlights.append(f"High confidence rate: {high_conf_pct:.1f}%")
        
        # Trend highlights
        if trends["success_rate"]["trend_direction"] == "improving":
            highlights.append("Success rate trend is improving")
        if trends["confidence_scores"]["trend_direction"] == "improving":
            highlights.append("Confidence scores are trending upward")
        
        # Rule performance highlights
        rule_perf = report["rule_performance"]
        if rule_perf.get("average_performance", 0) >= 0.8:
            highlights.append("Strong rule performance across the system")
        
        return highlights[:5]  # Limit to top 5 highlights
    
    def _assess_system_health(self) -> str:
        """Assess overall system health"""
        if not self.metrics_collector.processing_history:
            return "unknown"
        
        latest = self.metrics_collector.processing_history[-1]
        bottlenecks = self.analyzer.identify_bottlenecks()
        
        critical_issues = len([b for b in bottlenecks if b.get("severity") == "high"])
        
        if critical_issues > 0:
            return "critical"
        elif latest.success_rate < 0.7:
            return "poor"
        elif latest.success_rate < 0.85 or len(bottlenecks) > 2:
            return "fair"
        else:
            return "good"

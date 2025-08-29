from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

# Importing existing dashboard functionality
from src.progress_tracking.dashboard import ProgressDashboard
from src.progress_tracking.metrics_collector import MetricsCollector
from src.progress_tracking.performance_analyzer import PerformanceAnalyzer
from src.utils.config import get_project_settings

from ..models.dashboard import(
    DashboardSummary, ExecutiveSummary, RealTimeMetrics, PerformanceMetrics, QualityMetrics, SystemHealth
)

class DashboardService:
    """ Service layer for dashboard operations """
    def __init__(self):
        # Initialize with exisiting Athen components
        self.settings = get_project_settings()
        self.data_dir = self.settings.get('data_dir', 'data')

        # Initialize existing components
        self.metrics_collector = MetricsCollector(self.data_dir)
        self.performance_analyzer = PerformanceAnalyzer(self.metrics_collector)
        self.dashboard = ProgressDashboard(
            self.metrics_collector,
            self.performance_analyzer,
        )

        # Cache for performance
        self._cache = {}
        self._cache_ttl = 60 # 1 minute

    async def get_dashboard_summary(self) -> DashboardSummary:
        """ Get comprehensive dashboard summary """
        cache_key = "dashboard_summary"

        # Check cache
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]['data']

        # Get data from existing dashboard
        summary_report = self.dashboard.generate_summary_report()

        # Conver to Web API format
        dashboard_summary = DashboardSummary(
            system_overview=self._extract_system_overview(summary_report),
            performance_metrics=self._extract_performance_metrics(summary_report),
            quality_metrics=self._extract_quality_metrics(summary_report),
            recent_activity=self._extract_recent_activity(summary_report),
            recommendations=self._extract_recommendations(summary_report),
            system_health=self._extract_system_health(summary_report),
            last_updated=datetime.utcnow(),
        )

        # Cache result
        self._cache[cache_key] = {
            'data': dashboard_summary,
            'timestamp': datetime.utcnow(),
        }

        return dashboard_summary
    
    async def get_real_time_metrics(self) -> RealTimeMetrics:
        """ Get real-time metrics """
        real_time_data = self.dashboard.get_real_time_metrics()

        return RealTimeMetrics(
            current_batch_status=real_time_data.get('current_metrics', {}),
            processing_rate=real_time_data.get('recent_averages', {}),
            confidence__distribution=real_time_data.get('confidence_breakdown', {}),
            system_health=real_time_data.get('system_health', 'unknown'),
            active_alerts=real_time_data.get('alerts', 0),
            timestamp=datetime.utcnow(),
        )

    async def get_executive_summary(self) -> ExecutiveSummary:
        """" Get executive summary """
        cache_key = "executive_summary"
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]['data']

        # Get executive summary from existing dashboard
        exec_summary = self.dashboard.generate_executive_summary()

        executive_summary = ExecutiveSummary(
            key_performance_indicators=exec_summary.get('kpis', {}),
            quality_trend=exec_summary.get('quality_summary', {}),
            operational_status=exec_summary.get('operational_status', {}),
            critical_actions=exec_summary.get('critical_actions', []),
            performance_highlights=exec_summary.get('performance_highlights', {}),
            next_review_date=exec_summary.get('next_review_date'), 
            last_updated=datetime.utcnow(),
        )

        # Cache result
        self._cache[cache_key] = {
            'data': executive_summary,
            'timestamp': datetime.utcnow(),
        }

        return executive_summary

    async def get_performance_history(self, days: int =30) -> List[Dict]:
        """ Get performance history """
        # Use existing performance analyzer
        end_date = datetime.now()
        start_date = end_date - timedelta(days = days)

        history = self.performance_analyzer.get_performance_history(
            start_date=start_date,
            end_date=end_date
        )

        # Format for web API
        return [
            {
                'date': entry.get('date'),
                'succes_rate': entry.get('success_rate', 0),
                'confidence_score': entry.get('avg_confidence', 0),
                'processing_time': entry.get('avg_processing_time', 0),
                'items_processed': entry.get('total_items', 0),
                'batch_count': entry.get('batch_count', 0)
            }
            for entry in history    
        ]

    # Helper methods
    def _extract_system_overview(self, summary_report: Dict) -> Dict:
        """Extract system overview from summary report"""
        return {
            'total_batches': summary_report.get('processing_summary', {}).get('total_batches', 0),
            'total_items': summary_report.get('processing_summary', {}).get('total_items', 0),
            'success_rate': summary_report.get('processing_summary', {}).get('overall_success_rate', 0),
            'average_confidence': summary_report.get('quality_summary', {}).get('average_confidence', 0),
            'uptime_hours': summary_report.get('operational_summary', {}).get('uptime_hours', 0)
        }

    def _extract_performance_metrics(self, summary_report: Dict) -> Dict:
        """Extract performance metrics from summary report"""
        return {
            'processing_speed': summary_report.get('performance_summary', {}).get('avg_processing_time', 0),
            'throughput': summary_report.get('performance_summary', {}).get('items_per_hour', 0),
            'error_rate': summary_report.get('performance_summary', {}).get('error_rate', 0),
            'efficiency_score': summary_report.get('performance_summary', {}).get('efficiency_score', 0)
        }

    def _extract_quality_metrics(self, summary_report: Dict) -> Dict:
        """Extract quality metrics from summary report"""
        return {
            'high_confidence_rate': summary_report.get('quality_summary', {}).get('high_confidence_rate', 0),
            'medium_confidence_rate': summary_report.get('quality_summary', {}).get('medium_confidence_rate', 0),
            'low_confidence_rate': summary_report.get('quality_summary', {}).get('low_confidence_rate', 0),
            'improvement_trend': summary_report.get('quality_summary', {}).get('trend', 'stable'),
            'quality_score': summary_report.get('quality_summary', {}).get('overall_quality_score', 0)
        }

    def _extract_recent_activity(self, summary_report: Dict) -> List[Dict]:
        """Extract recent activity from summary report"""
        recent_batches = summary_report.get('recent_activity', {}).get('recent_batches', [])
        return [
            {
                'type': 'batch_completed',
                'description': f"Batch {batch.get('id')} completed with {batch.get('success_rate', 0):.1%} success rate",
                'timestamp': batch.get('completed_at'),
                'status': 'success' if batch.get('success_rate', 0) > 0.8 else 'warning'
            }
            for batch in recent_batches[-10:]  # Last 10 batches
        ]

    def _extract_recommendations(self, summary_report: Dict) -> List[Dict]:
        """Extract recommendations from summary report"""
        recs = summary_report.get('recommendations', [])
        return [
            {
                'priority': rec.get('priority', 'medium'),
                'title': rec.get('title', ''),
                'description': rec.get('description', ''),
                'category': rec.get('category', 'general'),
                'impact': rec.get('expected_impact', 'medium')
            }
            for rec in recs
        ]

    def _assess_system_health(self, summary_report: Dict) -> str:
        """Assess overall system health"""
        current_status = summary_report.get('current_status', {})
        health = current_status.get('overall_health', 'unknown')
        return health

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid"""
        if key not in self._cache:
            return False
        
        cache_entry = self._cache[key]
        elapsed = (datetime.utcnow() - cache_entry['timestamp']).seconds
        return elapsed < self._cache_ttl
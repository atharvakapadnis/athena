# src/ai_analysis/notes_exporter.py
"""
Notes Exporter for AI Notes System - handles export to various formats
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from ..utils.logger import get_logger
from .notes_manager import NotesManager, AINote, HumanFeedback
from .notes_pattern_analyzer import NotesPatternAnalyzer

logger = get_logger(__name__)

class NotesExporter:
    """Exports notes and insights to various formats"""
    
    def __init__(self, notes_manager: NotesManager):
        self.notes_manager = notes_manager
        self.pattern_analyzer = NotesPatternAnalyzer(notes_manager)
        self.logger = logger
    
    def export_notes_to_json(self, filepath: str, 
                           note_types: List[str] = None,
                           min_priority: int = 1,
                           status_filter: List[str] = None) -> bool:
        """Export filtered notes to JSON format"""
        try:
            notes = self._filter_notes(note_types, min_priority, status_filter)
            
            export_data = {
                "export_metadata": {
                    "export_timestamp": datetime.now().isoformat(),
                    "total_notes": len(notes),
                    "filters_applied": {
                        "note_types": note_types,
                        "min_priority": min_priority,
                        "status_filter": status_filter
                    }
                },
                "notes": [self._note_to_dict(note) for note in notes]
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Exported {len(notes)} notes to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Notes export to JSON failed: {e}")
            return False
    
    def export_feedback_to_json(self, filepath: str, 
                               action_filter: List[str] = None,
                               days_back: int = None) -> bool:
        """Export feedback to JSON format"""
        try:
            feedback = self._filter_feedback(action_filter, days_back)
            
            export_data = {
                "export_metadata": {
                    "export_timestamp": datetime.now().isoformat(),
                    "total_feedback": len(feedback),
                    "filters_applied": {
                        "action_filter": action_filter,
                        "days_back": days_back
                    }
                },
                "feedback": [self._feedback_to_dict(fb) for fb in feedback]
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Exported {len(feedback)} feedback items to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Feedback export to JSON failed: {e}")
            return False
    
    def export_notes_to_csv(self, filepath: str,
                           note_types: List[str] = None,
                           min_priority: int = 1) -> bool:
        """Export notes to CSV format"""
        try:
            notes = self._filter_notes(note_types, min_priority)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'note_id', 'timestamp', 'note_type', 'content', 
                    'priority', 'status', 'author', 'tags'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for note in notes:
                    writer.writerow({
                        'note_id': note.note_id,
                        'timestamp': note.timestamp.isoformat(),
                        'note_type': note.note_type,
                        'content': note.content,
                        'priority': note.priority,
                        'status': note.status,
                        'author': note.author,
                        'tags': ', '.join(note.tags)
                    })
            
            self.logger.info(f"Exported {len(notes)} notes to CSV: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Notes export to CSV failed: {e}")
            return False
    
    def export_insights_report(self, filepath: str, include_recommendations: bool = True) -> bool:
        """Export comprehensive insights report to markdown"""
        try:
            patterns = self.pattern_analyzer.analyze_note_patterns()
            insights = self.pattern_analyzer.identify_insights()
            quality_metrics = self.pattern_analyzer.get_quality_metrics()
            
            if include_recommendations:
                recommendations = self.pattern_analyzer.generate_recommendations()
            else:
                recommendations = []
            
            report_content = self._generate_insights_report(
                patterns, insights, quality_metrics, recommendations
            )
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            self.logger.info(f"Exported insights report to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Insights report export failed: {e}")
            return False
    
    def export_summary_dashboard(self, filepath: str) -> bool:
        """Export a summary dashboard in JSON format"""
        try:
            summary = self.notes_manager.get_summary()
            recent_activity = self.notes_manager.get_recent_activity(hours=24)
            quality_metrics = self.pattern_analyzer.get_quality_metrics()
            insights = self.pattern_analyzer.identify_insights()
            
            dashboard_data = {
                "generated_at": datetime.now().isoformat(),
                "summary": summary,
                "recent_activity": {
                    "notes_count": recent_activity["notes_count"],
                    "feedback_count": recent_activity["feedback_count"],
                    "time_window_hours": recent_activity["time_window_hours"]
                },
                "quality_metrics": quality_metrics,
                "active_insights": [
                    insight for insight in insights 
                    if insight.get("severity") in ["high", "medium"]
                ],
                "system_health": self._calculate_system_health(quality_metrics, insights)
            }
            
            with open(filepath, 'w') as f:
                json.dump(dashboard_data, f, indent=2, default=str)
            
            self.logger.info(f"Exported summary dashboard to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Dashboard export failed: {e}")
            return False
    
    def export_full_backup(self, backup_dir: str) -> bool:
        """Export complete backup of all notes and feedback"""
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Export all notes
            notes_file = backup_path / f"notes_backup_{timestamp}.json"
            self.export_notes_to_json(str(notes_file))
            
            # Export all feedback
            feedback_file = backup_path / f"feedback_backup_{timestamp}.json"
            self.export_feedback_to_json(str(feedback_file))
            
            # Export insights report
            insights_file = backup_path / f"insights_report_{timestamp}.md"
            self.export_insights_report(str(insights_file))
            
            # Export dashboard
            dashboard_file = backup_path / f"dashboard_{timestamp}.json"
            self.export_summary_dashboard(str(dashboard_file))
            
            # Create backup manifest
            manifest = {
                "backup_timestamp": datetime.now().isoformat(),
                "files": {
                    "notes": str(notes_file.name),
                    "feedback": str(feedback_file.name),
                    "insights": str(insights_file.name),
                    "dashboard": str(dashboard_file.name)
                },
                "counts": {
                    "total_notes": len(self.notes_manager.notes),
                    "total_feedback": len(self.notes_manager.feedback)
                }
            }
            
            manifest_file = backup_path / f"backup_manifest_{timestamp}.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            self.logger.info(f"Complete backup exported to {backup_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Full backup export failed: {e}")
            return False
    
    def _filter_notes(self, note_types: List[str] = None, 
                     min_priority: int = 1,
                     status_filter: List[str] = None) -> List[AINote]:
        """Filter notes based on criteria"""
        notes = self.notes_manager.notes
        
        if note_types:
            notes = [n for n in notes if n.note_type in note_types]
        
        if min_priority > 1:
            notes = [n for n in notes if n.priority >= min_priority]
        
        if status_filter:
            notes = [n for n in notes if n.status in status_filter]
        
        return notes
    
    def _filter_feedback(self, action_filter: List[str] = None,
                        days_back: int = None) -> List[HumanFeedback]:
        """Filter feedback based on criteria"""
        feedback = self.notes_manager.feedback
        
        if action_filter:
            feedback = [fb for fb in feedback if fb.action_taken in action_filter]
        
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            feedback = [fb for fb in feedback if fb.timestamp > cutoff_date]
        
        return feedback
    
    def _note_to_dict(self, note: AINote) -> Dict:
        """Convert note to dictionary for export"""
        return {
            "note_id": note.note_id,
            "timestamp": note.timestamp.isoformat(),
            "note_type": note.note_type,
            "content": note.content,
            "context": note.context,
            "tags": note.tags,
            "priority": note.priority,
            "status": note.status,
            "author": note.author
        }
    
    def _feedback_to_dict(self, feedback: HumanFeedback) -> Dict:
        """Convert feedback to dictionary for export"""
        return {
            "feedback_id": feedback.feedback_id,
            "timestamp": feedback.timestamp.isoformat(),
            "related_note_id": feedback.related_note_id,
            "content": feedback.content,
            "action_taken": feedback.action_taken,
            "user_id": feedback.user_id
        }
    
    def _generate_insights_report(self, patterns: Dict, insights: List[Dict], 
                                 quality_metrics: Dict, recommendations: List[Dict]) -> str:
        """Generate comprehensive markdown insights report"""
        report = "# AI Notes System - Insights Report\n\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Executive Summary
        report += "## Executive Summary\n\n"
        total_notes = quality_metrics.get("total_notes", 0)
        resolution_rate = quality_metrics.get("resolution_rate", 0)
        avg_priority = quality_metrics.get("average_priority", 0)
        
        report += f"- **Total Notes:** {total_notes}\n"
        report += f"- **Resolution Rate:** {resolution_rate:.1%}\n"
        report += f"- **Average Priority:** {avg_priority:.1f}/5\n"
        report += f"- **Active Insights:** {len([i for i in insights if i.get('severity') in ['high', 'medium']])}\n\n"
        
        # Key Insights
        report += "## Key Insights\n\n"
        for insight in insights:
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢", "info": "ℹ️"}.get(insight.get("severity", "info"), "ℹ️")
            report += f"### {severity_emoji} {insight.get('type', 'Unknown').replace('_', ' ').title()}\n"
            report += f"{insight.get('description', 'No description available')}\n\n"
            if insight.get('recommendation'):
                report += f"**Recommendation:** {insight['recommendation']}\n\n"
        
        # Pattern Analysis
        report += "## Pattern Analysis\n\n"
        
        # Note type distribution
        note_types = patterns.get("note_type_distribution", {})
        if note_types:
            report += "### Note Types\n"
            for note_type, count in note_types.items():
                report += f"- **{note_type.title()}:** {count}\n"
            report += "\n"
        
        # Priority distribution
        priority_dist = patterns.get("priority_distribution", {})
        if priority_dist:
            report += "### Priority Distribution\n"
            for priority in sorted(priority_dist.keys(), reverse=True):
                count = priority_dist[priority]
                stars = "⭐" * priority
                report += f"- **Priority {priority} {stars}:** {count}\n"
            report += "\n"
        
        # Feedback patterns
        feedback_patterns = patterns.get("feedback_patterns", {})
        if feedback_patterns and feedback_patterns.get("total_feedback", 0) > 0:
            report += "### Feedback Patterns\n"
            report += f"- **Acceptance Rate:** {feedback_patterns.get('acceptance_rate', 0):.1%}\n"
            report += f"- **Rejection Rate:** {feedback_patterns.get('rejection_rate', 0):.1%}\n"
            report += f"- **Modification Rate:** {feedback_patterns.get('modification_rate', 0):.1%}\n\n"
        
        # Trending topics
        trending_topics = patterns.get("trending_topics", [])
        if trending_topics:
            report += "### Trending Topics\n"
            for i, topic in enumerate(trending_topics[:5], 1):
                report += f"{i}. {topic}\n"
            report += "\n"
        
        # Recommendations
        if recommendations:
            report += "## Recommendations\n\n"
            for rec in recommendations:
                urgency_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec.get("urgency", "low"), "🟢")
                report += f"### {urgency_emoji} {rec.get('type', 'Unknown').replace('_', ' ').title()}\n"
                report += f"**Description:** {rec.get('description', 'No description')}\n\n"
                report += f"**Action:** {rec.get('action', 'No action specified')}\n\n"
                report += f"**Expected Impact:** {rec.get('impact', 'No impact specified')}\n\n"
        
        # Quality Metrics
        report += "## Quality Metrics\n\n"
        report += f"- **Tag Usage Rate:** {quality_metrics.get('tag_usage_rate', 0):.1%}\n"
        report += f"- **Notes with Feedback:** {quality_metrics.get('notes_with_feedback', 0)}\n"
        report += f"- **Feedback Acceptance Rate:** {quality_metrics.get('feedback_acceptance_rate', 0):.1%}\n\n"
        
        report += "---\n"
        report += "*This report was automatically generated by the AI Notes System*\n"
        
        return report
    
    def _calculate_system_health(self, quality_metrics: Dict, insights: List[Dict]) -> Dict:
        """Calculate overall system health score"""
        score = 100
        
        # Deduct points for issues
        high_severity_count = len([i for i in insights if i.get("severity") == "high"])
        medium_severity_count = len([i for i in insights if i.get("severity") == "medium"])
        
        score -= (high_severity_count * 15)  # -15 per high severity issue
        score -= (medium_severity_count * 5)  # -5 per medium severity issue
        
        # Adjust based on quality metrics
        resolution_rate = quality_metrics.get("resolution_rate", 0)
        if resolution_rate < 0.5:
            score -= 10
        
        feedback_rate = quality_metrics.get("feedback_acceptance_rate", 0)
        if feedback_rate < 0.5:
            score -= 10
        
        score = max(0, min(100, score))  # Clamp between 0-100
        
        if score >= 90:
            status = "excellent"
        elif score >= 75:
            status = "good"
        elif score >= 60:
            status = "fair"
        else:
            status = "needs_attention"
        
        return {
            "score": score,
            "status": status,
            "high_severity_issues": high_severity_count,
            "medium_severity_issues": medium_severity_count
        }

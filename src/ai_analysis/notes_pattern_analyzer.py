# src/ai_analysis/notes_pattern_analyzer.py
"""
Pattern analyzer for AI Notes System - analyzes patterns in notes and feedback
"""

from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta
import re
from utils.logger import get_logger
from .notes_manager import NotesManager, AINote, HumanFeedback

logger = get_logger(__name__)

class NotesPatternAnalyzer:
    """Analyzes patterns in AI notes and human feedback to generate insights"""
    
    def __init__(self, notes_manager: NotesManager):
        self.notes_manager = notes_manager
        self.logger = logger
    
    def analyze_note_patterns(self) -> Dict[str, Any]:
        """Analyze comprehensive patterns in AI notes and human feedback"""
        notes = self.notes_manager.notes
        feedback = self.notes_manager.feedback
        
        analysis = {
            "note_type_distribution": self._analyze_note_types(notes),
            "priority_distribution": self._analyze_priorities(notes),
            "status_distribution": self._analyze_status(notes),
            "common_tags": self._analyze_tags(notes),
            "feedback_patterns": self._analyze_feedback_patterns(feedback),
            "trending_topics": self._identify_trending_topics(notes),
            "temporal_patterns": self._analyze_temporal_patterns(notes),
            "correlation_analysis": self._analyze_note_feedback_correlation(notes, feedback)
        }
        
        self.logger.info(f"Analyzed patterns for {len(notes)} notes and {len(feedback)} feedback items")
        return analysis
    
    def identify_insights(self) -> List[Dict]:
        """Identify actionable insights from notes and feedback"""
        insights = []
        notes = self.notes_manager.notes
        feedback = self.notes_manager.feedback
        
        # Analyze high-priority notes
        high_priority_notes = self.notes_manager.get_notes_by_priority(4)
        active_high_priority = [n for n in high_priority_notes if n.status == "active"]
        
        if active_high_priority:
            insights.append({
                "type": "high_priority_notes",
                "severity": "high",
                "count": len(active_high_priority),
                "description": f"{len(active_high_priority)} high-priority notes require attention",
                "notes": [{"id": n.note_id, "content": n.content[:100]} for n in active_high_priority[:3]],
                "recommendation": "Review and address high-priority active notes"
            })
        
        # Analyze feedback patterns
        feedback_patterns = self._analyze_feedback_patterns(feedback)
        if feedback_patterns.get("rejection_rate", 0) > 0.3:
            insights.append({
                "type": "high_rejection_rate",
                "severity": "medium",
                "rate": feedback_patterns["rejection_rate"],
                "description": f"High AI suggestion rejection rate: {feedback_patterns['rejection_rate']:.1%}",
                "recommendation": "Review AI suggestion quality and criteria"
            })
        
        # Analyze note accumulation
        recent_notes = [n for n in notes if n.timestamp > datetime.now() - timedelta(days=7)]
        if len(recent_notes) > 50:  # More than 50 notes in a week
            insights.append({
                "type": "note_accumulation",
                "severity": "medium",
                "count": len(recent_notes),
                "description": f"High note creation rate: {len(recent_notes)} notes in the last week",
                "recommendation": "Consider note management and resolution workflows"
            })
        
        # Analyze unresolved observations
        unresolved_observations = [n for n in notes if n.note_type == "observation" and n.status == "active"]
        if len(unresolved_observations) > 20:
            insights.append({
                "type": "unresolved_observations",
                "severity": "low",
                "count": len(unresolved_observations),
                "description": f"{len(unresolved_observations)} observations remain unresolved",
                "recommendation": "Review and categorize unresolved observations"
            })
        
        # Analyze trending issues
        trending_topics = self._identify_trending_topics(notes)
        if trending_topics:
            insights.append({
                "type": "trending_topics",
                "severity": "info",
                "topics": trending_topics[:5],
                "description": f"Trending topics in recent notes: {', '.join(trending_topics[:3])}",
                "recommendation": "Monitor trending topics for emerging patterns"
            })
        
        return insights
    
    def generate_recommendations(self) -> List[Dict]:
        """Generate actionable recommendations based on pattern analysis"""
        recommendations = []
        patterns = self.analyze_note_patterns()
        
        # Priority-based recommendations
        priority_dist = patterns.get("priority_distribution", {})
        high_priority_ratio = priority_dist.get(5, 0) + priority_dist.get(4, 0)
        total_notes = sum(priority_dist.values()) if priority_dist else 1
        
        if high_priority_ratio / total_notes > 0.2:  # More than 20% high priority
            recommendations.append({
                "type": "priority_management",
                "urgency": "high",
                "description": "High proportion of critical notes detected",
                "action": "Implement priority-based review workflow",
                "impact": "Better resource allocation for critical issues"
            })
        
        # Feedback-based recommendations
        feedback_patterns = patterns.get("feedback_patterns", {})
        acceptance_rate = feedback_patterns.get("acceptance_rate", 0)
        
        if acceptance_rate < 0.5:  # Less than 50% acceptance
            recommendations.append({
                "type": "ai_improvement",
                "urgency": "medium",
                "description": "Low AI suggestion acceptance rate detected",
                "action": "Review and improve AI suggestion algorithms",
                "impact": "Higher quality suggestions and better human-AI collaboration"
            })
        
        # Tag-based recommendations
        common_tags = patterns.get("common_tags", [])
        if len(common_tags) > 10:  # Many different tags
            recommendations.append({
                "type": "tag_standardization",
                "urgency": "low",
                "description": "Many different tags in use",
                "action": "Standardize tagging system and create tag taxonomy",
                "impact": "Better note organization and searchability"
            })
        
        # Temporal pattern recommendations
        temporal_patterns = patterns.get("temporal_patterns", {})
        if temporal_patterns.get("recent_activity_increase", False):
            recommendations.append({
                "type": "capacity_planning",
                "urgency": "medium",
                "description": "Increasing note creation activity detected",
                "action": "Plan for increased review capacity",
                "impact": "Maintain response times as system usage grows"
            })
        
        return recommendations
    
    def _analyze_note_types(self, notes: List[AINote]) -> Dict[str, int]:
        """Analyze distribution of note types"""
        return dict(Counter(note.note_type for note in notes))
    
    def _analyze_priorities(self, notes: List[AINote]) -> Dict[int, int]:
        """Analyze distribution of note priorities"""
        return dict(Counter(note.priority for note in notes))
    
    def _analyze_status(self, notes: List[AINote]) -> Dict[str, int]:
        """Analyze distribution of note statuses"""
        return dict(Counter(note.status for note in notes))
    
    def _analyze_tags(self, notes: List[AINote]) -> List[Tuple[str, int]]:
        """Analyze most common tags"""
        all_tags = []
        for note in notes:
            all_tags.extend(note.tags)
        return Counter(all_tags).most_common(10)
    
    def _analyze_feedback_patterns(self, feedback: List[HumanFeedback]) -> Dict:
        """Analyze patterns in human feedback"""
        if not feedback:
            return {
                "total_feedback": 0,
                "acceptance_rate": 0,
                "rejection_rate": 0,
                "modification_rate": 0
            }
        
        actions = [f.action_taken for f in feedback]
        total = len(actions)
        
        return {
            "total_feedback": total,
            "acceptance_rate": actions.count("accepted") / total,
            "rejection_rate": actions.count("rejected") / total,
            "modification_rate": actions.count("modified") / total,
            "ignore_rate": actions.count("ignored") / total,
            "action_distribution": dict(Counter(actions))
        }
    
    def _identify_trending_topics(self, notes: List[AINote]) -> List[str]:
        """Identify trending topics from recent notes"""
        # Get notes from the last 14 days
        recent_cutoff = datetime.now() - timedelta(days=14)
        recent_notes = [note for note in notes if note.timestamp > recent_cutoff]
        
        if not recent_notes:
            return []
        
        # Extract keywords from content
        keywords = []
        for note in recent_notes:
            # Simple keyword extraction (could be enhanced with NLP)
            words = re.findall(r'\b[a-zA-Z]{4,}\b', note.content.lower())
            # Filter out common words
            stop_words = {'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'were', 'said'}
            filtered_words = [w for w in words if w not in stop_words]
            keywords.extend(filtered_words)
        
        # Return top trending keywords
        return [word for word, count in Counter(keywords).most_common(10)]
    
    def _analyze_temporal_patterns(self, notes: List[AINote]) -> Dict:
        """Analyze temporal patterns in note creation"""
        if not notes:
            return {"recent_activity_increase": False, "notes_by_day": {}}
        
        # Group notes by day
        notes_by_day = defaultdict(int)
        for note in notes:
            day_key = note.timestamp.date().isoformat()
            notes_by_day[day_key] += 1
        
        # Analyze recent activity
        last_week = datetime.now() - timedelta(days=7)
        previous_week = datetime.now() - timedelta(days=14)
        
        recent_notes = [n for n in notes if n.timestamp > last_week]
        previous_notes = [n for n in notes if previous_week < n.timestamp <= last_week]
        
        recent_activity_increase = len(recent_notes) > len(previous_notes) * 1.2  # 20% increase
        
        return {
            "recent_activity_increase": recent_activity_increase,
            "notes_by_day": dict(notes_by_day),
            "recent_week_count": len(recent_notes),
            "previous_week_count": len(previous_notes)
        }
    
    def _analyze_note_feedback_correlation(self, notes: List[AINote], feedback: List[HumanFeedback]) -> Dict:
        """Analyze correlation between notes and feedback"""
        # Map feedback to notes
        feedback_by_note = defaultdict(list)
        for fb in feedback:
            if fb.related_note_id:
                feedback_by_note[fb.related_note_id].append(fb)
        
        # Analyze which note types get most feedback
        note_type_feedback = defaultdict(int)
        for note in notes:
            if note.note_id in feedback_by_note:
                note_type_feedback[note.note_type] += len(feedback_by_note[note.note_id])
        
        # Analyze response times (notes to feedback)
        response_times = []
        for note in notes:
            note_feedback = feedback_by_note.get(note.note_id, [])
            for fb in note_feedback:
                response_time = (fb.timestamp - note.timestamp).total_seconds() / 3600  # hours
                response_times.append(response_time)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "notes_with_feedback": len(feedback_by_note),
            "total_notes": len(notes),
            "feedback_coverage": len(feedback_by_note) / len(notes) if notes else 0,
            "note_type_feedback_count": dict(note_type_feedback),
            "average_response_time_hours": avg_response_time
        }
    
    def get_quality_metrics(self) -> Dict:
        """Calculate quality metrics for the notes system"""
        notes = self.notes_manager.notes
        feedback = self.notes_manager.feedback
        
        if not notes:
            return {"error": "No notes available for analysis"}
        
        # Resolution rate
        resolved_notes = [n for n in notes if n.status in ["resolved", "archived"]]
        resolution_rate = len(resolved_notes) / len(notes)
        
        # Average priority
        avg_priority = sum(note.priority for note in notes) / len(notes)
        
        # Feedback quality
        feedback_patterns = self._analyze_feedback_patterns(feedback)
        
        # Tag usage consistency
        tagged_notes = [n for n in notes if n.tags]
        tag_usage_rate = len(tagged_notes) / len(notes)
        
        return {
            "total_notes": len(notes),
            "resolution_rate": resolution_rate,
            "average_priority": avg_priority,
            "tag_usage_rate": tag_usage_rate,
            "feedback_acceptance_rate": feedback_patterns.get("acceptance_rate", 0),
            "notes_with_feedback": len([n for n in notes if any(fb.related_note_id == n.note_id for fb in feedback)])
        }

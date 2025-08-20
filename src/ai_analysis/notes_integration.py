# src/ai_analysis/notes_integration.py
"""
Integration helpers for AI Notes System with existing components
"""

from typing import Dict, List, Any
from ..utils.logger import get_logger
from .notes_manager import NotesManager
from .pattern_analyzer import PatternAnalyzer
from .rule_suggester import RuleSuggester

logger = get_logger(__name__)

class NotesIntegration:
    """Integrates AI Notes System with existing AI analysis components"""
    
    def __init__(self, notes_manager: NotesManager = None):
        self.notes_manager = notes_manager or NotesManager()
        self.logger = logger
    
    def log_ai_analysis_observation(self, batch_id: str, analysis_results: Dict, 
                                   confidence_level: str = "medium") -> str:
        """Log observations from AI analysis results"""
        try:
            # Extract key information from analysis
            low_confidence_count = analysis_results.get('total_low_confidence', 0)
            suggestions_count = len(analysis_results.get('suggestions', []))
            
            # Create observation content
            content = f"Batch {batch_id} analysis: {low_confidence_count} low-confidence items, {suggestions_count} suggestions generated"
            
            # Determine priority based on results
            priority = self._calculate_priority(low_confidence_count, suggestions_count)
            
            # Create context
            context = {
                "batch_id": batch_id,
                "analysis_type": "pattern_analysis",
                "low_confidence_count": low_confidence_count,
                "suggestions_count": suggestions_count,
                "confidence_level": confidence_level
            }
            
            # Add tags
            tags = ["batch_analysis", f"batch_{batch_id}"]
            if low_confidence_count > 20:
                tags.append("high_failure_rate")
            if suggestions_count > 5:
                tags.append("many_suggestions")
            
            note_id = self.notes_manager.add_ai_note(
                note_type="observation",
                content=content,
                context=context,
                tags=tags,
                priority=priority
            )
            
            self.logger.info(f"Logged AI analysis observation for batch {batch_id}", note_id=note_id)
            return note_id
            
        except Exception as e:
            self.logger.error(f"Failed to log AI analysis observation: {e}")
            return ""
    
    def log_rule_suggestion(self, suggestion: Dict, batch_context: Dict = None) -> str:
        """Log a rule suggestion from AI analysis"""
        try:
            rule_type = suggestion.get('type', 'unknown')
            pattern = suggestion.get('pattern', '')
            confidence = suggestion.get('confidence', 0)
            
            content = f"AI suggests {rule_type} rule: '{pattern}' (confidence: {confidence:.2f})"
            
            context = {
                "suggestion": suggestion,
                "batch_context": batch_context or {},
                "ai_confidence": confidence
            }
            
            priority = 4 if confidence > 0.8 else 3 if confidence > 0.6 else 2
            
            tags = ["rule_suggestion", f"type_{rule_type}"]
            if confidence > 0.8:
                tags.append("high_confidence")
            
            note_id = self.notes_manager.add_ai_note(
                note_type="suggestion",
                content=content,
                context=context,
                tags=tags,
                priority=priority
            )
            
            self.logger.info(f"Logged rule suggestion: {rule_type}", note_id=note_id)
            return note_id
            
        except Exception as e:
            self.logger.error(f"Failed to log rule suggestion: {e}")
            return ""
    
    def log_human_rule_decision(self, note_id: str, decision: str, 
                               user_comment: str = "", user_id: str = "user") -> str:
        """Log human decision on AI rule suggestion"""
        try:
            action_map = {
                "accept": "accepted",
                "reject": "rejected", 
                "modify": "modified",
                "ignore": "ignored"
            }
            
            action = action_map.get(decision.lower(), "reviewed")
            content = f"Rule suggestion {decision}: {user_comment}" if user_comment else f"Rule suggestion {decision}"
            
            feedback_id = self.notes_manager.add_human_feedback(
                content=content,
                related_note_id=note_id,
                action_taken=action,
                user_id=user_id
            )
            
            # Update note status based on decision
            if decision.lower() in ["accept", "reject"]:
                self.notes_manager.update_note_status(note_id, "resolved")
            
            self.logger.info(f"Logged human decision: {decision}", 
                           note_id=note_id, feedback_id=feedback_id)
            return feedback_id
            
        except Exception as e:
            self.logger.error(f"Failed to log human decision: {e}")
            return ""
    
    def log_batch_processing_findings(self, batch_results: List[Dict], 
                                     batch_id: str) -> List[str]:
        """Log findings from batch processing results"""
        note_ids = []
        
        try:
            # Analyze confidence distribution
            confidence_counts = {'High': 0, 'Medium': 0, 'Low': 0}
            for result in batch_results:
                level = result.get('confidence_level', 'Low')
                confidence_counts[level] += 1
            
            total = len(batch_results)
            low_percentage = (confidence_counts['Low'] / total * 100) if total > 0 else 0
            
            # Log overall batch performance
            if low_percentage > 50:  # More than 50% low confidence
                content = f"High failure rate in batch {batch_id}: {low_percentage:.1f}% low confidence ({confidence_counts['Low']}/{total} items)"
                note_id = self.notes_manager.add_ai_note(
                    note_type="finding",
                    content=content,
                    context={
                        "batch_id": batch_id,
                        "confidence_distribution": confidence_counts,
                        "failure_rate": low_percentage
                    },
                    tags=["batch_performance", "high_failure_rate", f"batch_{batch_id}"],
                    priority=4
                )
                note_ids.append(note_id)
            
            # Log specific pattern findings
            if confidence_counts['Low'] > 10:  # Significant number of low confidence
                # Use existing PatternAnalyzer to find patterns
                pattern_analyzer = PatternAnalyzer()
                analysis = pattern_analyzer.analyze_low_confidence_results(batch_results)
                
                # Log common patterns found
                common_patterns = analysis.get('common_patterns', {})
                if common_patterns.get('common_words'):
                    top_words = list(common_patterns['common_words'].keys())[:3]
                    content = f"Common patterns in low-confidence items: {', '.join(top_words)}"
                    note_id = self.notes_manager.add_ai_note(
                        note_type="finding",
                        content=content,
                        context={
                            "batch_id": batch_id,
                            "pattern_analysis": common_patterns
                        },
                        tags=["pattern_finding", f"batch_{batch_id}"],
                        priority=3
                    )
                    note_ids.append(note_id)
            
            self.logger.info(f"Logged {len(note_ids)} findings for batch {batch_id}")
            return note_ids
            
        except Exception as e:
            self.logger.error(f"Failed to log batch findings: {e}")
            return note_ids
    
    def log_iterative_improvement_cycle(self, cycle_number: int, 
                                       before_metrics: Dict, after_metrics: Dict) -> str:
        """Log results of an iterative improvement cycle"""
        try:
            before_success = before_metrics.get('high_confidence_rate', 0)
            after_success = after_metrics.get('high_confidence_rate', 0)
            improvement = after_success - before_success
            
            content = f"Improvement cycle {cycle_number}: Success rate {before_success:.1%} → {after_success:.1%} (Δ{improvement:+.1%})"
            
            context = {
                "cycle_number": cycle_number,
                "before_metrics": before_metrics,
                "after_metrics": after_metrics,
                "improvement": improvement
            }
            
            priority = 4 if improvement > 0.1 else 3 if improvement > 0 else 2
            
            tags = ["improvement_cycle", f"cycle_{cycle_number}"]
            if improvement > 0.1:
                tags.append("significant_improvement")
            elif improvement < 0:
                tags.append("performance_decline")
            
            note_id = self.notes_manager.add_ai_note(
                note_type="finding",
                content=content,
                context=context,
                tags=tags,
                priority=priority
            )
            
            self.logger.info(f"Logged improvement cycle {cycle_number}", note_id=note_id)
            return note_id
            
        except Exception as e:
            self.logger.error(f"Failed to log improvement cycle: {e}")
            return ""
    
    def _calculate_priority(self, low_confidence_count: int, suggestions_count: int) -> int:
        """Calculate priority based on analysis results"""
        if low_confidence_count > 30 or suggestions_count > 8:
            return 4  # High priority
        elif low_confidence_count > 15 or suggestions_count > 4:
            return 3  # Medium priority
        elif low_confidence_count > 5 or suggestions_count > 1:
            return 2  # Low priority
        else:
            return 1  # Very low priority
    
    def get_active_suggestions(self) -> List[Dict]:
        """Get all active AI suggestions that need human review"""
        suggestion_notes = self.notes_manager.get_notes_by_type("suggestion")
        active_suggestions = [
            {
                "note_id": note.note_id,
                "content": note.content,
                "context": note.context,
                "priority": note.priority,
                "timestamp": note.timestamp
            }
            for note in suggestion_notes 
            if note.status == "active"
        ]
        
        # Sort by priority (highest first) then by timestamp (newest first)
        active_suggestions.sort(key=lambda x: (-x["priority"], -x["timestamp"].timestamp()))
        
        return active_suggestions
    
    def get_notes_summary_for_dashboard(self) -> Dict:
        """Get summary data for integration with progress tracking dashboard"""
        summary = self.notes_manager.get_summary()
        recent_activity = self.notes_manager.get_recent_activity(hours=24)
        
        active_suggestions = len([
            n for n in self.notes_manager.notes 
            if n.note_type == "suggestion" and n.status == "active"
        ])
        
        high_priority_active = len([
            n for n in self.notes_manager.notes 
            if n.priority >= 4 and n.status == "active"
        ])
        
        return {
            "total_notes": summary["total_notes"],
            "active_suggestions": active_suggestions,
            "high_priority_active": high_priority_active,
            "recent_notes_24h": recent_activity["notes_count"],
            "recent_feedback_24h": recent_activity["feedback_count"],
            "feedback_acceptance_rate": self._calculate_acceptance_rate()
        }
    
    def _calculate_acceptance_rate(self) -> float:
        """Calculate overall feedback acceptance rate"""
        if not self.notes_manager.feedback:
            return 0.0
        
        accepted = len([
            fb for fb in self.notes_manager.feedback 
            if fb.action_taken == "accepted"
        ])
        
        return accepted / len(self.notes_manager.feedback)

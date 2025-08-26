# src/batch_processor/feedback_loop.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import json
from pathlib import Path

from .processor import BatchResult, ProcessingResult

try:
    from ..utils.logger import get_logger
    from ..rule_editor.manager import RuleManager
    from ..rule_editor.workflow import ApprovalWorkflow
except ImportError:
    # Fallback for when running as script
    from utils.logger import get_logger
    from rule_editor.manager import RuleManager
    from rule_editor.workflow import ApprovalWorkflow

logger = get_logger(__name__)

class RefinementAction(Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    MODIFY = "modify"
    ADD_RULE = "add_rule"
    NEEDS_REVIEW = "needs_review"

@dataclass
class FeedbackItem:
    """Individual feedback item from batch processing"""
    product_id: str
    original_description: str
    generated_description: str
    confidence_score: float
    confidence_level: str
    action: RefinementAction
    notes: str
    timestamp: str
    batch_id: str = ""
    processing_time: float = 0.0
    extracted_features: Dict[str, str] = None

    def __post_init__(self):
        if self.extracted_features is None:
            self.extracted_features = {}

@dataclass
class FeedbackSummary:
    """Summary of feedback processing results"""
    batch_id: str
    total_items: int
    auto_accepted: int
    needs_review: int
    success_rate: float
    high_confidence_rate: float
    improvement_opportunities: List[str]
    timestamp: str

class FeedbackLoopManager:
    """Manages the feedback loop for iterative improvement"""
    
    def __init__(self, data_dir: Path, rule_manager: RuleManager = None, approval_workflow: ApprovalWorkflow = None):
        self.data_dir = Path(data_dir)
        self.feedback_history: List[FeedbackItem] = []
        self.rule_changes: List[Dict] = []
        self.rule_manager = rule_manager
        self.approval_workflow = approval_workflow
        
        # Ensure feedback directory exists
        self.feedback_dir = self.data_dir / "feedback"
        self.feedback_dir.mkdir(exist_ok=True)
        
        # Load existing feedback history
        self._load_feedback_history()
    
    def process_batch_feedback(self, batch_result: BatchResult) -> FeedbackSummary:
        """Process feedback from a completed batch"""
        logger.info(f"Processing feedback for batch {batch_result.batch_id}")
        
        feedback_items = []
        auto_accepted = 0
        needs_review = 0
        improvement_opportunities = []
        
        for result in batch_result.results:
            # Determine action based on confidence level
            action = self._determine_action(result)
            
            # Create feedback item
            feedback_item = FeedbackItem(
                product_id=result.item_id,
                original_description=result.original_description,
                generated_description=result.enhanced_description,
                confidence_score=result.confidence_score,
                confidence_level=result.confidence_level,
                action=action,
                notes=self._generate_feedback_notes(result),
                timestamp=datetime.now().isoformat(),
                batch_id=batch_result.batch_id,
                processing_time=result.processing_time,
                extracted_features=result.extracted_features
            )
            
            feedback_items.append(feedback_item)
            
            # Count actions
            if action == RefinementAction.ACCEPT:
                auto_accepted += 1
            elif action in [RefinementAction.NEEDS_REVIEW, RefinementAction.ADD_RULE]:
                needs_review += 1
                improvement_opportunities.append(self._identify_improvement_opportunity(result))
        
        # Add to history
        self.feedback_history.extend(feedback_items)
        
        # Create summary
        summary = FeedbackSummary(
            batch_id=batch_result.batch_id,
            total_items=batch_result.total_items,
            auto_accepted=auto_accepted,
            needs_review=needs_review,
            success_rate=batch_result.summary.get('success_rate', 0.0),
            high_confidence_rate=batch_result.summary.get('high_confidence_rate', 0.0),
            improvement_opportunities=list(set(filter(None, improvement_opportunities))),
            timestamp=datetime.now().isoformat()
        )
        
        # Save feedback data
        self._save_batch_feedback(batch_result.batch_id, feedback_items, summary)
        
        logger.info(f"Processed feedback: {auto_accepted} accepted, {needs_review} need review")
        return summary
    
    def _determine_action(self, result: ProcessingResult) -> RefinementAction:
        """Determine the appropriate action for a processing result"""
        if not result.success:
            return RefinementAction.ADD_RULE
        
        if result.confidence_level == "High":
            return RefinementAction.ACCEPT
        elif result.confidence_level == "Medium":
            # Medium confidence items might need review if they have specific patterns
            if self._has_improvement_pattern(result):
                return RefinementAction.NEEDS_REVIEW
            else:
                return RefinementAction.ACCEPT
        else:  # Low confidence
            return RefinementAction.NEEDS_REVIEW
    
    def _has_improvement_pattern(self, result: ProcessingResult) -> bool:
        """Check if result has patterns that suggest improvement opportunities"""
        # Look for common improvement patterns
        features = result.extracted_features
        
        # Missing key features
        if not features.get('material') or not features.get('size'):
            return True
        
        # Very generic descriptions
        if len(result.enhanced_description.split()) < 5:
            return True
        
        # Confidence score near threshold boundaries
        if 0.6 <= result.confidence_score <= 0.65:  # Near medium/low boundary
            return True
        
        return False
    
    def _generate_feedback_notes(self, result: ProcessingResult) -> str:
        """Generate descriptive notes for feedback item"""
        notes = []
        
        if not result.success:
            notes.append(f"Processing failed: {result.error_message}")
        else:
            notes.append(f"Confidence: {result.confidence_level} ({result.confidence_score:.3f})")
            
            if result.confidence_level == "Low":
                # Identify specific issues
                features = result.extracted_features
                if not features.get('material'):
                    notes.append("Missing material identification")
                if not features.get('size'):
                    notes.append("Missing size information")
                if len(result.enhanced_description.split()) < 5:
                    notes.append("Description too brief")
        
        return "; ".join(notes)
    
    def _identify_improvement_opportunity(self, result: ProcessingResult) -> Optional[str]:
        """Identify specific improvement opportunity from result"""
        if not result.success:
            return "Processing failure - needs rule addition"
        
        features = result.extracted_features
        
        if not features.get('material'):
            return "Material identification improvement"
        elif not features.get('size'):
            return "Size extraction improvement"
        elif result.confidence_level == "Low":
            return "General description enhancement"
        elif self._has_improvement_pattern(result):
            return "Pattern-based enhancement"
        
        return None
    
    def apply_rule_changes(self, new_rules: List[Dict], reviewer: str = "system") -> bool:
        """Apply approved rule changes to the system"""
        if not self.rule_manager or not self.approval_workflow:
            logger.warning("No rule manager or approval workflow configured")
            return False
        
        try:
            applied_rules = []
            
            for rule in new_rules:
                # Submit for approval workflow
                approval_id = self.approval_workflow.submit_for_approval(rule)
                
                # For now, auto-approve system-generated rules with low risk
                if self._is_low_risk_rule(rule):
                    success = self.approval_workflow.approve_rule(
                        approval_id, 
                        reviewer, 
                        "Auto-approved low-risk system rule"
                    )
                    
                    if success:
                        applied_rules.append(rule)
                        logger.info(f"Applied rule: {rule.get('name', 'unnamed')}")
                else:
                    logger.info(f"Rule submitted for manual approval: {approval_id}")
            
            # Track rule changes
            change_record = {
                'timestamp': datetime.now().isoformat(),
                'reviewer': reviewer,
                'rules_applied': len(applied_rules),
                'rules_pending': len(new_rules) - len(applied_rules),
                'rules': applied_rules
            }
            
            self.rule_changes.append(change_record)
            
            return len(applied_rules) > 0
            
        except Exception as e:
            logger.error(f"Error applying rule changes: {e}")
            return False
    
    def _is_low_risk_rule(self, rule: Dict) -> bool:
        """Determine if a rule is low risk and can be auto-approved"""
        # Simple heuristics for low-risk rules
        confidence = rule.get('confidence', 0)
        rule_type = rule.get('type', '')
        
        # High confidence, simple improvement rules
        if confidence > 0.9 and rule_type in ['enhancement', 'feature_extraction']:
            return True
        
        # Rules that only add information, don't change existing
        if rule.get('action') == 'append' and not rule.get('replaces'):
            return True
        
        return False
    
    def get_feedback_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get feedback summary for recent period"""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        recent_feedback = [
            item for item in self.feedback_history
            if datetime.fromisoformat(item.timestamp).timestamp() > cutoff_date
        ]
        
        if not recent_feedback:
            return {
                'period_days': days,
                'total_items': 0,
                'no_data': True
            }
        
        # Calculate statistics
        action_counts = {}
        confidence_counts = {'High': 0, 'Medium': 0, 'Low': 0}
        total_confidence = 0
        
        for item in recent_feedback:
            action_counts[item.action.value] = action_counts.get(item.action.value, 0) + 1
            confidence_counts[item.confidence_level] += 1
            total_confidence += item.confidence_score
        
        avg_confidence = total_confidence / len(recent_feedback)
        
        return {
            'period_days': days,
            'total_items': len(recent_feedback),
            'action_distribution': action_counts,
            'confidence_distribution': confidence_counts,
            'average_confidence': round(avg_confidence, 3),
            'auto_accept_rate': round(action_counts.get('accept', 0) / len(recent_feedback) * 100, 2),
            'review_needed_rate': round(
                (action_counts.get('needs_review', 0) + action_counts.get('add_rule', 0)) 
                / len(recent_feedback) * 100, 2
            )
        }
    
    def get_improvement_trends(self) -> Dict[str, Any]:
        """Analyze improvement trends over time"""
        if len(self.feedback_history) < 20:
            return {'insufficient_data': True}
        
        # Group by batches
        batch_data = {}
        for item in self.feedback_history:
            if item.batch_id not in batch_data:
                batch_data[item.batch_id] = []
            batch_data[item.batch_id].append(item)
        
        # Calculate trends
        batch_scores = []
        batch_dates = []
        
        for batch_id, items in batch_data.items():
            avg_confidence = sum(item.confidence_score for item in items) / len(items)
            batch_scores.append(avg_confidence)
            # Use first item's timestamp as batch timestamp
            batch_dates.append(items[0].timestamp)
        
        # Sort by date
        sorted_data = sorted(zip(batch_dates, batch_scores))
        
        if len(sorted_data) >= 3:
            recent_avg = sum(score for _, score in sorted_data[-3:]) / 3
            early_avg = sum(score for _, score in sorted_data[:3]) / 3
            improvement = recent_avg - early_avg
        else:
            improvement = 0
        
        return {
            'total_batches': len(batch_data),
            'improvement_trend': round(improvement, 3),
            'recent_average_confidence': round(recent_avg if len(sorted_data) >= 3 else 0, 3),
            'trend_direction': 'improving' if improvement > 0.01 else 'stable' if improvement > -0.01 else 'declining'
        }
    
    def _save_batch_feedback(self, batch_id: str, feedback_items: List[FeedbackItem], summary: FeedbackSummary):
        """Save batch feedback to file"""
        try:
            feedback_file = self.feedback_dir / f"{batch_id}_feedback.json"
            
            data = {
                'batch_id': batch_id,
                'summary': {
                    'total_items': summary.total_items,
                    'auto_accepted': summary.auto_accepted,
                    'needs_review': summary.needs_review,
                    'success_rate': summary.success_rate,
                    'high_confidence_rate': summary.high_confidence_rate,
                    'improvement_opportunities': summary.improvement_opportunities,
                    'timestamp': summary.timestamp
                },
                'feedback_items': [
                    {
                        'product_id': item.product_id,
                        'confidence_level': item.confidence_level,
                        'confidence_score': item.confidence_score,
                        'action': item.action.value,
                        'notes': item.notes,
                        'timestamp': item.timestamp,
                        'processing_time': item.processing_time,
                        'extracted_features': item.extracted_features
                    }
                    for item in feedback_items
                ]
            }
            
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.debug(f"Saved batch feedback to {feedback_file}")
            
        except Exception as e:
            logger.error(f"Error saving batch feedback: {e}")
    
    def _load_feedback_history(self):
        """Load existing feedback history from files"""
        try:
            feedback_files = list(self.feedback_dir.glob("*_feedback.json"))
            
            for feedback_file in feedback_files:
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert to FeedbackItem objects
                for item_data in data.get('feedback_items', []):
                    feedback_item = FeedbackItem(
                        product_id=item_data['product_id'],
                        original_description=item_data.get('original_description', ''),
                        generated_description=item_data.get('generated_description', ''),
                        confidence_score=item_data['confidence_score'],
                        confidence_level=item_data['confidence_level'],
                        action=RefinementAction(item_data['action']),
                        notes=item_data['notes'],
                        timestamp=item_data['timestamp'],
                        batch_id=data['batch_id'],
                        processing_time=item_data.get('processing_time', 0.0),
                        extracted_features=item_data.get('extracted_features', {})
                    )
                    self.feedback_history.append(feedback_item)
            
            logger.info(f"Loaded {len(self.feedback_history)} feedback items from history")
            
        except Exception as e:
            logger.error(f"Error loading feedback history: {e}")
    
    def export_feedback_data(self, filepath: str):
        """Export all feedback data for analysis"""
        export_data = {
            'feedback_history': [
                {
                    'product_id': item.product_id,
                    'batch_id': item.batch_id,
                    'confidence_level': item.confidence_level,
                    'confidence_score': item.confidence_score,
                    'action': item.action.value,
                    'notes': item.notes,
                    'timestamp': item.timestamp,
                    'processing_time': item.processing_time,
                    'extracted_features': item.extracted_features
                }
                for item in self.feedback_history
            ],
            'rule_changes': self.rule_changes,
            'exported_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported feedback data to {filepath}")


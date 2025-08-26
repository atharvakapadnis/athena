# src/rule_editor/workflow.py
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid

from .validator import RuleValidator
from .manager import RuleManager

@dataclass
class ApprovalRequest:
    """Request for rule approval"""
    id: str
    rule: Dict
    validation: object  # ValidationResult
    submitted_at: str
    status: str  # 'pending', 'approved', 'rejected', 'modified'
    reviewer: str = ""
    reasoning: str = ""
    approved_at: str = ""
    rejected_at: str = ""

class ApprovalWorkflow:
    """Manages the approval workflow for rules"""
    
    def __init__(self, rule_manager: RuleManager, validator: RuleValidator):
        self.rule_manager = rule_manager
        self.validator = validator
        self.pending_approvals = []
        self.completed_approvals = []
    
    def submit_for_approval(self, rule_suggestion: Dict) -> str:
        """Submit a rule for approval"""
        # Validate the rule
        validation = self.validator.validate_rule(rule_suggestion)
        
        if not validation.is_valid:
            raise ValueError(f"Rule validation failed: {validation.errors}")
        
        # Add to pending approvals
        approval_id = str(uuid.uuid4())
        approval_request = ApprovalRequest(
            id=approval_id,
            rule=rule_suggestion,
            validation=validation,
            submitted_at=datetime.now().isoformat(),
            status='pending'
        )
        
        self.pending_approvals.append(approval_request)
        
        return approval_id
    
    def approve_rule(self, approval_id: str, reviewer: str, reasoning: str = "") -> bool:
        """Approve a rule"""
        approval = self._find_approval(approval_id)
        if not approval:
            return False
        
        # Update approval status
        approval.status = 'approved'
        approval.reviewer = reviewer
        approval.reasoning = reasoning
        approval.approved_at = datetime.now().isoformat()
        
        # Add to rule manager
        decision_data = {
            'reviewer': reviewer,
            'reasoning': reasoning,
            'decision': 'approve'
        }
        
        rule_id = self.rule_manager.add_approved_rule(approval.rule, decision_data)
        
        # Move to completed approvals
        self._move_to_completed(approval)
        
        return True
    
    def reject_rule(self, approval_id: str, reviewer: str, reasoning: str = "") -> bool:
        """Reject a rule"""
        approval = self._find_approval(approval_id)
        if not approval:
            return False
        
        # Update approval status
        approval.status = 'rejected'
        approval.reviewer = reviewer
        approval.reasoning = reasoning
        approval.rejected_at = datetime.now().isoformat()
        
        # Move to completed approvals
        self._move_to_completed(approval)
        
        return True
    
    def modify_rule(self, approval_id: str, modified_rule: Dict, 
                   reviewer: str, reasoning: str = "") -> bool:
        """Modify and approve a rule"""
        approval = self._find_approval(approval_id)
        if not approval:
            return False
        
        # Validate modified rule
        validation = self.validator.validate_rule(modified_rule)
        if not validation.is_valid:
            raise ValueError(f"Modified rule validation failed: {validation.errors}")
        
        # Update approval with modified rule
        approval.rule = modified_rule
        approval.validation = validation
        approval.status = 'modified'
        approval.reviewer = reviewer
        approval.reasoning = reasoning
        approval.approved_at = datetime.now().isoformat()
        
        # Add to rule manager
        decision_data = {
            'reviewer': reviewer,
            'reasoning': reasoning,
            'decision': 'modify',
            'was_modified': True
        }
        
        rule_id = self.rule_manager.add_approved_rule(modified_rule, decision_data)
        
        # Move to completed approvals
        self._move_to_completed(approval)
        
        return True
    
    def _find_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Find approval by ID"""
        for approval in self.pending_approvals:
            if approval.id == approval_id:
                return approval
        return None
    
    def _move_to_completed(self, approval: ApprovalRequest):
        """Move approval from pending to completed"""
        if approval in self.pending_approvals:
            self.pending_approvals.remove(approval)
            self.completed_approvals.append(approval)
    
    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approvals"""
        return [a for a in self.pending_approvals if a.status == 'pending']
    
    def get_completed_approvals(self) -> List[ApprovalRequest]:
        """Get all completed approvals"""
        return self.completed_approvals
    
    def get_approval_by_id(self, approval_id: str) -> Optional[ApprovalRequest]:
        """Get approval by ID from all approvals"""
        # Check pending first
        for approval in self.pending_approvals:
            if approval.id == approval_id:
                return approval
        
        # Check completed
        for approval in self.completed_approvals:
            if approval.id == approval_id:
                return approval
        
        return None
    
    def get_approvals_by_status(self, status: str) -> List[ApprovalRequest]:
        """Get approvals by status"""
        all_approvals = self.pending_approvals + self.completed_approvals
        return [a for a in all_approvals if a.status == status]
    
    def get_approvals_by_reviewer(self, reviewer: str) -> List[ApprovalRequest]:
        """Get approvals by reviewer"""
        return [a for a in self.completed_approvals if a.reviewer == reviewer]
    
    def get_high_priority_approvals(self) -> List[ApprovalRequest]:
        """Get high priority pending approvals"""
        high_priority = []
        
        for approval in self.pending_approvals:
            # Consider high priority if:
            # - High confidence rule
            # - No conflicts
            # - Few warnings
            if hasattr(approval.validation, 'conflicts') and hasattr(approval.validation, 'warnings'):
                has_conflicts = len(approval.validation.conflicts) > 0
                has_many_warnings = len(approval.validation.warnings) > 2
                
                rule_confidence = approval.rule.get('confidence', 0)
                
                if rule_confidence > 0.8 and not has_conflicts and not has_many_warnings:
                    high_priority.append(approval)
        
        return high_priority
    
    def batch_approve(self, approval_ids: List[str], reviewer: str, reasoning: str = "") -> Dict[str, bool]:
        """Approve multiple rules in batch"""
        results = {}
        
        for approval_id in approval_ids:
            try:
                success = self.approve_rule(approval_id, reviewer, reasoning)
                results[approval_id] = success
            except Exception as e:
                results[approval_id] = False
                print(f"Error approving rule {approval_id}: {e}")
        
        return results
    
    def get_approval_statistics(self) -> Dict:
        """Get approval statistics"""
        all_approvals = self.pending_approvals + self.completed_approvals
        
        status_counts = {}
        reviewer_counts = {}
        
        for approval in all_approvals:
            # Count by status
            status_counts[approval.status] = status_counts.get(approval.status, 0) + 1
            
            # Count by reviewer (only for completed)
            if approval.reviewer:
                reviewer_counts[approval.reviewer] = reviewer_counts.get(approval.reviewer, 0) + 1
        
        # Calculate approval rate
        completed = len(self.completed_approvals)
        approved = status_counts.get('approved', 0) + status_counts.get('modified', 0)
        approval_rate = (approved / completed * 100) if completed > 0 else 0
        
        return {
            'total_approvals': len(all_approvals),
            'pending': len(self.pending_approvals),
            'completed': len(self.completed_approvals),
            'status_breakdown': status_counts,
            'reviewer_breakdown': reviewer_counts,
            'approval_rate': round(approval_rate, 2),
            'generated_at': datetime.now().isoformat()
        }
    
    def export_approval_history(self, filepath: str):
        """Export approval history to JSON file"""
        import json
        
        export_data = {
            'pending_approvals': [],
            'completed_approvals': [],
            'exported_at': datetime.now().isoformat()
        }
        
        # Convert pending approvals
        for approval in self.pending_approvals:
            export_data['pending_approvals'].append({
                'id': approval.id,
                'rule': approval.rule,
                'submitted_at': approval.submitted_at,
                'status': approval.status
            })
        
        # Convert completed approvals
        for approval in self.completed_approvals:
            export_data['completed_approvals'].append({
                'id': approval.id,
                'rule': approval.rule,
                'submitted_at': approval.submitted_at,
                'status': approval.status,
                'reviewer': approval.reviewer,
                'reasoning': approval.reasoning,
                'approved_at': approval.approved_at,
                'rejected_at': approval.rejected_at
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def clear_completed_approvals(self, older_than_days: int = 30):
        """Clear old completed approvals"""
        if older_than_days <= 0:
            return
        
        cutoff_date = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)
        
        self.completed_approvals = [
            approval for approval in self.completed_approvals
            if datetime.fromisoformat(approval.submitted_at).timestamp() > cutoff_date
        ]

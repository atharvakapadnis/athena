# tests/test_rule_editor.py
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from src.rule_editor import (
    RuleReviewInterface, RuleSuggestion, RuleDecision,
    RuleValidator, ValidationResult,
    RuleManager,
    ApprovalWorkflow, ApprovalRequest
)

class TestRuleReviewInterface:
    """Test rule review interface functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.interface = RuleReviewInterface()
    
    def test_add_suggestion(self):
        """Test adding rule suggestions"""
        suggestion = RuleSuggestion(
            id="test_1",
            rule_type="company",
            pattern="TEST",
            replacement="Test Company",
            confidence=0.8,
            reasoning="Test reasoning",
            examples=["TEST 123"],
            priority=3
        )
        
        self.interface.add_suggestion(suggestion)
        assert len(self.interface.pending_suggestions) == 1
        assert suggestion.timestamp is not None
    
    def test_get_pending_suggestions(self):
        """Test retrieving pending suggestions"""
        suggestion1 = RuleSuggestion(
            id="test_1", rule_type="company", pattern="TEST1", 
            replacement="Test1", confidence=0.8, reasoning="reason1",
            examples=["TEST1"], priority=1
        )
        suggestion2 = RuleSuggestion(
            id="test_2", rule_type="company", pattern="TEST2", 
            replacement="Test2", confidence=0.9, reasoning="reason2",
            examples=["TEST2"], priority=3
        )
        
        self.interface.add_suggestion(suggestion1)
        self.interface.add_suggestion(suggestion2)
        
        # Test without threshold
        all_suggestions = self.interface.get_pending_suggestions()
        assert len(all_suggestions) == 2
        
        # Test with threshold
        high_priority = self.interface.get_pending_suggestions(priority_threshold=2)
        assert len(high_priority) == 1
        assert high_priority[0].id == "test_2"
    
    def test_make_decision(self):
        """Test making decisions on suggestions"""
        suggestion = RuleSuggestion(
            id="test_1", rule_type="company", pattern="TEST", 
            replacement="Test", confidence=0.8, reasoning="reason",
            examples=["TEST"], priority=1
        )
        
        self.interface.add_suggestion(suggestion)
        
        decision = self.interface.make_decision(
            rule_id="test_1",
            decision="approve",
            reasoning="Looks good",
            reviewer="user1"
        )
        
        assert decision.rule_id == "test_1"
        assert decision.decision == "approve"
        assert decision.reasoning == "Looks good"
        assert decision.reviewer == "user1"
        assert decision.timestamp is not None
        
        # Should be removed from pending
        assert len(self.interface.pending_suggestions) == 0
        assert len(self.interface.decisions) == 1
    
    def test_get_suggestion_by_id(self):
        """Test retrieving suggestion by ID"""
        suggestion = RuleSuggestion(
            id="test_1", rule_type="company", pattern="TEST", 
            replacement="Test", confidence=0.8, reasoning="reason",
            examples=["TEST"], priority=1
        )
        
        self.interface.add_suggestion(suggestion)
        
        found = self.interface.get_suggestion_by_id("test_1")
        assert found is not None
        assert found.id == "test_1"
        
        not_found = self.interface.get_suggestion_by_id("not_exist")
        assert not_found is None


class TestRuleValidator:
    """Test rule validator functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.existing_rules = [
            {
                'rule_type': 'company',
                'pattern': 'EXISTING',
                'replacement': 'Existing Company'
            }
        ]
        self.validator = RuleValidator(self.existing_rules)
    
    def test_validate_valid_rule(self):
        """Test validation of valid rule"""
        valid_rule = {
            'rule_type': 'company',
            'pattern': 'TEST',
            'replacement': 'Test Company'
        }
        
        result = self.validator.validate_rule(valid_rule)
        assert result.is_valid == True
        assert len(result.errors) == 0
    
    def test_validate_missing_fields(self):
        """Test validation with missing fields"""
        invalid_rule = {
            'rule_type': 'company',
            # Missing pattern and replacement
        }
        
        result = self.validator.validate_rule(invalid_rule)
        assert result.is_valid == False
        assert len(result.errors) >= 1
        assert any('pattern' in error for error in result.errors)
    
    def test_validate_invalid_regex(self):
        """Test validation with invalid regex"""
        invalid_rule = {
            'rule_type': 'company',
            'pattern': '[unclosed',  # Invalid regex
            'replacement': 'Test'
        }
        
        result = self.validator.validate_rule(invalid_rule)
        assert result.is_valid == False
        assert len(result.errors) >= 1
        assert any('regex' in error.lower() for error in result.errors)
    
    def test_conflict_detection(self):
        """Test conflict detection"""
        conflicting_rule = {
            'rule_type': 'company',
            'pattern': 'EXISTING',  # Same as existing rule
            'replacement': 'Different Company'  # Different replacement
        }
        
        result = self.validator.validate_rule(conflicting_rule)
        assert len(result.conflicts) >= 1
    
    def test_warning_detection(self):
        """Test warning detection"""
        warning_rule = {
            'rule_type': 'company',
            'pattern': 'X',  # Very short pattern
            'replacement': 'Test'
        }
        
        result = self.validator.validate_rule(warning_rule)
        assert len(result.warnings) >= 1
        assert any('short' in warning.lower() for warning in result.warnings)


class TestRuleManager:
    """Test rule manager functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.rules_dir = Path(self.temp_dir)
        self.manager = RuleManager(self.rules_dir)
    
    def test_load_save_current_rules(self):
        """Test loading and saving current rules"""
        test_rules = [
            {
                'rule_type': 'company',
                'pattern': 'TEST',
                'replacement': 'Test Company'
            }
        ]
        
        # Save rules
        self.manager.save_current_rules(test_rules)
        
        # Load rules
        loaded_rules = self.manager.load_current_rules()
        assert len(loaded_rules) == 1
        assert loaded_rules[0]['pattern'] == 'TEST'
    
    def test_add_approved_rule(self):
        """Test adding approved rule"""
        rule = {
            'rule_type': 'company',
            'pattern': 'TEST',
            'replacement': 'Test Company'
        }
        
        decision = {
            'reviewer': 'user1',
            'reasoning': 'Good rule'
        }
        
        rule_id = self.manager.add_approved_rule(rule, decision)
        assert rule_id is not None
        
        # Check if rule was added
        current_rules = self.manager.load_current_rules()
        assert len(current_rules) == 1
        assert current_rules[0]['id'] == rule_id
        assert current_rules[0]['approved_by'] == 'user1'
    
    def test_remove_rule(self):
        """Test removing rule"""
        # Add a rule first
        rule = {'rule_type': 'company', 'pattern': 'TEST', 'replacement': 'Test'}
        decision = {'reviewer': 'user1'}
        rule_id = self.manager.add_approved_rule(rule, decision)
        
        # Remove the rule
        success = self.manager.remove_rule(rule_id)
        assert success == True
        
        # Check if rule was removed
        current_rules = self.manager.load_current_rules()
        assert len(current_rules) == 0
    
    def test_get_rule_by_id(self):
        """Test retrieving rule by ID"""
        rule = {'rule_type': 'company', 'pattern': 'TEST', 'replacement': 'Test'}
        decision = {'reviewer': 'user1'}
        rule_id = self.manager.add_approved_rule(rule, decision)
        
        found_rule = self.manager.get_rule_by_id(rule_id)
        assert found_rule is not None
        assert found_rule['id'] == rule_id
        assert found_rule['pattern'] == 'TEST'
    
    def test_get_rules_by_type(self):
        """Test retrieving rules by type"""
        company_rule = {'rule_type': 'company', 'pattern': 'COMP', 'replacement': 'Company'}
        product_rule = {'rule_type': 'product', 'pattern': 'PROD', 'replacement': 'Product'}
        decision = {'reviewer': 'user1'}
        
        self.manager.add_approved_rule(company_rule, decision)
        self.manager.add_approved_rule(product_rule, decision)
        
        company_rules = self.manager.get_rules_by_type('company')
        assert len(company_rules) == 1
        assert company_rules[0]['rule_type'] == 'company'
        
        product_rules = self.manager.get_rules_by_type('product')
        assert len(product_rules) == 1
        assert product_rules[0]['rule_type'] == 'product'
    
    def test_get_rule_statistics(self):
        """Test rule statistics"""
        # Add some rules
        company_rule = {'rule_type': 'company', 'pattern': 'COMP', 'replacement': 'Company'}
        product_rule = {'rule_type': 'product', 'pattern': 'PROD', 'replacement': 'Product'}
        decision = {'reviewer': 'user1'}
        
        self.manager.add_approved_rule(company_rule, decision)
        self.manager.add_approved_rule(product_rule, decision)
        
        stats = self.manager.get_rule_statistics()
        assert stats['total_rules'] == 2
        assert stats['rule_types']['company'] == 1
        assert stats['rule_types']['product'] == 1
        assert stats['approved_by']['user1'] == 2


class TestApprovalWorkflow:
    """Test approval workflow functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.rules_dir = Path(self.temp_dir)
        self.manager = RuleManager(self.rules_dir)
        self.validator = RuleValidator([])
        self.workflow = ApprovalWorkflow(self.manager, self.validator)
    
    def test_submit_for_approval(self):
        """Test submitting rule for approval"""
        rule = {
            'rule_type': 'company',
            'pattern': 'TEST',
            'replacement': 'Test Company'
        }
        
        approval_id = self.workflow.submit_for_approval(rule)
        assert approval_id is not None
        
        pending = self.workflow.get_pending_approvals()
        assert len(pending) == 1
        assert pending[0].id == approval_id
    
    def test_approve_rule(self):
        """Test approving rule"""
        rule = {
            'rule_type': 'company',
            'pattern': 'TEST',
            'replacement': 'Test Company'
        }
        
        approval_id = self.workflow.submit_for_approval(rule)
        success = self.workflow.approve_rule(approval_id, 'user1', 'Good rule')
        
        assert success == True
        
        # Should be moved to completed
        pending = self.workflow.get_pending_approvals()
        assert len(pending) == 0
        
        completed = self.workflow.get_completed_approvals()
        assert len(completed) == 1
        assert completed[0].status == 'approved'
    
    def test_reject_rule(self):
        """Test rejecting rule"""
        rule = {
            'rule_type': 'company',
            'pattern': 'TEST',
            'replacement': 'Test Company'
        }
        
        approval_id = self.workflow.submit_for_approval(rule)
        success = self.workflow.reject_rule(approval_id, 'user1', 'Not suitable')
        
        assert success == True
        
        completed = self.workflow.get_completed_approvals()
        assert len(completed) == 1
        assert completed[0].status == 'rejected'
        assert completed[0].reasoning == 'Not suitable'
    
    def test_modify_rule(self):
        """Test modifying and approving rule"""
        rule = {
            'rule_type': 'company',
            'pattern': 'TEST',
            'replacement': 'Test Company'
        }
        
        modified_rule = {
            'rule_type': 'company',
            'pattern': 'TEST',
            'replacement': 'Modified Test Company'
        }
        
        approval_id = self.workflow.submit_for_approval(rule)
        success = self.workflow.modify_rule(approval_id, modified_rule, 'user1', 'Improved replacement')
        
        assert success == True
        
        completed = self.workflow.get_completed_approvals()
        assert len(completed) == 1
        assert completed[0].status == 'modified'
        assert completed[0].rule['replacement'] == 'Modified Test Company'
    
    def test_get_approval_statistics(self):
        """Test approval statistics"""
        rule1 = {'rule_type': 'company', 'pattern': 'TEST1', 'replacement': 'Test1'}
        rule2 = {'rule_type': 'company', 'pattern': 'TEST2', 'replacement': 'Test2'}
        
        approval_id1 = self.workflow.submit_for_approval(rule1)
        approval_id2 = self.workflow.submit_for_approval(rule2)
        
        self.workflow.approve_rule(approval_id1, 'user1', 'Good')
        self.workflow.reject_rule(approval_id2, 'user1', 'Bad')
        
        stats = self.workflow.get_approval_statistics()
        assert stats['total_approvals'] == 2
        assert stats['completed'] == 2
        assert stats['pending'] == 0
        assert stats['status_breakdown']['approved'] == 1
        assert stats['status_breakdown']['rejected'] == 1
        assert stats['approval_rate'] == 50.0  # 1 approved out of 2 completed


class TestIntegration:
    """Test integration between rule editor components"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.rules_dir = Path(self.temp_dir)
        
        # Create integrated system
        self.interface = RuleReviewInterface()
        self.manager = RuleManager(self.rules_dir)
        self.validator = RuleValidator([])
        self.workflow = ApprovalWorkflow(self.manager, self.validator)
    
    def test_full_workflow(self):
        """Test complete rule approval workflow"""
        # 1. Create a rule suggestion
        suggestion = RuleSuggestion(
            id="test_1",
            rule_type="company",
            pattern="TEST",
            replacement="Test Company",
            confidence=0.8,
            reasoning="Consistent pattern found",
            examples=["TEST 123", "TEST Corp"],
            priority=3
        )
        
        # 2. Add to interface
        self.interface.add_suggestion(suggestion)
        
        # 3. Convert to rule and submit for approval
        rule = {
            'rule_type': suggestion.rule_type,
            'pattern': suggestion.pattern,
            'replacement': suggestion.replacement,
            'confidence': suggestion.confidence
        }
        
        approval_id = self.workflow.submit_for_approval(rule)
        
        # 4. Make decision through interface
        decision = self.interface.make_decision(
            rule_id=suggestion.id,
            decision="approve",
            reasoning="Rule looks good",
            reviewer="user1"
        )
        
        # 5. Approve through workflow
        success = self.workflow.approve_rule(approval_id, "user1", "Rule looks good")
        
        # 6. Verify rule is in manager
        current_rules = self.manager.load_current_rules()
        
        assert success == True
        assert len(current_rules) == 1
        assert current_rules[0]['pattern'] == 'TEST'
        assert current_rules[0]['approved_by'] == 'user1'
        assert len(self.interface.pending_suggestions) == 0
        assert len(self.interface.decisions) == 1


if __name__ == "__main__":
    pytest.main([__file__])

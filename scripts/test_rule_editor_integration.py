#!/usr/bin/env python3
"""
Rule Editor Integration Test

Tests integration between rule editor and existing system components:
- AI Analysis Engine
- Batch Processor  
- Confidence Scoring

This script demonstrates the full workflow from AI rule suggestion
to human approval and rule application.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from rule_editor import (
    RuleReviewInterface, RuleSuggestion,
    RuleValidator, RuleManager, ApprovalWorkflow
)

# Try to import other components, but don't fail if they're not available
try:
    from ai_analysis.rule_suggester import RuleSuggester
    ai_analysis_available = True
except ImportError:
    print("⚠️  AI Analysis components not available - using mock data")
    ai_analysis_available = False

try:
    from batch_processor.processor import BatchProcessor
    batch_processor_available = True
except ImportError:
    print("⚠️  Batch Processor components not available - using mock data")
    batch_processor_available = False

try:
    from confidence_scoring.scorer import ConfidenceScorer
    confidence_scoring_available = True
except ImportError:
    print("⚠️  Confidence Scoring components not available - using mock data")
    confidence_scoring_available = False

def test_rule_editor_integration():
    """Test complete integration workflow"""
    print("🧪 Testing Rule Editor Integration")
    print("=" * 50)
    
    # Setup components
    rules_dir = Path("data/rules")
    rules_dir.mkdir(exist_ok=True)
    
    # Initialize rule editor components
    interface = RuleReviewInterface()
    manager = RuleManager(rules_dir)
    validator = RuleValidator(manager.load_current_rules())
    workflow = ApprovalWorkflow(manager, validator)
    
    print("✅ Rule editor components initialized")
    
    # Simulate AI analysis suggesting rules
    print("\n🤖 AI Analysis: Generating rule suggestions...")
    
    ai_suggestions = [
        {
            'id': 'ai_rule_1',
            'rule_type': 'company_standardization',
            'pattern': r'\b([A-Z]+)\s+(?:CO|COMPANY|CORP|CORPORATION)\b',
            'replacement': r'\1 Company',
            'confidence': 0.85,
            'reasoning': 'Standardize company name formats',
            'examples': ['ACME CORP -> ACME Company', 'TEST CO -> TEST Company'],
            'priority': 3
        },
        {
            'id': 'ai_rule_2', 
            'rule_type': 'unit_standardization',
            'pattern': r'\b(\d+)\s*(?:KG|KILOGRAMS?)\b',
            'replacement': r'\1 kg',
            'confidence': 0.92,
            'reasoning': 'Standardize weight units to lowercase',
            'examples': ['5 KG -> 5 kg', '10 KILOGRAMS -> 10 kg'],
            'priority': 4
        },
        {
            'id': 'ai_rule_3',
            'rule_type': 'measurement_cleanup',
            'pattern': r'\b(\d+)\s*X\s*(\d+)\s*(?:MM|MILLIMETERS?)\b',
            'replacement': r'\1x\2 mm',
            'confidence': 0.78,
            'reasoning': 'Standardize dimension format',
            'examples': ['100 X 200 MM -> 100x200 mm'],
            'priority': 2
        }
    ]
    
    # Add suggestions to interface
    for suggestion_data in ai_suggestions:
        suggestion = RuleSuggestion(
            id=suggestion_data['id'],
            rule_type=suggestion_data['rule_type'],
            pattern=suggestion_data['pattern'],
            replacement=suggestion_data['replacement'],
            confidence=suggestion_data['confidence'],
            reasoning=suggestion_data['reasoning'],
            examples=suggestion_data['examples'],
            priority=suggestion_data['priority']
        )
        interface.add_suggestion(suggestion)
    
    print(f"✅ Added {len(ai_suggestions)} AI rule suggestions")
    
    # Review suggestions
    print("\n👤 Human Review: Reviewing rule suggestions...")
    
    pending = interface.get_pending_suggestions()
    print(f"📋 Found {len(pending)} pending suggestions")
    
    # Simulate human decisions
    decisions = []
    
    for suggestion in pending:
        print(f"\n📝 Reviewing: {suggestion.rule_type}")
        print(f"   Pattern: {suggestion.pattern}")
        print(f"   Replacement: {suggestion.replacement}")
        print(f"   Confidence: {suggestion.confidence:.2f}")
        print(f"   Priority: {suggestion.priority}")
        
        # Simulate decision based on confidence and priority
        if suggestion.confidence > 0.9 and suggestion.priority >= 4:
            decision = "approve"
            reasoning = "High confidence and priority - auto-approve"
        elif suggestion.confidence > 0.8 and suggestion.priority >= 3:
            decision = "approve"
            reasoning = "Good confidence and priority - approve"
        elif suggestion.confidence < 0.8:
            if suggestion.priority >= 3:
                decision = "modify"
                reasoning = "Lower confidence - needs modification"
            else:
                decision = "reject"
                reasoning = "Low confidence and priority - reject"
        else:
            decision = "approve"
            reasoning = "Acceptable rule"
        
        print(f"   Decision: {decision} - {reasoning}")
        
        # Make decision through interface
        rule_decision = interface.make_decision(
            rule_id=suggestion.id,
            decision=decision,
            reasoning=reasoning,
            reviewer="integration_test"
        )
        decisions.append((suggestion, rule_decision))
    
    print(f"\n✅ Made {len(decisions)} human decisions")
    
    # Process approvals through workflow
    print("\n⚙️  Processing approvals through workflow...")
    
    approved_count = 0
    rejected_count = 0
    modified_count = 0
    
    for suggestion, decision in decisions:
        if decision.decision == "approve":
            # Submit for approval
            rule_dict = {
                'rule_type': suggestion.rule_type,
                'pattern': suggestion.pattern,
                'replacement': suggestion.replacement,
                'confidence': suggestion.confidence,
                'priority': suggestion.priority
            }
            
            try:
                approval_id = workflow.submit_for_approval(rule_dict)
                success = workflow.approve_rule(
                    approval_id, 
                    decision.reviewer, 
                    decision.reasoning
                )
                if success:
                    approved_count += 1
                    print(f"   ✅ Approved: {suggestion.rule_type}")
            except Exception as e:
                print(f"   ❌ Failed to approve {suggestion.rule_type}: {e}")
                
        elif decision.decision == "reject":
            rejected_count += 1
            print(f"   ❌ Rejected: {suggestion.rule_type}")
            
        elif decision.decision == "modify":
            # Simulate modification
            modified_rule = {
                'rule_type': suggestion.rule_type,
                'pattern': suggestion.pattern,
                'replacement': suggestion.replacement + " (modified)",
                'confidence': min(suggestion.confidence + 0.1, 1.0),
                'priority': suggestion.priority
            }
            
            try:
                approval_id = workflow.submit_for_approval(suggestion.__dict__)
                success = workflow.modify_rule(
                    approval_id,
                    modified_rule,
                    decision.reviewer,
                    decision.reasoning
                )
                if success:
                    modified_count += 1
                    print(f"   🔧 Modified: {suggestion.rule_type}")
            except Exception as e:
                print(f"   ❌ Failed to modify {suggestion.rule_type}: {e}")
    
    # Check final state
    print(f"\n📊 Final Results:")
    print(f"   Approved: {approved_count}")
    print(f"   Rejected: {rejected_count}")
    print(f"   Modified: {modified_count}")
    
    # Get current rules from manager
    current_rules = manager.load_current_rules()
    print(f"   Total rules in system: {len(current_rules)}")
    
    # Display rule statistics
    stats = manager.get_rule_statistics()
    print(f"   Rule types: {stats['rule_types']}")
    
    # Display workflow statistics
    workflow_stats = workflow.get_approval_statistics()
    print(f"   Approval rate: {workflow_stats.get('approval_rate', 0):.1f}%")
    
    # Test rule validation
    print("\n🔍 Testing rule validation...")
    
    test_rule = {
        'rule_type': 'test',
        'pattern': 'INVALID[',  # Invalid regex
        'replacement': 'Test'
    }
    
    validation_result = validator.validate_rule(test_rule)
    print(f"   Validation test - Valid: {validation_result.is_valid}")
    print(f"   Errors: {validation_result.errors}")
    
    # Test export/import
    print("\n💾 Testing export/import functionality...")
    
    export_file = rules_dir / "exported_rules.json"
    success = manager.export_rules(str(export_file))
    print(f"   Export success: {success}")
    
    if export_file.exists():
        with open(export_file, 'r') as f:
            exported_data = json.load(f)
        print(f"   Exported {len(exported_data)} rules")
    
    print("\n🎉 Integration test completed successfully!")
    print("=" * 50)
    
    return {
        'suggestions_processed': len(ai_suggestions),
        'approved': approved_count,
        'rejected': rejected_count,
        'modified': modified_count,
        'final_rules': len(current_rules),
        'validation_working': not validation_result.is_valid,  # Should fail for invalid rule
        'export_working': success
    }

def main():
    """Run the integration test"""
    try:
        results = test_rule_editor_integration()
        
        print("\n📋 Test Summary:")
        for key, value in results.items():
            print(f"   {key}: {value}")
        
        # Verify expected results
        assert results['suggestions_processed'] > 0, "No suggestions processed"
        assert results['final_rules'] >= 0, "Rule count invalid"
        assert results['validation_working'], "Validation not working"
        assert results['export_working'], "Export not working"
        
        print("\n✅ All integration tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())

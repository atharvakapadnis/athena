#!/usr/bin/env python3
"""
Demonstration script for the Rule Versioning System

This script demonstrates the key features of the rule versioning system:
1. Creating and managing rule versions
2. Detecting and resolving conflicts
3. Rolling back to previous versions
4. Integration with existing rule management

Usage:
    python scripts/demo_rule_versioning.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_versioning.integration import IntegratedRuleManager
from rule_versioning.version_manager import RuleVersionManager
from rule_versioning.conflict_resolver import RuleConflictResolver
try:
    from utils.logger import setup_logging
except ImportError:
    # Fallback if logger module not available
    def setup_logging(log_level=None):
        import logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def print_separator(title: str = ""):
    """Print a visual separator"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    else:
        print("-" * 60)

def print_json(data, title: str = ""):
    """Pretty print JSON data"""
    if title:
        print(f"\n{title}:")
    print(json.dumps(data, indent=2, default=str))

def demo_basic_versioning():
    """Demonstrate basic rule versioning functionality"""
    print_separator("BASIC RULE VERSIONING DEMO")
    
    # Initialize version manager
    version_manager = RuleVersionManager("data/rules")
    
    # Sample rule
    sample_rule = {
        'rule_type': 'company_standardization',
        'pattern': r'\b([A-Z]+)\s+(?:CO|COMPANY|CORP|CORPORATION)\b',
        'replacement': r'\1 Company',
        'confidence': 0.85,
        'priority': 3,
        'description': 'Standardize company suffixes'
    }
    
    print("Creating initial rule version...")
    
    # Create initial version
    version1_id = version_manager.create_version(
        rule_id="demo_company_rule",
        rule_content=sample_rule,
        author="demo_user",
        description="Initial company standardization rule",
        change_type="creation"
    )
    
    print(f"✓ Created version: {version1_id}")
    
    # Get and display the version
    version1 = version_manager.get_version("demo_company_rule", version1_id)
    print_json({
        'version_id': version1.version_id,
        'author': version1.author,
        'timestamp': version1.timestamp,
        'description': version1.change_description,
        'is_active': version1.is_active
    }, "Version 1 Details")
    
    print("\nUpdating rule with higher confidence...")
    
    # Create updated version
    updated_rule = sample_rule.copy()
    updated_rule['confidence'] = 0.92
    updated_rule['description'] = 'Improved company standardization rule'
    
    version2_id = version_manager.create_version(
        rule_id="demo_company_rule",
        rule_content=updated_rule,
        author="demo_user",
        description="Increased confidence after validation",
        change_type="modification"
    )
    
    print(f"✓ Created version: {version2_id}")
    
    # Show version history
    history = version_manager.get_version_history("demo_company_rule")
    print_json([{
        'version_id': v.version_id,
        'timestamp': v.timestamp,
        'author': v.author,
        'description': v.change_description,
        'confidence': v.rule_content.get('confidence'),
        'is_active': v.is_active
    } for v in history], "Complete Version History")
    
    print("\nTesting rollback functionality...")
    
    # Rollback to version 1
    rollback_success = version_manager.rollback_to_version(
        rule_id="demo_company_rule",
        target_version_id=version1_id,
        author="demo_admin",
        reason="Reverting confidence change for testing"
    )
    
    if rollback_success:
        print("✓ Rollback successful")
        current = version_manager.get_current_version("demo_company_rule")
        print(f"Current confidence: {current.rule_content['confidence']}")
        print(f"Change type: {current.change_type}")
    else:
        print("✗ Rollback failed")

def demo_conflict_detection():
    """Demonstrate conflict detection and resolution"""
    print_separator("CONFLICT DETECTION DEMO")
    
    resolver = RuleConflictResolver()
    
    # Define rules that will conflict
    rule1 = {
        'id': 'rule_1',
        'rule_type': 'company_standardization',
        'pattern': r'\b([A-Z]+)\s+COMPANY\b',
        'replacement': r'\1 Company',
        'confidence': 0.85,
        'priority': 3
    }
    
    rule2 = {
        'id': 'rule_2',
        'rule_type': 'company_standardization',
        'pattern': r'\b([A-Z]+)\s+COMPANY\b',  # Same pattern
        'replacement': r'\1 Corporation',        # Different replacement
        'confidence': 0.80,
        'priority': 3
    }
    
    rule3 = {
        'id': 'rule_3',
        'rule_type': 'company_standardization',
        'pattern': r'[invalid regex',  # Invalid regex
        'replacement': r'Test',
        'confidence': 0.75,
        'priority': 2
    }
    
    print("Detecting conflicts between rules...")
    
    # Detect conflicts
    existing_rules = [rule1]
    conflicts = resolver.detect_conflicts(rule2, existing_rules)
    
    print(f"Found {len(conflicts)} conflicts with rule2")
    for conflict in conflicts:
        print_json({
            'conflict_type': conflict.conflict_type.value,
            'severity': conflict.severity.value,
            'description': conflict.description,
            'auto_resolvable': conflict.auto_resolvable
        }, f"Conflict {conflict.conflict_id}")
    
    # Test with invalid regex
    conflicts_invalid = resolver.detect_conflicts(rule3, existing_rules)
    print(f"\nFound {len(conflicts_invalid)} conflicts with invalid regex rule")
    
    for conflict in conflicts_invalid:
        print_json({
            'conflict_type': conflict.conflict_type.value,
            'severity': conflict.severity.value,
            'description': conflict.description
        }, f"Invalid Regex Conflict")
    
    # Generate conflict report
    all_conflicts = conflicts + conflicts_invalid
    if all_conflicts:
        report = resolver.get_conflict_report(all_conflicts)
        print_json(report['summary'], "Conflict Report Summary")
        
        if report['recommendations']:
            print("\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")

def demo_integrated_management():
    """Demonstrate integrated rule management"""
    print_separator("INTEGRATED RULE MANAGEMENT DEMO")
    
    # Initialize integrated manager
    try:
        integrated_manager = IntegratedRuleManager("data/rules")
    except Exception as e:
        print(f"Note: Using simplified demo due to: {e}")
        return
    
    # Sample rule and decision
    new_rule = {
        'rule_type': 'unit_standardization',
        'pattern': r'\b(\d+)\s*(?:KG|KILOGRAMS?)\b',
        'replacement': r'\1 kg',
        'confidence': 0.92,
        'priority': 4,
        'description': 'Standardize kilogram units'
    }
    
    decision = {
        'reviewer': 'demo_reviewer',
        'reasoning': 'High confidence rule for unit standardization',
        'approved': True
    }
    
    print("Adding rule with integrated versioning...")
    
    # Add rule with versioning
    result = integrated_manager.add_rule_with_versioning(
        new_rule,
        decision,
        "demo_integration_user"
    )
    
    print_json({
        'success': result['success'],
        'rule_id': result.get('rule_id'),
        'version_id': result.get('version_id'),
        'conflicts_detected': len(result.get('conflicts', []))
    }, "Rule Addition Result")
    
    if result['success']:
        rule_id = result['rule_id']
        
        print(f"\nGetting rule history for {rule_id}...")
        history = integrated_manager.get_rule_history(rule_id)
        print_json(history, "Rule History")
        
        # Demonstrate update
        print("\nUpdating rule with versioning...")
        updated_rule = new_rule.copy()
        updated_rule['confidence'] = 0.95
        
        update_result = integrated_manager.update_rule_with_versioning(
            rule_id,
            updated_rule,
            "demo_updater",
            "Increased confidence after additional validation"
        )
        
        print_json({
            'success': update_result['success'],
            'version_id': update_result.get('version_id'),
            'conflicts_detected': len(update_result.get('conflicts', []))
        }, "Rule Update Result")

def demo_system_statistics():
    """Demonstrate system statistics and monitoring"""
    print_separator("SYSTEM STATISTICS DEMO")
    
    try:
        # Initialize managers
        version_manager = RuleVersionManager("data/rules")
        
        # Get comprehensive statistics
        version_stats = version_manager.get_version_statistics()
        storage_stats = version_manager.storage.get_storage_statistics()
        
        print_json(version_stats, "Version Management Statistics")
        print_json(storage_stats, "Storage Statistics")
        
        # Show recent activity
        if version_stats.get('recent_changes'):
            print("\nRecent Changes:")
            for change in version_stats['recent_changes'][:5]:
                print(f"  • {change['timestamp'][:19]} - {change['author']}: {change['description']}")
        
    except Exception as e:
        print(f"Statistics demo error: {e}")

def demo_migration():
    """Demonstrate migration capabilities"""
    print_separator("MIGRATION DEMO")
    
    try:
        integrated_manager = IntegratedRuleManager("data/rules")
        
        print("Checking system consistency...")
        stats = integrated_manager.get_system_statistics()
        
        if 'integration_health' in stats:
            health = stats['integration_health']
            print_json(health, "System Health Check")
        
        print("\nSimulating migration...")
        migration_results = integrated_manager.migrate_existing_rules()
        print_json(migration_results, "Migration Results")
        
    except Exception as e:
        print(f"Migration demo error: {e}")

def main():
    """Run the complete demonstration"""
    print("🚀 Rule Versioning System Demonstration")
    print("This demo showcases the key features of the rule versioning system.")
    
    # Setup logging
    setup_logging()
    
    try:
        # Run demonstrations
        demo_basic_versioning()
        demo_conflict_detection()
        demo_integrated_management()
        demo_system_statistics()
        demo_migration()
        
        print_separator("DEMO COMPLETE")
        print("✨ All demonstrations completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  ✓ Rule version creation and management")
        print("  ✓ Conflict detection and resolution")
        print("  ✓ Rollback capabilities")
        print("  ✓ Integrated rule management")
        print("  ✓ System statistics and monitoring")
        print("  ✓ Migration functionality")
        
        print("\nNext Steps:")
        print("  • Run the migration script to migrate existing rules")
        print("  • Use the integrated manager in your workflow")
        print("  • Monitor system health with statistics")
        print("  • Test rollback procedures")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

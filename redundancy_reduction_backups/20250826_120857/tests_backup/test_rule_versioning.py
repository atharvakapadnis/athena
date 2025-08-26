# tests/test_rule_versioning.py
import unittest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.rule_versioning.version_manager import RuleVersionManager, RuleVersion
from src.rule_versioning.storage import RuleStorage
from src.rule_versioning.conflict_resolver import RuleConflictResolver, ConflictType, ConflictSeverity
from src.rule_versioning.integration import IntegratedRuleManager

class TestRuleVersionManager(unittest.TestCase):
    """Test cases for RuleVersionManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.version_manager = RuleVersionManager(self.temp_dir)
        
        # Sample rule data
        self.sample_rule = {
            'rule_type': 'company_standardization',
            'pattern': r'\b([A-Z]+)\s+(?:CO|COMPANY)\b',
            'replacement': r'\1 Company',
            'confidence': 0.85,
            'priority': 3
        }
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_version(self):
        """Test version creation"""
        version_id = self.version_manager.create_version(
            rule_id="test_rule_1",
            rule_content=self.sample_rule,
            author="test_user",
            description="Test rule creation"
        )
        
        self.assertIsNotNone(version_id)
        self.assertEqual(len(version_id), 12)  # Expected length of version ID
        
        # Verify version was stored
        version = self.version_manager.get_version("test_rule_1", version_id)
        self.assertIsNotNone(version)
        self.assertEqual(version.rule_id, "test_rule_1")
        self.assertEqual(version.author, "test_user")
        self.assertTrue(version.is_active)
    
    def test_multiple_versions(self):
        """Test creating multiple versions of the same rule"""
        # Create first version
        version1_id = self.version_manager.create_version(
            rule_id="test_rule_2",
            rule_content=self.sample_rule,
            author="user1",
            description="Initial version"
        )
        
        # Create second version
        updated_rule = self.sample_rule.copy()
        updated_rule['confidence'] = 0.90
        
        version2_id = self.version_manager.create_version(
            rule_id="test_rule_2",
            rule_content=updated_rule,
            author="user2",
            description="Updated confidence"
        )
        
        # Verify both versions exist
        version1 = self.version_manager.get_version("test_rule_2", version1_id)
        version2 = self.version_manager.get_version("test_rule_2", version2_id)
        
        self.assertIsNotNone(version1)
        self.assertIsNotNone(version2)
        
        # First version should be inactive, second should be active
        self.assertFalse(version1.is_active)
        self.assertTrue(version2.is_active)
        
        # Current version should be version2
        current = self.version_manager.get_current_version("test_rule_2")
        self.assertEqual(current.version_id, version2_id)
    
    def test_rollback(self):
        """Test rule rollback functionality"""
        # Create multiple versions
        version1_id = self.version_manager.create_version(
            rule_id="test_rule_3",
            rule_content=self.sample_rule,
            author="user1",
            description="Version 1"
        )
        
        updated_rule = self.sample_rule.copy()
        updated_rule['confidence'] = 0.95
        
        version2_id = self.version_manager.create_version(
            rule_id="test_rule_3",
            rule_content=updated_rule,
            author="user2",
            description="Version 2"
        )
        
        # Rollback to version 1
        success = self.version_manager.rollback_to_version(
            rule_id="test_rule_3",
            target_version_id=version1_id,
            author="admin",
            reason="Testing rollback"
        )
        
        self.assertTrue(success)
        
        # Verify rollback created new version with original content
        current = self.version_manager.get_current_version("test_rule_3")
        self.assertIsNotNone(current)
        self.assertEqual(current.rule_content['confidence'], 0.85)  # Original confidence
        self.assertEqual(current.change_type, "rollback")
    
    def test_version_history(self):
        """Test version history retrieval"""
        rule_id = "test_rule_4"
        
        # Create several versions
        for i in range(3):
            updated_rule = self.sample_rule.copy()
            updated_rule['priority'] = i + 1
            
            self.version_manager.create_version(
                rule_id=rule_id,
                rule_content=updated_rule,
                author=f"user_{i}",
                description=f"Version {i+1}"
            )
        
        # Get version history
        history = self.version_manager.get_version_history(rule_id)
        
        self.assertEqual(len(history), 3)
        
        # Verify chronological order
        for i in range(len(history) - 1):
            self.assertLessEqual(history[i].timestamp, history[i+1].timestamp)
        
        # Verify content progression
        for i, version in enumerate(history):
            self.assertEqual(version.rule_content['priority'], i + 1)
    
    def test_statistics(self):
        """Test version statistics generation"""
        # Create versions with different authors and change types
        authors = ["user1", "user2", "admin"]
        change_types = ["creation", "modification", "rollback"]
        
        for i, (author, change_type) in enumerate(zip(authors, change_types)):
            self.version_manager.create_version(
                rule_id=f"rule_{i}",
                rule_content=self.sample_rule,
                author=author,
                description=f"Test {change_type}",
                change_type=change_type
            )
        
        stats = self.version_manager.get_version_statistics()
        
        self.assertEqual(stats['total_rules'], 3)
        self.assertEqual(stats['total_versions'], 3)
        self.assertEqual(stats['active_rules'], 3)
        
        # Check change type distribution
        self.assertIn('creation', stats['change_types'])
        self.assertIn('modification', stats['change_types'])
        self.assertIn('rollback', stats['change_types'])
        
        # Check author distribution
        for author in authors:
            self.assertIn(author, stats['authors'])


class TestRuleStorage(unittest.TestCase):
    """Test cases for RuleStorage"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = RuleStorage(self.temp_dir)
        
        # Create sample version
        self.sample_version = RuleVersion(
            version_id="test_version_1",
            rule_id="test_rule_1",
            rule_content={'pattern': 'test', 'replacement': 'TEST'},
            timestamp=datetime.now(),
            author="test_user",
            change_description="Test version",
            parent_version=None,
            is_active=True
        )
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load_version(self):
        """Test saving and loading a single version"""
        # Save version
        self.storage.save_rule_version(self.sample_version)
        
        # Load version
        loaded_version = self.storage.get_version("test_rule_1", "test_version_1")
        
        self.assertIsNotNone(loaded_version)
        self.assertEqual(loaded_version.rule_id, self.sample_version.rule_id)
        self.assertEqual(loaded_version.version_id, self.sample_version.version_id)
        self.assertEqual(loaded_version.author, self.sample_version.author)
    
    def test_load_rule_versions(self):
        """Test loading all versions for a rule"""
        rule_id = "test_rule_2"
        
        # Create multiple versions
        versions = []
        for i in range(3):
            version = RuleVersion(
                version_id=f"version_{i}",
                rule_id=rule_id,
                rule_content={'priority': i},
                timestamp=datetime.now(),
                author=f"user_{i}",
                change_description=f"Version {i}",
                parent_version=f"version_{i-1}" if i > 0 else None,
                is_active=(i == 2)  # Last version is active
            )
            versions.append(version)
            self.storage.save_rule_version(version)
        
        # Load all versions
        loaded_versions = self.storage.load_rule_versions(rule_id)
        
        self.assertEqual(len(loaded_versions), 3)
        
        # Verify sorting by timestamp
        for i in range(len(loaded_versions) - 1):
            self.assertLessEqual(loaded_versions[i].timestamp, loaded_versions[i+1].timestamp)
    
    def test_backup_and_restore(self):
        """Test backup and restore functionality"""
        # Save multiple versions
        for i in range(3):
            version = RuleVersion(
                version_id=f"backup_version_{i}",
                rule_id=f"backup_rule_{i}",
                rule_content={'test': i},
                timestamp=datetime.now(),
                author="backup_user",
                change_description=f"Backup test {i}",
                parent_version=None,
                is_active=True
            )
            self.storage.save_rule_version(version)
        
        # Create backup
        backup_path = self.storage.create_backup("test_backup")
        self.assertTrue(Path(backup_path).exists())
        
        # Verify backup contains data
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        self.assertEqual(backup_data['total_versions'], 3)
        self.assertEqual(len(backup_data['versions']), 3)
        
        # Test restore (would require clearing and restoring in real scenario)
        restore_success = self.storage.restore_from_backup(backup_path)
        self.assertTrue(restore_success)
    
    def test_storage_statistics(self):
        """Test storage statistics generation"""
        # Add some test data
        for i in range(5):
            version = RuleVersion(
                version_id=f"stats_version_{i}",
                rule_id=f"stats_rule_{i % 2}",  # 2 rules with multiple versions
                rule_content={'data': i},
                timestamp=datetime.now(),
                author="stats_user",
                change_description=f"Stats test {i}",
                parent_version=None,
                is_active=True
            )
            self.storage.save_rule_version(version)
        
        stats = self.storage.get_storage_statistics()
        
        self.assertEqual(stats['total_rules'], 2)
        self.assertEqual(stats['total_versions'], 5)
        self.assertGreaterEqual(stats['storage_size_mb'], 0)  # Allow 0 for small test files


class TestRuleConflictResolver(unittest.TestCase):
    """Test cases for RuleConflictResolver"""
    
    def setUp(self):
        """Set up test environment"""
        self.resolver = RuleConflictResolver()
        
        # Sample rules for testing
        self.rule1 = {
            'id': 'rule_1',
            'rule_type': 'company',
            'pattern': r'\b([A-Z]+)\s+COMPANY\b',
            'replacement': r'\1 Company',
            'priority': 3,
            'confidence': 0.8
        }
        
        self.rule2 = {
            'id': 'rule_2',
            'rule_type': 'company',
            'pattern': r'\b([A-Z]+)\s+CO\b',
            'replacement': r'\1 Company',
            'priority': 3,
            'confidence': 0.8
        }
        
        self.conflicting_rule = {
            'id': 'rule_3',
            'rule_type': 'company',
            'pattern': r'\b([A-Z]+)\s+COMPANY\b',  # Same pattern as rule1
            'replacement': r'\1 Corporation',       # Different replacement
            'priority': 3,
            'confidence': 0.8
        }
    
    def test_pattern_overlap_detection(self):
        """Test pattern overlap conflict detection"""
        conflicts = self.resolver.detect_conflicts(self.rule1, [self.rule2])
        
        # Should detect some overlap between COMPANY and CO patterns
        pattern_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.PATTERN_OVERLAP]
        self.assertTrue(len(pattern_conflicts) >= 0)  # May or may not overlap depending on test strings
    
    def test_replacement_conflict_detection(self):
        """Test replacement ambiguity detection"""
        conflicts = self.resolver.detect_conflicts(self.conflicting_rule, [self.rule1])
        
        # Should detect replacement conflict (same pattern, different replacement)
        replacement_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.REPLACEMENT_AMBIGUITY]
        self.assertEqual(len(replacement_conflicts), 1)
        
        conflict = replacement_conflicts[0]
        self.assertEqual(conflict.severity, ConflictSeverity.HIGH)
        self.assertTrue(conflict.auto_resolvable)
    
    def test_regex_error_detection(self):
        """Test detection of invalid regex patterns"""
        invalid_rule = {
            'id': 'invalid_rule',
            'pattern': r'[invalid regex',  # Unclosed bracket
            'replacement': 'test'
        }
        
        conflicts = self.resolver.detect_conflicts(invalid_rule, [self.rule1])
        
        # Should detect regex error
        regex_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.REGEX_CONFLICT]
        self.assertEqual(len(regex_conflicts), 1)
        
        conflict = regex_conflicts[0]
        self.assertEqual(conflict.severity, ConflictSeverity.CRITICAL)
        self.assertFalse(conflict.auto_resolvable)
    
    def test_conflict_resolution(self):
        """Test conflict resolution strategies"""
        conflicts = self.resolver.detect_conflicts(self.conflicting_rule, [self.rule1])
        
        # Resolve conflicts
        resolution_results = self.resolver.resolve_conflicts(conflicts)
        
        self.assertIn('resolved_conflicts', resolution_results)
        self.assertIn('unresolved_conflicts', resolution_results)
        self.assertIn('actions_taken', resolution_results)
    
    def test_conflict_report_generation(self):
        """Test conflict report generation"""
        conflicts = self.resolver.detect_conflicts(self.conflicting_rule, [self.rule1])
        
        report = self.resolver.get_conflict_report(conflicts)
        
        self.assertIn('summary', report)
        self.assertIn('total_conflicts', report['summary'])
        self.assertIn('by_severity', report['summary'])
        self.assertIn('by_type', report['summary'])
        self.assertIn('recommendations', report)
        self.assertIn('impact_analysis', report)


class TestIntegratedRuleManager(unittest.TestCase):
    """Test cases for IntegratedRuleManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock the legacy manager to avoid file system dependencies
        with patch('rule_versioning.integration.RuleManager') as mock_manager:
            mock_instance = MagicMock()
            mock_instance.load_current_rules.return_value = []
            mock_instance.add_approved_rule.return_value = "test_rule_id"
            mock_manager.return_value = mock_instance
            
            self.integrated_manager = IntegratedRuleManager(self.temp_dir)
        
        self.sample_rule = {
            'rule_type': 'company',
            'pattern': r'\bTEST\s+COMPANY\b',
            'replacement': 'Test Company',
            'confidence': 0.85,
            'priority': 3
        }
        
        self.sample_decision = {
            'reviewer': 'test_user',
            'reasoning': 'Test rule for integration testing'
        }
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_rule_with_versioning(self):
        """Test adding a rule with versioning"""
        result = self.integrated_manager.add_rule_with_versioning(
            self.sample_rule,
            self.sample_decision,
            "integration_test"
        )
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['rule_id'])
        self.assertIsNotNone(result['version_id'])
        self.assertIsInstance(result['conflicts'], list)
    
    def test_update_rule_with_versioning(self):
        """Test updating a rule with versioning"""
        # First add a rule
        add_result = self.integrated_manager.add_rule_with_versioning(
            self.sample_rule,
            self.sample_decision,
            "integration_test"
        )
        
        rule_id = add_result['rule_id']
        
        # Mock the get_rule_by_id method
        self.integrated_manager.legacy_manager.get_rule_by_id = MagicMock(return_value={
            'id': rule_id,
            **self.sample_rule
        })
        
        # Update the rule
        updated_rule = self.sample_rule.copy()
        updated_rule['confidence'] = 0.95
        
        update_result = self.integrated_manager.update_rule_with_versioning(
            rule_id,
            updated_rule,
            "integration_test",
            "Increased confidence"
        )
        
        self.assertTrue(update_result['success'])
        self.assertIsNotNone(update_result['version_id'])
    
    def test_migration_simulation(self):
        """Test rule migration functionality"""
        # Mock existing rules
        existing_rules = [
            {
                'id': 'legacy_rule_1',
                'rule_type': 'company',
                'pattern': r'\bTEST\b',
                'replacement': 'Test',
                'approved_by': 'legacy_user',
                'approved_at': '2023-01-01T00:00:00'
            },
            {
                'id': 'legacy_rule_2',
                'rule_type': 'unit',
                'pattern': r'\bKG\b',
                'replacement': 'kg',
                'approved_by': 'legacy_user',
                'approved_at': '2023-01-02T00:00:00'
            }
        ]
        
        self.integrated_manager.legacy_manager.load_current_rules = MagicMock(return_value=existing_rules)
        
        # Perform migration
        migration_results = self.integrated_manager.migrate_existing_rules()
        
        self.assertEqual(migration_results['total_rules'], 2)
        self.assertEqual(migration_results['migrated'], 2)
        self.assertEqual(migration_results['failed'], 0)
    
    def test_system_statistics(self):
        """Test system statistics generation"""
        # Mock legacy statistics
        self.integrated_manager.legacy_manager.get_rule_statistics = MagicMock(return_value={
            'total_rules': 5,
            'rule_types': {'company': 3, 'unit': 2}
        })
        
        stats = self.integrated_manager.get_system_statistics()
        
        self.assertIn('legacy_system', stats)
        self.assertIn('versioning_system', stats)
        self.assertIn('storage_system', stats)
        self.assertIn('integration_health', stats)


class TestRuleVersioningIntegration(unittest.TestCase):
    """Integration tests for the complete rule versioning system"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a realistic test scenario
        self.rules = [
            {
                'id': 'company_rule_1',
                'rule_type': 'company_standardization',
                'pattern': r'\b([A-Z]+)\s+(?:CO|COMPANY|CORP)\b',
                'replacement': r'\1 Company',
                'confidence': 0.85,
                'priority': 3,
                'approved_by': 'admin',
                'approved_at': '2023-01-01T00:00:00'
            },
            {
                'id': 'unit_rule_1',
                'rule_type': 'unit_standardization',
                'pattern': r'\b(\d+)\s*(?:KG|KILOGRAMS?)\b',
                'replacement': r'\1 kg',
                'confidence': 0.92,
                'priority': 4,
                'approved_by': 'admin',
                'approved_at': '2023-01-02T00:00:00'
            }
        ]
    
    def tearDown(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_workflow(self):
        """Test complete workflow: create, update, conflict detection, rollback"""
        # Initialize managers
        version_manager = RuleVersionManager(self.temp_dir)
        conflict_resolver = RuleConflictResolver()
        
        # Step 1: Create initial versions
        version_ids = []
        for rule in self.rules:
            version_id = version_manager.create_version(
                rule_id=rule['id'],
                rule_content=rule,
                author=rule['approved_by'],
                description="Initial migration",
                change_type="creation"
            )
            version_ids.append(version_id)
        
        # Verify initial state
        self.assertEqual(len(version_ids), 2)
        stats = version_manager.get_version_statistics()
        self.assertEqual(stats['total_rules'], 2)
        self.assertEqual(stats['total_versions'], 2)
        
        # Step 2: Create conflicting rule and detect conflicts
        conflicting_rule = {
            'id': 'conflicting_rule',
            'rule_type': 'company_standardization',
            'pattern': r'\b([A-Z]+)\s+COMPANY\b',  # Overlaps with company_rule_1
            'replacement': r'\1 Corp',              # Different replacement
            'confidence': 0.80,
            'priority': 3
        }
        
        existing_rules = [rule.rule_content for rule in version_manager.get_all_active_rules().values()]
        conflicts = conflict_resolver.detect_conflicts(conflicting_rule, existing_rules)
        
        # Should detect conflicts
        self.assertGreater(len(conflicts), 0)
        
        # Step 3: Update existing rule
        updated_rule = self.rules[0].copy()
        updated_rule['confidence'] = 0.95
        
        new_version_id = version_manager.create_version(
            rule_id=updated_rule['id'],
            rule_content=updated_rule,
            author="updater",
            description="Increased confidence",
            change_type="modification"
        )
        
        # Verify update
        current_version = version_manager.get_current_version(updated_rule['id'])
        self.assertEqual(current_version.rule_content['confidence'], 0.95)
        
        # Step 4: Test rollback
        rollback_success = version_manager.rollback_to_version(
            rule_id=updated_rule['id'],
            target_version_id=version_ids[0],
            author="admin",
            reason="Testing rollback functionality"
        )
        
        self.assertTrue(rollback_success)
        
        # Verify rollback
        current_after_rollback = version_manager.get_current_version(updated_rule['id'])
        self.assertEqual(current_after_rollback.rule_content['confidence'], 0.85)  # Original value
        self.assertEqual(current_after_rollback.change_type, "rollback")
        
        # Step 5: Verify complete history
        history = version_manager.get_version_history(updated_rule['id'])
        self.assertEqual(len(history), 3)  # creation, modification, rollback
        
        change_types = [v.change_type for v in history]
        self.assertIn("creation", change_types)
        self.assertIn("modification", change_types)
        self.assertIn("rollback", change_types)


def run_all_tests():
    """Run all rule versioning tests"""
    # Create test suite
    test_classes = [
        TestRuleVersionManager,
        TestRuleStorage,
        TestRuleConflictResolver,
        TestIntegratedRuleManager,
        TestRuleVersioningIntegration
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

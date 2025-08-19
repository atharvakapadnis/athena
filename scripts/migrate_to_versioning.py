#!/usr/bin/env python3
"""
Migration script to transition existing rules to the new versioning system.

This script:
1. Backs up existing rules
2. Migrates rules to the new versioning system
3. Validates the migration
4. Provides rollback capability if needed

Usage:
    python scripts/migrate_to_versioning.py [--dry-run] [--backup-name NAME]
"""

import sys
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rule_versioning.integration import IntegratedRuleManager
from rule_versioning.version_manager import RuleVersionManager
from rule_editor.manager import RuleManager
try:
    from utils.logger import setup_logging
except ImportError:
    # Fallback if logger module not available
    def setup_logging(log_level=None):
        import logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

class RuleMigrator:
    """Handles migration of rules from legacy system to versioning system"""
    
    def __init__(self, rules_dir: str = "data/rules", dry_run: bool = False):
        self.rules_dir = Path(rules_dir)
        self.dry_run = dry_run
        
        if not dry_run:
            self.integrated_manager = IntegratedRuleManager(str(self.rules_dir))
            self.legacy_manager = self.integrated_manager.legacy_manager
            self.version_manager = self.integrated_manager.version_manager
        else:
            # For dry run, only need read access
            self.legacy_manager = RuleManager(self.rules_dir)
        
        self.migration_log = []
    
    def migrate_all_rules(self, backup_name: str = None) -> Dict:
        """
        Perform complete migration of all rules
        
        Args:
            backup_name: Optional name for backup
            
        Returns:
            Migration results
        """
        logger.info(f"Starting rule migration {'(DRY RUN)' if self.dry_run else ''}")
        
        results = {
            'backup_created': False,
            'backup_path': '',
            'migration_results': {},
            'validation_results': {},
            'success': False,
            'errors': []
        }
        
        try:
            # Step 1: Create backup
            if not self.dry_run:
                results['backup_path'] = self._create_comprehensive_backup(backup_name)
                results['backup_created'] = True
                logger.info(f"Created backup: {results['backup_path']}")
            else:
                logger.info("DRY RUN: Would create backup")
                results['backup_created'] = True
            
            # Step 2: Analyze current state
            analysis = self._analyze_current_state()
            logger.info(f"Current state: {analysis['summary']}")
            
            # Step 3: Perform migration
            if not self.dry_run:
                results['migration_results'] = self.integrated_manager.migrate_existing_rules()
            else:
                results['migration_results'] = self._simulate_migration()
            
            logger.info(f"Migration results: {results['migration_results']}")
            
            # Step 4: Validate migration
            if not self.dry_run:
                results['validation_results'] = self._validate_migration()
            else:
                results['validation_results'] = {'status': 'simulated', 'valid': True}
            
            logger.info(f"Validation results: {results['validation_results']}")
            
            # Step 5: Check success
            migration_success = results['migration_results'].get('failed', 1) == 0
            validation_success = results['validation_results'].get('valid', False)
            
            results['success'] = migration_success and validation_success
            
            if results['success']:
                logger.info("Migration completed successfully!")
            else:
                logger.warning("Migration completed with issues")
            
        except Exception as e:
            logger.error(f"Error during migration: {e}")
            results['errors'].append(str(e))
            results['success'] = False
        
        return results
    
    def rollback_migration(self, backup_path: str) -> bool:
        """
        Rollback migration using a backup
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if rollback successful
        """
        if self.dry_run:
            logger.info("DRY RUN: Would rollback migration")
            return True
        
        try:
            logger.info(f"Rolling back migration using backup: {backup_path}")
            
            # Restore legacy system
            success = self.legacy_manager.restore_from_backup(backup_path)
            if not success:
                logger.error("Failed to restore legacy system from backup")
                return False
            
            # Clear versioning system (optional - keep for audit trail)
            # In production, you might want to mark versions as 'rolled_back'
            # rather than deleting them
            
            logger.info("Migration rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            return False
    
    def _create_comprehensive_backup(self, backup_name: str = None) -> str:
        """Create comprehensive backup of all rule data"""
        if backup_name is None:
            backup_name = f"pre_migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create backup using legacy manager
        backup_path = self.legacy_manager.create_backup(backup_name)
        
        # Also backup any existing version data
        version_backup_path = self.version_manager.storage.create_backup(f"version_{backup_name}")
        
        self.migration_log.append(f"Created backups: {backup_path}, {version_backup_path}")
        return backup_path
    
    def _analyze_current_state(self) -> Dict:
        """Analyze current state of rule system"""
        try:
            current_rules = self.legacy_manager.load_current_rules()
            
            # Get existing version data if any
            existing_versions = []
            if not self.dry_run:
                try:
                    existing_versions = self.version_manager.storage.load_all_versions()
                except Exception:
                    pass  # No existing versions is fine
            
            analysis = {
                'total_legacy_rules': len(current_rules),
                'existing_versions': len(existing_versions),
                'rule_types': {},
                'authors': {},
                'date_range': {},
                'summary': ''
            }
            
            # Analyze rule types
            for rule in current_rules:
                rule_type = rule.get('rule_type', 'unknown')
                analysis['rule_types'][rule_type] = analysis['rule_types'].get(rule_type, 0) + 1
                
                author = rule.get('approved_by', 'unknown')
                analysis['authors'][author] = analysis['authors'].get(author, 0) + 1
            
            # Determine date range
            dates = [rule.get('approved_at') for rule in current_rules if rule.get('approved_at')]
            if dates:
                analysis['date_range'] = {
                    'earliest': min(dates),
                    'latest': max(dates)
                }
            
            analysis['summary'] = (f"{analysis['total_legacy_rules']} rules, "
                                 f"{len(analysis['rule_types'])} types, "
                                 f"{analysis['existing_versions']} existing versions")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing current state: {e}")
            return {'error': str(e)}
    
    def _simulate_migration(self) -> Dict:
        """Simulate migration for dry run"""
        try:
            current_rules = self.legacy_manager.load_current_rules()
            
            return {
                'total_rules': len(current_rules),
                'migrated': len(current_rules),  # All would be migrated
                'failed': 0,
                'errors': [],
                'simulated': True
            }
            
        except Exception as e:
            return {
                'total_rules': 0,
                'migrated': 0,
                'failed': 0,
                'errors': [str(e)],
                'simulated': True
            }
    
    def _validate_migration(self) -> Dict:
        """Validate that migration was successful"""
        try:
            # Get rules from both systems
            legacy_rules = self.legacy_manager.load_current_rules()
            active_versions = self.version_manager.get_all_active_rules()
            
            validation = {
                'legacy_count': len(legacy_rules),
                'version_count': len(active_versions),
                'matched_rules': 0,
                'mismatched_rules': [],
                'missing_versions': [],
                'extra_versions': [],
                'valid': False
            }
            
            legacy_ids = set(rule.get('id') for rule in legacy_rules if rule.get('id'))
            version_ids = set(active_versions.keys())
            
            # Check for matches
            validation['matched_rules'] = len(legacy_ids & version_ids)
            validation['missing_versions'] = list(legacy_ids - version_ids)
            validation['extra_versions'] = list(version_ids - legacy_ids)
            
            # Content validation for matched rules
            content_matches = 0
            for rule in legacy_rules:
                rule_id = rule.get('id')
                if rule_id in active_versions:
                    version_content = active_versions[rule_id].rule_content
                    
                    # Compare key fields
                    key_fields = ['pattern', 'replacement', 'rule_type', 'priority']
                    fields_match = all(
                        rule.get(field) == version_content.get(field)
                        for field in key_fields
                    )
                    
                    if fields_match:
                        content_matches += 1
                    else:
                        validation['mismatched_rules'].append(rule_id)
            
            # Migration is valid if all rules have versions and content matches
            validation['valid'] = (
                len(validation['missing_versions']) == 0 and
                len(validation['mismatched_rules']) == 0 and
                validation['matched_rules'] == validation['legacy_count']
            )
            
            return validation
            
        except Exception as e:
            logger.error(f"Error validating migration: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def generate_migration_report(self, results: Dict) -> str:
        """Generate a comprehensive migration report"""
        report = []
        report.append("=" * 60)
        report.append("RULE VERSIONING MIGRATION REPORT")
        report.append("=" * 60)
        report.append(f"Migration Time: {datetime.now().isoformat()}")
        report.append(f"Dry Run: {'Yes' if self.dry_run else 'No'}")
        report.append(f"Success: {'Yes' if results.get('success') else 'No'}")
        report.append("")
        
        # Backup information
        if results.get('backup_created'):
            report.append("BACKUP INFORMATION")
            report.append("-" * 20)
            report.append(f"Backup Created: Yes")
            report.append(f"Backup Path: {results.get('backup_path', 'N/A')}")
            report.append("")
        
        # Migration results
        migration_results = results.get('migration_results', {})
        report.append("MIGRATION RESULTS")
        report.append("-" * 20)
        report.append(f"Total Rules: {migration_results.get('total_rules', 0)}")
        report.append(f"Successfully Migrated: {migration_results.get('migrated', 0)}")
        report.append(f"Failed: {migration_results.get('failed', 0)}")
        
        if migration_results.get('errors'):
            report.append("\nMigration Errors:")
            for error in migration_results['errors']:
                report.append(f"  - {error}")
        report.append("")
        
        # Validation results
        validation_results = results.get('validation_results', {})
        report.append("VALIDATION RESULTS")
        report.append("-" * 20)
        report.append(f"Validation Status: {'PASSED' if validation_results.get('valid') else 'FAILED'}")
        
        if not self.dry_run and validation_results.get('legacy_count') is not None:
            report.append(f"Legacy Rules: {validation_results['legacy_count']}")
            report.append(f"Versioned Rules: {validation_results['version_count']}")
            report.append(f"Matched Rules: {validation_results['matched_rules']}")
            
            if validation_results.get('missing_versions'):
                report.append(f"\nMissing Versions ({len(validation_results['missing_versions'])}):")
                for rule_id in validation_results['missing_versions']:
                    report.append(f"  - {rule_id}")
            
            if validation_results.get('mismatched_rules'):
                report.append(f"\nContent Mismatches ({len(validation_results['mismatched_rules'])}):")
                for rule_id in validation_results['mismatched_rules']:
                    report.append(f"  - {rule_id}")
        
        # Migration log
        if self.migration_log:
            report.append("\nMIGRATION LOG")
            report.append("-" * 20)
            for log_entry in self.migration_log:
                report.append(f"  {log_entry}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)


def main():
    """Main migration script entry point"""
    parser = argparse.ArgumentParser(description="Migrate rules to versioning system")
    parser.add_argument('--dry-run', action='store_true', 
                       help="Perform a dry run without making changes")
    parser.add_argument('--backup-name', type=str,
                       help="Custom name for backup (optional)")
    parser.add_argument('--rollback', type=str,
                       help="Rollback using specified backup file")
    parser.add_argument('--verbose', '-v', action='store_true',
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)
    
    try:
        migrator = RuleMigrator(dry_run=args.dry_run)
        
        if args.rollback:
            # Perform rollback
            success = migrator.rollback_migration(args.rollback)
            if success:
                print("Rollback completed successfully")
                sys.exit(0)
            else:
                print("Rollback failed")
                sys.exit(1)
        else:
            # Perform migration
            results = migrator.migrate_all_rules(args.backup_name)
            
            # Generate and display report
            report = migrator.generate_migration_report(results)
            print(report)
            
            # Save report to file
            report_file = Path("data/logs") / f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            report_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(report_file, 'w') as f:
                f.write(report)
            
            print(f"\nDetailed report saved to: {report_file}")
            
            # Exit with appropriate code
            sys.exit(0 if results.get('success') else 1)
    
    except KeyboardInterrupt:
        print("\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Migration failed with error: {e}")
        print(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

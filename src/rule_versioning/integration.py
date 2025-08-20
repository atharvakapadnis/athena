# src/rule_versioning/integration.py
"""
Integration layer between the new rule versioning system and existing rule_editor
"""

import logging
from typing import Dict, List, Optional
from pathlib import Path

from .version_manager import RuleVersionManager, RuleVersion
from .conflict_resolver import RuleConflictResolver
try:
    from ..rule_editor.manager import RuleManager
except ImportError:
    try:
        from rule_editor.manager import RuleManager
    except ImportError:
        from src.rule_editor.manager import RuleManager

logger = logging.getLogger(__name__)

class IntegratedRuleManager:
    """
    Enhanced rule manager that combines existing functionality with 
    comprehensive versioning and conflict resolution
    """
    
    def __init__(self, rules_dir: str = "data/rules"):
        self.rules_dir = Path(rules_dir)
        
        # Initialize components
        self.legacy_manager = RuleManager(self.rules_dir)
        self.version_manager = RuleVersionManager(str(self.rules_dir))
        self.conflict_resolver = RuleConflictResolver()
        
        logger.info("Initialized integrated rule manager with versioning support")
    
    def add_rule_with_versioning(self, rule: Dict, decision: Dict, 
                                author: str = "system") -> Dict:
        """
        Add a rule with full versioning and conflict detection
        
        Args:
            rule: Rule data to add
            decision: Decision metadata from approval process
            author: Who is adding the rule
            
        Returns:
            Dictionary with rule_id, version_id, and any conflicts detected
        """
        try:
            # Get existing rules for conflict detection
            existing_rules = self.legacy_manager.load_current_rules()
            
            # Detect conflicts
            conflicts = self.conflict_resolver.detect_conflicts(rule, existing_rules)
            
            result = {
                'rule_id': None,
                'version_id': None,
                'conflicts': conflicts,
                'conflict_report': None,
                'success': False
            }
            
            # Generate conflict report
            if conflicts:
                result['conflict_report'] = self.conflict_resolver.get_conflict_report(conflicts)
                
                # Check for critical conflicts
                critical_conflicts = [c for c in conflicts if c.severity.value == 'critical']
                if critical_conflicts:
                    result['error'] = 'Critical conflicts detected - rule not added'
                    logger.warning(f"Critical conflicts prevented rule addition: {len(critical_conflicts)} conflicts")
                    return result
            
            # Add rule using legacy manager to maintain compatibility
            rule_id = self.legacy_manager.add_approved_rule(rule, decision)
            
            # Create version record
            version_description = f"Added new rule - {decision.get('reasoning', 'No reason provided')}"
            version_id = self.version_manager.create_version(
                rule_id=rule_id,
                rule_content=rule,
                author=author,
                description=version_description,
                change_type="creation"
            )
            
            result.update({
                'rule_id': rule_id,
                'version_id': version_id,
                'success': True
            })
            
            logger.info(f"Successfully added rule {rule_id} with version {version_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error adding rule with versioning: {e}")
            return {
                'rule_id': None,
                'version_id': None,
                'conflicts': [],
                'success': False,
                'error': str(e)
            }
    
    def update_rule_with_versioning(self, rule_id: str, updated_rule: Dict, 
                                   author: str, reason: str) -> Dict:
        """
        Update a rule with full versioning support
        
        Args:
            rule_id: ID of rule to update
            updated_rule: New rule data
            author: Who is making the update
            reason: Reason for the update
            
        Returns:
            Dictionary with version_id and any conflicts detected
        """
        try:
            # Get current rule
            current_rule = self.legacy_manager.get_rule_by_id(rule_id)
            if not current_rule:
                return {
                    'success': False,
                    'error': f'Rule {rule_id} not found'
                }
            
            # Get other existing rules for conflict detection
            existing_rules = [r for r in self.legacy_manager.load_current_rules() 
                            if r.get('id') != rule_id]
            
            # Detect conflicts
            conflicts = self.conflict_resolver.detect_conflicts(updated_rule, existing_rules)
            
            result = {
                'version_id': None,
                'conflicts': conflicts,
                'conflict_report': None,
                'success': False
            }
            
            # Generate conflict report
            if conflicts:
                result['conflict_report'] = self.conflict_resolver.get_conflict_report(conflicts)
                
                # Check for critical conflicts
                critical_conflicts = [c for c in conflicts if c.severity.value == 'critical']
                if critical_conflicts:
                    result['error'] = 'Critical conflicts detected - rule not updated'
                    logger.warning(f"Critical conflicts prevented rule update: {len(critical_conflicts)} conflicts")
                    return result
            
            # Update rule using legacy manager
            success = self.legacy_manager.update_rule(rule_id, updated_rule)
            if not success:
                result['error'] = 'Failed to update rule in legacy system'
                return result
            
            # Create version record
            version_description = f"Updated rule - {reason}"
            version_id = self.version_manager.create_version(
                rule_id=rule_id,
                rule_content=updated_rule,
                author=author,
                description=version_description,
                change_type="modification"
            )
            
            result.update({
                'version_id': version_id,
                'success': True
            })
            
            logger.info(f"Successfully updated rule {rule_id} with version {version_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error updating rule {rule_id} with versioning: {e}")
            return {
                'version_id': None,
                'conflicts': [],
                'success': False,
                'error': str(e)
            }
    
    def rollback_rule(self, rule_id: str, target_version_id: str, 
                     author: str, reason: str) -> Dict:
        """
        Rollback a rule to a previous version
        
        Args:
            rule_id: ID of rule to rollback
            target_version_id: Version to rollback to
            author: Who initiated the rollback
            reason: Reason for rollback
            
        Returns:
            Dictionary with rollback results
        """
        try:
            # Get target version
            target_version = self.version_manager.get_version(rule_id, target_version_id)
            if not target_version:
                return {
                    'success': False,
                    'error': f'Target version {target_version_id} not found'
                }
            
            # Perform rollback in version manager
            rollback_success = self.version_manager.rollback_to_version(
                rule_id, target_version_id, author, reason
            )
            
            if not rollback_success:
                return {
                    'success': False,
                    'error': 'Failed to rollback in version manager'
                }
            
            # Update legacy manager with rolled-back content
            update_success = self.legacy_manager.update_rule(rule_id, target_version.rule_content)
            
            if not update_success:
                return {
                    'success': False,
                    'error': 'Failed to update legacy system after rollback'
                }
            
            logger.info(f"Successfully rolled back rule {rule_id} to version {target_version_id}")
            return {
                'success': True,
                'rolled_back_to': target_version_id,
                'rule_content': target_version.rule_content
            }
            
        except Exception as e:
            logger.error(f"Error rolling back rule {rule_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_rule_history(self, rule_id: str) -> List[Dict]:
        """Get complete version history for a rule"""
        try:
            versions = self.version_manager.get_version_history(rule_id)
            return [
                {
                    'version_id': v.version_id,
                    'timestamp': v.timestamp.isoformat(),
                    'author': v.author,
                    'change_description': v.change_description,
                    'change_type': v.change_type,
                    'is_active': v.is_active,
                    'impact_score': v.impact_score
                }
                for v in versions
            ]
        except Exception as e:
            logger.error(f"Error getting rule history for {rule_id}: {e}")
            return []
    
    def get_system_statistics(self) -> Dict:
        """Get comprehensive system statistics"""
        try:
            legacy_stats = self.legacy_manager.get_rule_statistics()
            version_stats = self.version_manager.get_version_statistics()
            storage_stats = self.version_manager.storage.get_storage_statistics()
            
            return {
                'legacy_system': legacy_stats,
                'versioning_system': version_stats,
                'storage_system': storage_stats,
                'integration_health': {
                    'rules_in_both_systems': self._check_system_consistency(),
                    'last_check': logger.name  # Placeholder for timestamp
                }
            }
        except Exception as e:
            logger.error(f"Error getting system statistics: {e}")
            return {}
    
    def migrate_existing_rules(self) -> Dict:
        """
        Migrate existing rules from legacy system to versioning system
        
        Returns:
            Migration results with success/failure counts
        """
        try:
            existing_rules = self.legacy_manager.load_current_rules()
            
            migration_results = {
                'total_rules': len(existing_rules),
                'migrated': 0,
                'failed': 0,
                'errors': []
            }
            
            for rule in existing_rules:
                try:
                    # Create initial version for existing rule
                    rule_id = rule.get('id')
                    if not rule_id:
                        migration_results['failed'] += 1
                        migration_results['errors'].append('Rule missing ID')
                        continue
                    
                    # Check if already migrated
                    existing_version = self.version_manager.get_current_version(rule_id)
                    if existing_version:
                        logger.debug(f"Rule {rule_id} already has versions, skipping")
                        continue
                    
                    # Create initial version
                    version_id = self.version_manager.create_version(
                        rule_id=rule_id,
                        rule_content=rule,
                        author=rule.get('approved_by', 'migration_system'),
                        description=f"Migrated from legacy system - originally approved: {rule.get('approved_at', 'unknown')}",
                        change_type="migration"
                    )
                    
                    migration_results['migrated'] += 1
                    logger.debug(f"Migrated rule {rule_id} as version {version_id}")
                    
                except Exception as e:
                    migration_results['failed'] += 1
                    migration_results['errors'].append(f"Failed to migrate rule {rule.get('id', 'unknown')}: {e}")
                    logger.error(f"Error migrating rule: {e}")
            
            logger.info(f"Migration completed: {migration_results['migrated']} migrated, {migration_results['failed']} failed")
            return migration_results
            
        except Exception as e:
            logger.error(f"Error during rule migration: {e}")
            return {
                'total_rules': 0,
                'migrated': 0,
                'failed': 0,
                'errors': [str(e)]
            }
    
    def resolve_conflicts_interactive(self, conflicts: List) -> Dict:
        """
        Resolve conflicts with interactive feedback
        
        Args:
            conflicts: List of RuleConflict objects
            
        Returns:
            Resolution results
        """
        try:
            # For now, use automatic resolution
            # In a real implementation, this would involve user interaction
            resolution_results = self.conflict_resolver.resolve_conflicts(conflicts)
            
            # Apply resolution actions to the rule system
            for action in resolution_results['actions_taken']:
                logger.info(f"Applied conflict resolution action: {action}")
                # Here you would implement the actual rule modifications
            
            return resolution_results
            
        except Exception as e:
            logger.error(f"Error resolving conflicts: {e}")
            return {
                'resolved_conflicts': [],
                'unresolved_conflicts': conflicts,
                'actions_taken': [],
                'error': str(e)
            }
    
    def _check_system_consistency(self) -> Dict:
        """Check consistency between legacy and versioning systems"""
        try:
            legacy_rules = self.legacy_manager.load_current_rules()
            active_versions = self.version_manager.get_all_active_rules()
            
            legacy_ids = set(rule.get('id') for rule in legacy_rules if rule.get('id'))
            version_ids = set(active_versions.keys())
            
            return {
                'rules_in_legacy': len(legacy_ids),
                'rules_in_versioning': len(version_ids),
                'rules_in_both': len(legacy_ids & version_ids),
                'rules_only_in_legacy': len(legacy_ids - version_ids),
                'rules_only_in_versioning': len(version_ids - legacy_ids)
            }
        except Exception as e:
            logger.error(f"Error checking system consistency: {e}")
            return {}
    
    # Delegate methods to maintain compatibility with existing code
    def load_current_rules(self) -> List[Dict]:
        """Delegate to legacy manager for compatibility"""
        return self.legacy_manager.load_current_rules()
    
    def get_rule_by_id(self, rule_id: str) -> Optional[Dict]:
        """Delegate to legacy manager for compatibility"""
        return self.legacy_manager.get_rule_by_id(rule_id)
    
    def get_rules_by_type(self, rule_type: str) -> List[Dict]:
        """Delegate to legacy manager for compatibility"""
        return self.legacy_manager.get_rules_by_type(rule_type)
    
    def export_rules(self, filepath: str, rule_type: str = None) -> bool:
        """Delegate to legacy manager for compatibility"""
        return self.legacy_manager.export_rules(filepath, rule_type)
    
    def create_backup(self, backup_name: str = None) -> str:
        """Create backup in both systems"""
        try:
            legacy_backup = self.legacy_manager.create_backup(backup_name)
            version_backup = self.version_manager.storage.create_backup(backup_name)
            
            logger.info(f"Created backups: legacy={legacy_backup}, versioning={version_backup}")
            return version_backup  # Return versioning backup path as primary
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return ""

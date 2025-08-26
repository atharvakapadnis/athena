# src/rule_editor/manager.py
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import uuid
import shutil

class RuleManager:
    """Manages rule storage, versioning, and application"""
    
    def __init__(self, rules_dir: Path):
        self.rules_dir = Path(rules_dir)
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        self.current_rules_file = self.rules_dir / "current_rules.json"
        self.rule_history_file = self.rules_dir / "rule_history.json"
        self.approved_rules_file = self.rules_dir / "approved_rules.json"
        self.backup_dir = self.rules_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def load_current_rules(self) -> List[Dict]:
        """Load current active rules"""
        if not self.current_rules_file.exists():
            return []
        
        try:
            with open(self.current_rules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading current rules: {e}")
            return []
    
    def save_current_rules(self, rules: List[Dict]):
        """Save current rules"""
        # Backup current rules if they exist
        if self.current_rules_file.exists():
            backup_file = self.backup_dir / f"backup_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy2(self.current_rules_file, backup_file)
        
        # Save new rules
        try:
            with open(self.current_rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules, f, indent=2, default=str, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving current rules: {e}")
            raise
    
    def add_approved_rule(self, rule: Dict, decision: Dict):
        """Add an approved rule to the system"""
        current_rules = self.load_current_rules()
        
        # Add rule with metadata
        rule_with_metadata = {
            **rule,
            'id': str(uuid.uuid4()),
            'approved_at': datetime.now().isoformat(),
            'approved_by': decision.get('reviewer', 'unknown'),
            'approval_reasoning': decision.get('reasoning', ''),
            'version': len(current_rules) + 1,
            'status': 'active'
        }
        
        current_rules.append(rule_with_metadata)
        self.save_current_rules(current_rules)
        
        # Add to approved rules history
        self._add_to_approved_history(rule_with_metadata, decision)
        
        return rule_with_metadata['id']
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule from the system"""
        current_rules = self.load_current_rules()
        original_count = len(current_rules)
        
        current_rules = [r for r in current_rules if r.get('id') != rule_id]
        
        if len(current_rules) < original_count:
            self.save_current_rules(current_rules)
            return True
        
        return False
    
    def update_rule(self, rule_id: str, updated_rule: Dict) -> bool:
        """Update an existing rule"""
        current_rules = self.load_current_rules()
        
        for i, rule in enumerate(current_rules):
            if rule.get('id') == rule_id:
                # Preserve metadata
                updated_rule_with_metadata = {
                    **updated_rule,
                    'id': rule_id,
                    'approved_at': rule.get('approved_at'),
                    'approved_by': rule.get('approved_by'),
                    'approval_reasoning': rule.get('approval_reasoning'),
                    'version': rule.get('version'),
                    'status': 'active',
                    'last_updated': datetime.now().isoformat()
                }
                
                current_rules[i] = updated_rule_with_metadata
                self.save_current_rules(current_rules)
                return True
        
        return False
    
    def get_rule_by_id(self, rule_id: str) -> Optional[Dict]:
        """Get a specific rule by ID"""
        current_rules = self.load_current_rules()
        
        for rule in current_rules:
            if rule.get('id') == rule_id:
                return rule
        
        return None
    
    def get_rules_by_type(self, rule_type: str) -> List[Dict]:
        """Get all rules of a specific type"""
        current_rules = self.load_current_rules()
        return [rule for rule in current_rules if rule.get('rule_type') == rule_type]
    
    def get_rule_statistics(self) -> Dict:
        """Get statistics about current rules"""
        current_rules = self.load_current_rules()
        
        rule_types = {}
        for rule in current_rules:
            rule_type = rule.get('rule_type', 'unknown')
            rule_types[rule_type] = rule_types.get(rule_type, 0) + 1
        
        # Get approval statistics
        approved_by_stats = {}
        for rule in current_rules:
            approved_by = rule.get('approved_by', 'unknown')
            approved_by_stats[approved_by] = approved_by_stats.get(approved_by, 0) + 1
        
        return {
            'total_rules': len(current_rules),
            'rule_types': rule_types,
            'approved_by': approved_by_stats,
            'last_updated': datetime.now().isoformat()
        }
    
    def export_rules(self, filepath: str, rule_type: str = None) -> bool:
        """Export rules to a file"""
        current_rules = self.load_current_rules()
        
        if rule_type:
            rules_to_export = [rule for rule in current_rules if rule.get('rule_type') == rule_type]
        else:
            rules_to_export = current_rules
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(rules_to_export, f, indent=2, default=str, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error exporting rules: {e}")
            return False
    
    def import_rules(self, filepath: str, merge: bool = True) -> bool:
        """Import rules from a file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported_rules = json.load(f)
            
            if merge:
                current_rules = self.load_current_rules()
                # Add unique ID if missing
                for rule in imported_rules:
                    if 'id' not in rule:
                        rule['id'] = str(uuid.uuid4())
                    rule['imported_at'] = datetime.now().isoformat()
                
                current_rules.extend(imported_rules)
                self.save_current_rules(current_rules)
            else:
                self.save_current_rules(imported_rules)
            
            return True
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error importing rules: {e}")
            return False
    
    def _add_to_approved_history(self, rule: Dict, decision: Dict):
        """Add rule to approved history"""
        history = []
        if self.approved_rules_file.exists():
            try:
                with open(self.approved_rules_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except (json.JSONDecodeError, IOError):
                history = []
        
        history.append({
            'rule': rule,
            'decision': decision,
            'timestamp': datetime.now().isoformat()
        })
        
        try:
            with open(self.approved_rules_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, default=str, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving approved rules history: {e}")
    
    def get_approved_history(self) -> List[Dict]:
        """Get history of approved rules"""
        if not self.approved_rules_file.exists():
            return []
        
        try:
            with open(self.approved_rules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def create_backup(self, backup_name: str = None) -> str:
        """Create a backup of current rules"""
        if backup_name is None:
            backup_name = f"manual_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_file = self.backup_dir / f"{backup_name}.json"
        
        if self.current_rules_file.exists():
            shutil.copy2(self.current_rules_file, backup_file)
            return str(backup_file)
        
        return ""
    
    def restore_from_backup(self, backup_file: str) -> bool:
        """Restore rules from a backup file"""
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            backup_path = self.backup_dir / backup_file
            if not backup_path.exists():
                print(f"Backup file not found: {backup_file}")
                return False
        
        try:
            # Create backup of current state
            self.create_backup("pre_restore_backup")
            
            # Restore from backup
            shutil.copy2(backup_path, self.current_rules_file)
            return True
        except IOError as e:
            print(f"Error restoring from backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """List available backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.json"):
            try:
                stat = backup_file.stat()
                backups.append({
                    'name': backup_file.name,
                    'path': str(backup_file),
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except OSError:
                continue
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)

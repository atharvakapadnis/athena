# src/rule_versioning/storage.py
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class RuleStorage:
    """
    Handles efficient storage and retrieval of rule versions with optimized
    file organization and indexing capabilities.
    """
    
    def __init__(self, base_path: str = "data/rules"):
        self.base_path = Path(base_path)
        self.versions_path = self.base_path / "rule_versions"
        self.active_path = self.base_path / "active"
        self.index_path = self.base_path / "version_index.json"
        self.backup_path = self.base_path / "backups"
        
        self._ensure_directories()
        self._load_or_create_index()
    
    def save_rule_version(self, version):
        """
        Save a rule version to storage with efficient organization
        
        Args:
            version: RuleVersion object to save
        """
        try:
            # Create rule-specific directory
            rule_dir = self.versions_path / version.rule_id
            rule_dir.mkdir(exist_ok=True)
            
            # Save version file
            version_file = rule_dir / f"{version.version_id}.json"
            version_data = version.to_dict()
            
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2, ensure_ascii=False)
            
            # Update index
            self._update_index(version)
            
            # Update active rule if this version is active
            if version.is_active:
                self._update_active_rule(version)
            
            logger.debug(f"Saved version {version.version_id} for rule {version.rule_id}")
            
        except Exception as e:
            logger.error(f"Error saving rule version {version.version_id}: {e}")
            raise
    
    def load_rule_versions(self, rule_id: str) -> List:
        """
        Load all versions of a specific rule sorted by timestamp
        
        Args:
            rule_id: ID of the rule to load versions for
            
        Returns:
            List of RuleVersion objects
        """
        from rule_versioning.version_manager import RuleVersion  # Import here to avoid circular import
        
        versions = []
        rule_dir = self.versions_path / rule_id
        
        if not rule_dir.exists():
            return versions
        
        try:
            for version_file in rule_dir.glob("*.json"):
                try:
                    with open(version_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        versions.append(RuleVersion.from_dict(data))
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Error loading version file {version_file}: {e}")
                    continue
            
            # Sort by timestamp
            versions.sort(key=lambda v: v.timestamp)
            logger.debug(f"Loaded {len(versions)} versions for rule {rule_id}")
            
        except Exception as e:
            logger.error(f"Error loading versions for rule {rule_id}: {e}")
        
        return versions
    
    def load_all_versions(self) -> List:
        """
        Load all rule versions from storage
        
        Returns:
            List of all RuleVersion objects
        """
        all_versions = []
        
        try:
            if not self.versions_path.exists():
                return all_versions
            
            for rule_dir in self.versions_path.iterdir():
                if rule_dir.is_dir():
                    rule_versions = self.load_rule_versions(rule_dir.name)
                    all_versions.extend(rule_versions)
            
            logger.info(f"Loaded {len(all_versions)} total versions from storage")
            
        except Exception as e:
            logger.error(f"Error loading all versions: {e}")
        
        return all_versions
    
    def get_version(self, rule_id: str, version_id: str):
        """
        Get a specific version of a rule
        
        Args:
            rule_id: ID of the rule
            version_id: ID of the version
            
        Returns:
            RuleVersion object or None if not found
        """
        from rule_versioning.version_manager import RuleVersion
        
        version_file = self.versions_path / rule_id / f"{version_id}.json"
        
        if not version_file.exists():
            return None
        
        try:
            with open(version_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return RuleVersion.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error loading version {version_id} for rule {rule_id}: {e}")
            return None
    
    def delete_version(self, rule_id: str, version_id: str) -> bool:
        """
        Delete a specific version (use with caution)
        
        Args:
            rule_id: ID of the rule
            version_id: ID of the version to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            version_file = self.versions_path / rule_id / f"{version_id}.json"
            
            if version_file.exists():
                # Create backup before deletion
                self._backup_version(rule_id, version_id)
                
                # Delete the file
                version_file.unlink()
                
                # Update index
                self._remove_from_index(rule_id, version_id)
                
                logger.info(f"Deleted version {version_id} for rule {rule_id}")
                return True
            else:
                logger.warning(f"Version file not found: {version_file}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting version {version_id} for rule {rule_id}: {e}")
            return False
    
    def get_active_rules(self) -> Dict:
        """
        Get all currently active rules
        
        Returns:
            Dict mapping rule_id to active version data
        """
        active_rules = {}
        
        if not self.active_path.exists():
            return active_rules
        
        try:
            for active_file in self.active_path.glob("*.json"):
                rule_id = active_file.stem
                
                with open(active_file, 'r', encoding='utf-8') as f:
                    active_rules[rule_id] = json.load(f)
                    
        except Exception as e:
            logger.error(f"Error loading active rules: {e}")
        
        return active_rules
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create a complete backup of all rule versions
        
        Args:
            backup_name: Optional name for the backup
            
        Returns:
            Path to the created backup
        """
        if backup_name is None:
            backup_name = f"complete_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_file = self.backup_path / f"{backup_name}.json"
        
        try:
            # Collect all versions
            all_versions = self.load_all_versions()
            
            # Convert to serializable format
            backup_data = {
                'backup_timestamp': datetime.now().isoformat(),
                'total_versions': len(all_versions),
                'versions': [version.to_dict() for version in all_versions]
            }
            
            # Save backup
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created backup with {len(all_versions)} versions: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise
    
    def restore_from_backup(self, backup_file: str) -> bool:
        """
        Restore rule versions from a backup file
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            True if restore successful, False otherwise
        """
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            backup_path = self.backup_path / backup_file
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False
        
        try:
            # Create current state backup before restore
            current_backup = self.create_backup("pre_restore_backup")
            logger.info(f"Created pre-restore backup: {current_backup}")
            
            # Load backup data
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Clear current versions (move to temp backup)
            temp_backup_dir = self.base_path / f"temp_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if self.versions_path.exists():
                self.versions_path.rename(temp_backup_dir)
            
            # Recreate directories
            self._ensure_directories()
            
            # Restore versions
            from rule_versioning.version_manager import RuleVersion
            restored_count = 0
            
            for version_data in backup_data.get('versions', []):
                try:
                    version = RuleVersion.from_dict(version_data)
                    self.save_rule_version(version)
                    restored_count += 1
                except Exception as e:
                    logger.error(f"Error restoring version {version_data.get('version_id')}: {e}")
                    continue
            
            logger.info(f"Restored {restored_count} versions from backup")
            
            # Clean up temp backup if restore successful
            if restored_count > 0:
                import shutil
                shutil.rmtree(temp_backup_dir, ignore_errors=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Error restoring from backup: {e}")
            return False
    
    def get_storage_statistics(self) -> Dict:
        """Get statistics about storage usage and organization"""
        stats = {
            'total_rules': 0,
            'total_versions': 0,
            'storage_size_mb': 0,
            'rule_distribution': {},
            'oldest_version': None,
            'newest_version': None
        }
        
        try:
            if not self.versions_path.exists():
                return stats
            
            total_size = 0
            all_timestamps = []
            
            for rule_dir in self.versions_path.iterdir():
                if rule_dir.is_dir():
                    stats['total_rules'] += 1
                    rule_version_count = 0
                    
                    for version_file in rule_dir.glob("*.json"):
                        stats['total_versions'] += 1
                        rule_version_count += 1
                        total_size += version_file.stat().st_size
                        
                        # Track timestamps for oldest/newest
                        try:
                            with open(version_file, 'r') as f:
                                data = json.load(f)
                                timestamp = data.get('timestamp')
                                if timestamp:
                                    all_timestamps.append(timestamp)
                        except Exception:
                            pass
                    
                    stats['rule_distribution'][rule_dir.name] = rule_version_count
            
            stats['storage_size_mb'] = round(total_size / (1024 * 1024), 2)
            
            if all_timestamps:
                all_timestamps.sort()
                stats['oldest_version'] = all_timestamps[0]
                stats['newest_version'] = all_timestamps[-1]
                
        except Exception as e:
            logger.error(f"Error calculating storage statistics: {e}")
        
        return stats
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        for directory in [self.versions_path, self.active_path, self.backup_path]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_or_create_index(self):
        """Load or create the version index for fast lookups"""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.index = self._build_index()
        else:
            self.index = self._build_index()
    
    def _build_index(self) -> Dict:
        """Build index from existing files"""
        index = {
            'rules': {},
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            if self.versions_path.exists():
                for rule_dir in self.versions_path.iterdir():
                    if rule_dir.is_dir():
                        rule_id = rule_dir.name
                        index['rules'][rule_id] = {
                            'versions': [],
                            'active_version': None
                        }
                        
                        for version_file in rule_dir.glob("*.json"):
                            version_id = version_file.stem
                            index['rules'][rule_id]['versions'].append(version_id)
            
            self._save_index(index)
            
        except Exception as e:
            logger.error(f"Error building index: {e}")
        
        return index
    
    def _update_index(self, version):
        """Update the version index when a new version is saved"""
        rule_id = version.rule_id
        
        if 'rules' not in self.index:
            self.index['rules'] = {}
        
        if rule_id not in self.index['rules']:
            self.index['rules'][rule_id] = {
                'versions': [],
                'active_version': None
            }
        
        if version.version_id not in self.index['rules'][rule_id]['versions']:
            self.index['rules'][rule_id]['versions'].append(version.version_id)
        
        if version.is_active:
            self.index['rules'][rule_id]['active_version'] = version.version_id
        
        self.index['last_updated'] = datetime.now().isoformat()
        self._save_index(self.index)
    
    def _save_index(self, index: Dict):
        """Save the index to disk"""
        try:
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def _remove_from_index(self, rule_id: str, version_id: str):
        """Remove a version from the index"""
        if rule_id in self.index.get('rules', {}):
            versions = self.index['rules'][rule_id]['versions']
            if version_id in versions:
                versions.remove(version_id)
            
            if self.index['rules'][rule_id]['active_version'] == version_id:
                self.index['rules'][rule_id]['active_version'] = None
            
            self._save_index(self.index)
    
    def _update_active_rule(self, version):
        """Update the active rule file"""
        try:
            active_file = self.active_path / f"{version.rule_id}.json"
            
            with open(active_file, 'w', encoding='utf-8') as f:
                json.dump(version.to_dict(), f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error updating active rule {version.rule_id}: {e}")
    
    def _backup_version(self, rule_id: str, version_id: str):
        """Create a backup of a version before deletion"""
        try:
            source_file = self.versions_path / rule_id / f"{version_id}.json"
            backup_file = self.backup_path / f"deleted_{rule_id}_{version_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            import shutil
            shutil.copy2(source_file, backup_file)
            
        except Exception as e:
            logger.warning(f"Error creating backup for version {version_id}: {e}")

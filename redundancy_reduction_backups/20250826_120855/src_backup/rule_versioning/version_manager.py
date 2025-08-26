# src/rule_versioning/version_manager.py
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
import hashlib
import logging
from pathlib import Path

# Import storage module locally to avoid circular imports

logger = logging.getLogger(__name__)

@dataclass
class RuleVersion:
    """Represents a single version of a rule with full metadata"""
    version_id: str
    rule_id: str
    rule_content: Dict
    timestamp: datetime
    author: str
    change_description: str
    parent_version: Optional[str]
    is_active: bool
    change_type: str = "modification"  # creation, modification, rollback
    impact_score: float = 0.0  # Predicted impact of this change
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'RuleVersion':
        """Create from dictionary (JSON deserialization)"""
        data = data.copy()
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class RuleVersionManager:
    """
    Manages the complete lifecycle of rule versions including creation,
    tracking, rollback, and conflict detection.
    """
    
    def __init__(self, rules_dir: str = "data/rules"):
        self.rules_dir = Path(rules_dir)
        # Import here to avoid circular imports
        from .storage import RuleStorage
        self.storage = RuleStorage(str(self.rules_dir))
        self.version_history: Dict[str, List[RuleVersion]] = {}
        self._load_version_history()
    
    def create_version(self, rule_id: str, rule_content: Dict, 
                      author: str, description: str, 
                      change_type: str = "modification") -> str:
        """
        Create a new version of a rule
        
        Args:
            rule_id: Unique identifier for the rule
            rule_content: The actual rule content
            author: Who made this change
            description: Description of what changed
            change_type: Type of change (creation, modification, rollback)
            
        Returns:
            version_id: Unique identifier for this version
        """
        try:
            # Generate unique version ID
            version_id = self._generate_version_id(rule_id, rule_content)
            
            # Check if this exact version already exists
            if self._version_exists(rule_id, version_id):
                logger.warning(f"Version {version_id} already exists for rule {rule_id}")
                return version_id
            
            # Get parent version
            parent_version = self._get_current_version(rule_id)
            
            # Calculate impact score
            impact_score = self._calculate_impact_score(rule_content, parent_version)
            
            # Create version object
            version = RuleVersion(
                version_id=version_id,
                rule_id=rule_id,
                rule_content=rule_content.copy(),
                timestamp=datetime.now(),
                author=author,
                change_description=description,
                parent_version=parent_version,
                is_active=True,
                change_type=change_type,
                impact_score=impact_score
            )
            
            # Deactivate previous version
            if parent_version:
                self._deactivate_version(rule_id, parent_version)
            
            # Save version
            self._save_version(version)
            
            # Update version history
            if rule_id not in self.version_history:
                self.version_history[rule_id] = []
            self.version_history[rule_id].append(version)
            
            logger.info(f"Created version {version_id} for rule {rule_id}")
            return version_id
            
        except Exception as e:
            logger.error(f"Error creating version for rule {rule_id}: {e}")
            raise
    
    def rollback_to_version(self, rule_id: str, target_version_id: str, 
                           author: str, reason: str) -> bool:
        """
        Rollback a rule to a specific version
        
        Args:
            rule_id: The rule to rollback
            target_version_id: The version to rollback to
            author: Who initiated the rollback
            reason: Reason for rollback
            
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            # Get target version
            target_version = self.get_version(rule_id, target_version_id)
            if not target_version:
                logger.error(f"Target version {target_version_id} not found for rule {rule_id}")
                return False
            
            # Create new version with target content
            rollback_description = f"Rollback to version {target_version_id}: {reason}"
            new_version_id = self.create_version(
                rule_id=rule_id,
                rule_content=target_version.rule_content,
                author=author,
                description=rollback_description,
                change_type="rollback"
            )
            
            logger.info(f"Successfully rolled back rule {rule_id} to version {target_version_id} as {new_version_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error rolling back rule {rule_id} to version {target_version_id}: {e}")
            return False
    
    def get_version(self, rule_id: str, version_id: str) -> Optional[RuleVersion]:
        """Get a specific version of a rule"""
        if rule_id in self.version_history:
            for version in self.version_history[rule_id]:
                if version.version_id == version_id:
                    return version
        return None
    
    def get_current_version(self, rule_id: str) -> Optional[RuleVersion]:
        """Get the current active version of a rule"""
        if rule_id in self.version_history:
            for version in reversed(self.version_history[rule_id]):
                if version.is_active:
                    return version
        return None
    
    def get_version_history(self, rule_id: str) -> List[RuleVersion]:
        """Get complete version history for a rule"""
        return self.version_history.get(rule_id, [])
    
    def get_all_active_rules(self) -> Dict[str, RuleVersion]:
        """Get all currently active rule versions"""
        active_rules = {}
        for rule_id in self.version_history:
            current = self.get_current_version(rule_id)
            if current:
                active_rules[rule_id] = current
        return active_rules
    
    def deactivate_rule(self, rule_id: str, author: str, reason: str) -> bool:
        """Deactivate a rule (mark as inactive)"""
        try:
            current_version = self.get_current_version(rule_id)
            if not current_version:
                logger.warning(f"No active version found for rule {rule_id}")
                return False
            
            # Create deactivation record
            deactivation_content = {
                **current_version.rule_content,
                "_deactivated": True,
                "_deactivation_reason": reason
            }
            
            self.create_version(
                rule_id=rule_id,
                rule_content=deactivation_content,
                author=author,
                description=f"Deactivated: {reason}",
                change_type="deactivation"
            )
            
            # Mark as inactive
            current_version.is_active = False
            self._save_version(current_version)
            
            logger.info(f"Deactivated rule {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating rule {rule_id}: {e}")
            return False
    
    def get_version_statistics(self) -> Dict:
        """Get comprehensive statistics about rule versions"""
        stats = {
            'total_rules': len(self.version_history),
            'total_versions': sum(len(versions) for versions in self.version_history.values()),
            'active_rules': len([rule_id for rule_id in self.version_history 
                               if self.get_current_version(rule_id) and 
                               self.get_current_version(rule_id).is_active]),
            'change_types': {},
            'authors': {},
            'recent_changes': []
        }
        
        # Analyze change types and authors
        all_versions = []
        for versions in self.version_history.values():
            all_versions.extend(versions)
        
        for version in all_versions:
            # Change types
            change_type = version.change_type
            stats['change_types'][change_type] = stats['change_types'].get(change_type, 0) + 1
            
            # Authors
            author = version.author
            stats['authors'][author] = stats['authors'].get(author, 0) + 1
        
        # Recent changes (last 10)
        all_versions.sort(key=lambda v: v.timestamp, reverse=True)
        stats['recent_changes'] = [
            {
                'rule_id': v.rule_id,
                'version_id': v.version_id,
                'author': v.author,
                'change_type': v.change_type,
                'description': v.change_description,
                'timestamp': v.timestamp.isoformat()
            }
            for v in all_versions[:10]
        ]
        
        return stats
    
    def _generate_version_id(self, rule_id: str, content: Dict) -> str:
        """Generate unique version ID based on rule ID, content, and timestamp"""
        timestamp = datetime.now().isoformat()
        content_str = json.dumps(content, sort_keys=True)
        hash_input = f"{rule_id}:{content_str}:{timestamp}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]
    
    def _get_current_version(self, rule_id: str) -> Optional[str]:
        """Get the current version ID for a rule"""
        current = self.get_current_version(rule_id)
        return current.version_id if current else None
    
    def _version_exists(self, rule_id: str, version_id: str) -> bool:
        """Check if a version already exists"""
        return self.get_version(rule_id, version_id) is not None
    
    def _deactivate_version(self, rule_id: str, version_id: str):
        """Mark a specific version as inactive"""
        version = self.get_version(rule_id, version_id)
        if version:
            version.is_active = False
            self._save_version(version)
    
    def _save_version(self, version: RuleVersion):
        """Save a version to storage"""
        self.storage.save_rule_version(version)
    
    def _load_version_history(self):
        """Load complete version history from storage"""
        try:
            all_versions = self.storage.load_all_versions()
            
            for version in all_versions:
                rule_id = version.rule_id
                if rule_id not in self.version_history:
                    self.version_history[rule_id] = []
                self.version_history[rule_id].append(version)
            
            # Sort version history by timestamp
            for rule_id in self.version_history:
                self.version_history[rule_id].sort(key=lambda v: v.timestamp)
            
            logger.info(f"Loaded version history for {len(self.version_history)} rules")
            
        except Exception as e:
            logger.error(f"Error loading version history: {e}")
            self.version_history = {}
    
    def _calculate_impact_score(self, rule_content: Dict, parent_version_id: Optional[str]) -> float:
        """
        Calculate predicted impact score for a rule change
        Higher score = more significant change
        """
        if not parent_version_id:
            return 1.0  # New rule creation has high impact
        
        parent_version = self.get_version(rule_content.get('rule_id', ''), parent_version_id)
        if not parent_version:
            return 1.0
        
        # Compare rule contents to estimate impact
        parent_content = parent_version.rule_content
        
        impact_factors = []
        
        # Check if pattern changed
        if rule_content.get('pattern') != parent_content.get('pattern'):
            impact_factors.append(0.8)  # High impact
        
        # Check if replacement changed
        if rule_content.get('replacement') != parent_content.get('replacement'):
            impact_factors.append(0.6)  # Medium-high impact
        
        # Check if confidence changed significantly
        old_conf = parent_content.get('confidence', 0.5)
        new_conf = rule_content.get('confidence', 0.5)
        if abs(new_conf - old_conf) > 0.2:
            impact_factors.append(0.4)  # Medium impact
        
        # Check if priority changed
        if rule_content.get('priority') != parent_content.get('priority'):
            impact_factors.append(0.3)  # Medium-low impact
        
        # Return average impact, minimum 0.1
        return max(0.1, sum(impact_factors) / len(impact_factors) if impact_factors else 0.1)

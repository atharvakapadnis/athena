# src/ai_analysis/notes_manager.py
"""
AI Notes Manager for tracking AI observations, findings, and human feedback
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import uuid
from pathlib import Path
from ..utils.logger import get_logger
from ..utils.config import DATA_DIR

logger = get_logger(__name__)

@dataclass
class AINote:
    """Represents an AI-generated note or observation"""
    note_id: str
    timestamp: datetime
    note_type: str  # "observation", "finding", "suggestion", "feedback"
    content: str
    context: Dict  # Related data, batch info, etc.
    tags: List[str]
    priority: int  # 1-5, higher = more important
    status: str  # "active", "resolved", "archived"
    author: str  # "ai" or "human"

@dataclass
class HumanFeedback:
    """Represents human feedback on AI suggestions or observations"""
    feedback_id: str
    timestamp: datetime
    related_note_id: Optional[str]
    content: str
    action_taken: str  # "accepted", "rejected", "modified", "ignored"
    user_id: str

class NotesManager:
    """Manages AI notes and human feedback with persistent storage"""
    
    def __init__(self, notes_dir: str = None):
        self.notes_dir = Path(notes_dir) if notes_dir else DATA_DIR / "ai_notes"
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        
        self.notes_file = self.notes_dir / "notes.json"
        self.feedback_file = self.notes_dir / "feedback.json"
        
        self.notes: List[AINote] = []
        self.feedback: List[HumanFeedback] = []
        
        # Load existing data
        self._load_data()
        
        logger.info(f"NotesManager initialized with {len(self.notes)} notes and {len(self.feedback)} feedback items")
    
    def add_ai_note(self, note_type: str, content: str, 
                   context: Dict = None, tags: List[str] = None,
                   priority: int = 3) -> str:
        """Add a new AI-generated note"""
        note_id = self._generate_note_id()
        note = AINote(
            note_id=note_id,
            timestamp=datetime.now(),
            note_type=note_type,
            content=content,
            context=context or {},
            tags=tags or [],
            priority=priority,
            status="active",
            author="ai"
        )
        
        self.notes.append(note)
        self._save_notes()
        
        logger.info(f"Added AI note: {note_type} - {content[:50]}...", 
                   note_id=note_id, priority=priority)
        return note_id
    
    def add_human_feedback(self, content: str, related_note_id: str = None,
                          action_taken: str = "reviewed", user_id: str = "user") -> str:
        """Add human feedback to the system"""
        feedback_id = self._generate_feedback_id()
        feedback = HumanFeedback(
            feedback_id=feedback_id,
            timestamp=datetime.now(),
            related_note_id=related_note_id,
            content=content,
            action_taken=action_taken,
            user_id=user_id
        )
        
        self.feedback.append(feedback)
        self._save_feedback()
        
        logger.info(f"Added human feedback: {action_taken} - {content[:50]}...",
                   feedback_id=feedback_id, related_note_id=related_note_id)
        return feedback_id
    
    def get_notes_by_type(self, note_type: str) -> List[AINote]:
        """Get all notes of a specific type"""
        return [note for note in self.notes if note.note_type == note_type]
    
    def get_notes_by_priority(self, min_priority: int = 1) -> List[AINote]:
        """Get notes above a certain priority threshold"""
        return [note for note in self.notes if note.priority >= min_priority]
    
    def get_notes_by_status(self, status: str) -> List[AINote]:
        """Get notes by status"""
        return [note for note in self.notes if note.status == status]
    
    def search_notes(self, query: str, tags: List[str] = None) -> List[AINote]:
        """Search notes by content and tags"""
        results = []
        query_lower = query.lower()
        
        for note in self.notes:
            content_match = query_lower in note.content.lower()
            tag_match = not tags or any(tag in note.tags for tag in tags)
            
            if content_match and tag_match:
                results.append(note)
        
        logger.info(f"Search for '{query}' found {len(results)} notes")
        return results
    
    def update_note_status(self, note_id: str, new_status: str) -> bool:
        """Update the status of a note"""
        for note in self.notes:
            if note.note_id == note_id:
                old_status = note.status
                note.status = new_status
                self._save_notes()
                
                logger.info(f"Updated note status: {note_id} from {old_status} to {new_status}")
                return True
        
        logger.warning(f"Note not found for status update: {note_id}")
        return False
    
    def archive_old_notes(self, days_old: int = 30) -> int:
        """Archive notes older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        archived_count = 0
        
        for note in self.notes:
            if note.timestamp < cutoff_date and note.status == "active":
                note.status = "archived"
                archived_count += 1
        
        if archived_count > 0:
            self._save_notes()
            logger.info(f"Archived {archived_count} notes older than {days_old} days")
        
        return archived_count
    
    def get_feedback_for_note(self, note_id: str) -> List[HumanFeedback]:
        """Get all feedback related to a specific note"""
        return [fb for fb in self.feedback if fb.related_note_id == note_id]
    
    def get_recent_activity(self, hours: int = 24) -> Dict:
        """Get recent notes and feedback activity"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_notes = [note for note in self.notes if note.timestamp > cutoff_time]
        recent_feedback = [fb for fb in self.feedback if fb.timestamp > cutoff_time]
        
        return {
            "recent_notes": recent_notes,
            "recent_feedback": recent_feedback,
            "notes_count": len(recent_notes),
            "feedback_count": len(recent_feedback),
            "time_window_hours": hours
        }
    
    def _generate_note_id(self) -> str:
        """Generate a unique note ID"""
        return f"note_{uuid.uuid4().hex[:12]}"
    
    def _generate_feedback_id(self) -> str:
        """Generate a unique feedback ID"""
        return f"feedback_{uuid.uuid4().hex[:12]}"
    
    def _load_data(self):
        """Load existing notes and feedback from storage"""
        try:
            # Load notes
            if self.notes_file.exists():
                with open(self.notes_file, 'r') as f:
                    notes_data = json.load(f)
                    self.notes = [
                        AINote(
                            note_id=note_data['note_id'],
                            timestamp=datetime.fromisoformat(note_data['timestamp']),
                            note_type=note_data['note_type'],
                            content=note_data['content'],
                            context=note_data['context'],
                            tags=note_data['tags'],
                            priority=note_data['priority'],
                            status=note_data['status'],
                            author=note_data['author']
                        )
                        for note_data in notes_data
                    ]
            
            # Load feedback
            if self.feedback_file.exists():
                with open(self.feedback_file, 'r') as f:
                    feedback_data = json.load(f)
                    self.feedback = [
                        HumanFeedback(
                            feedback_id=fb_data['feedback_id'],
                            timestamp=datetime.fromisoformat(fb_data['timestamp']),
                            related_note_id=fb_data.get('related_note_id'),
                            content=fb_data['content'],
                            action_taken=fb_data['action_taken'],
                            user_id=fb_data['user_id']
                        )
                        for fb_data in feedback_data
                    ]
                    
        except Exception as e:
            logger.error(f"Error loading notes data: {e}")
            self.notes = []
            self.feedback = []
    
    def _save_notes(self):
        """Save notes to persistent storage"""
        try:
            notes_data = []
            for note in self.notes:
                note_dict = asdict(note)
                note_dict['timestamp'] = note.timestamp.isoformat()
                notes_data.append(note_dict)
            
            with open(self.notes_file, 'w') as f:
                json.dump(notes_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving notes: {e}")
    
    def _save_feedback(self):
        """Save feedback to persistent storage"""
        try:
            feedback_data = []
            for feedback in self.feedback:
                feedback_dict = asdict(feedback)
                feedback_dict['timestamp'] = feedback.timestamp.isoformat()
                feedback_data.append(feedback_dict)
            
            with open(self.feedback_file, 'w') as f:
                json.dump(feedback_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
    
    def get_summary(self) -> Dict:
        """Get a summary of all notes and feedback"""
        note_types = {}
        priority_counts = {}
        status_counts = {}
        
        for note in self.notes:
            note_types[note.note_type] = note_types.get(note.note_type, 0) + 1
            priority_counts[note.priority] = priority_counts.get(note.priority, 0) + 1
            status_counts[note.status] = status_counts.get(note.status, 0) + 1
        
        action_counts = {}
        for feedback in self.feedback:
            action_counts[feedback.action_taken] = action_counts.get(feedback.action_taken, 0) + 1
        
        return {
            "total_notes": len(self.notes),
            "total_feedback": len(self.feedback),
            "note_types": note_types,
            "priority_distribution": priority_counts,
            "status_distribution": status_counts,
            "feedback_actions": action_counts
        }

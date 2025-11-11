"""
Session management and data persistence
"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional


class Session:
    """Manages conversation session data and persistence"""
    
    def __init__(self):
        self.id = str(uuid.uuid4())[:8]
        self.data: Dict[str, Any] = {}
        self.triage_complete = False
        self.triage_attempts = 0
        self.conversation_log: List[Dict] = []
        self.start_time = datetime.now()
        self.triage_task_id: Optional[str] = None
        self.triage_context_id: Optional[str] = None
        self.triage_results: Dict[str, Any] = {}
        self.in_triage_mode = False
    
    def add_interaction(self, role: str, message: str, extra_data: Optional[Dict] = None):
        """Log a conversation interaction"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "message": message,
            "session_data_snapshot": self.data.copy()
        }
        if extra_data:
            interaction["extra_data"] = extra_data
        
        self.conversation_log.append(interaction)
        print(f"SESSION-LOG: {role.upper()} - {message[:100]}...")
    
    def update_data(self, key: str, value: Any):
        """Update session data with logging"""
        self.data[key] = value
        print(f"SESSION-UPDATE: Set {key} = {value}")
    
    def update_multiple(self, data: Dict[str, Any]):
        """Update multiple session data fields"""
        for key, value in data.items():
            if value:
                self.update_data(key, value)
    
    def has_required_fields(self, fields: List[str]) -> bool:
        """Check if all required fields are present"""
        return all(k in self.data and self.data[k] for k in fields)
    
    def save_to_file(self) -> Optional[str]:
        """Save session data to JSON file"""
        try:
            os.makedirs("sessions", exist_ok=True)
            filename = f"sessions/session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.id}.json"
            
            session_data = {
                "session_id": self.id,
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_minutes": (datetime.now() - self.start_time).total_seconds() / 60,
                "final_data": self.data,
                "triage_complete": self.triage_complete,
                "triage_attempts": self.triage_attempts,
                "triage_results": self.triage_results,
                "conversation_log": self.conversation_log,
                "data_fields_collected": list(self.data.keys()),
                "total_interactions": len(self.conversation_log)
            }
            
            with open(filename, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            print(f"SESSION: Saved complete session to {filename}")
            return filename
        except Exception as e:
            print(f"SESSION: Save failed: {e}")
            return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get session summary"""
        return {
            "session_id": self.id,
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "interactions": len(self.conversation_log),
            "fields_collected": len(self.data),
            "triage_complete": self.triage_complete
        }
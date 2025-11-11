"""
Session Management
"""
import json
import os
import uuid
from datetime import datetime


class Session:
    """Manages session state and conversation history"""
    
    def __init__(self, session_dir='sessions'):
        self.id = str(uuid.uuid4())[:8]
        self.session_dir = session_dir
        self.data = {}
        self.triage_complete = False
        self.triage_attempts = 0
        self.conversation_log = []
        self.start_time = datetime.now()
        self.triage_task_id = None
        self.triage_context_id = None
        self.triage_results = {}
        self.in_triage_mode = False
        
        print(f"SESSION: Created session {self.id}")
    
    def add_interaction(self, role, message, extra_data=None):
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
    
    def save_to_file(self):
        """Save session data to file"""
        try:
            os.makedirs(self.session_dir, exist_ok=True)
            filename = f"{self.session_dir}/session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.id}.json"
            
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
"""Session management for IP Grabber Bot."""

import json
import os
from typing import Dict, Optional, Any
from datetime import datetime


class SessionManager:
    """Manage bot sessions with persistent storage."""
    
    def __init__(self, storage_file: str = "sessions.json"):
        self.storage_file = storage_file
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._load_sessions()
    
    def _load_sessions(self):
        """Load sessions from file."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.storage_file) or '.', exist_ok=True)
        
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    self.sessions = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.sessions = {}
    
    def _save_sessions(self):
        """Save sessions to file."""
        os.makedirs(os.path.dirname(self.storage_file) or '.', exist_ok=True)
        with open(self.storage_file, 'w') as f:
            json.dump(self.sessions, f, indent=2)
    
    # ... rest of the methods remain the same ...

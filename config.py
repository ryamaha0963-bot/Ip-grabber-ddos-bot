"""Configuration management for IP Grabber Bot."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Bot configuration."""
    
    api_id: int
    api_hash: str
    bot_token: str
    session_string: str
    admin_id: int
    max_sessions: int = 10
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load config from environment variables."""
        required = ["API_ID", "API_HASH", "BOT_TOKEN", "SESSION_STRING", "ADMIN_ID"]
        missing = [key for key in required if not os.getenv(key)]
        
        if missing:
            raise ValueError(f"Missing required env vars: {', '.join(missing)}")
        
        return cls(
            api_id=int(os.getenv("API_ID")),
            api_hash=os.getenv("API_HASH"),
            bot_token=os.getenv("BOT_TOKEN"),
            session_string=os.getenv("SESSION_STRING"),
            admin_id=int(os.getenv("ADMIN_ID")),
            max_sessions=int(os.getenv("MAX_SESSIONS", "10"))
        )

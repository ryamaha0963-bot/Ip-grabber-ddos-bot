"""Utility functions for IP Grabber Bot."""

import ipaddress
import re
from typing import Optional, List


def is_valid_ip(ip: str) -> bool:
    """Check if string is valid IP address."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def extract_ips_from_text(text: str) -> List[str]:
    """Extract IP addresses from text."""
    ip_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    return re.findall(ip_pattern, text)


def format_session_info(session_id: str, chat_name: str, ip: str, port: int) -> str:
    """Format session information for display."""
    return f"""🎯 **IP Extracted**

**Session:** {session_id}
**Chat:** {chat_name}
**IP:** {ip}
**Port:** {port}

[Copy Command]"""


def format_session_list(sessions: dict) -> str:
    """Format list of sessions."""
    if not sessions:
        return "📭 **No Active Sessions**\n\nUse /addsession to create one."
    
    text = "📋 **Active Sessions**\n\n"
    for idx, (session_id, data) in enumerate(sessions.items(), 1):
        text += f"**{idx}. {session_id}**\n"
        text += f"   Chat: {data.get('chat_name', 'Unknown')}\n"
        text += f"   IP: {data.get('ip', 'Not set')}\n"
        text += f"   Port: {data.get('port', 'Not set')}\n\n"
    
    return text


def human_bytes(size: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

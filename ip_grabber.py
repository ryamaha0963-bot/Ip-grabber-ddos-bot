"""IP extraction from Telegram voice chats."""

import asyncio
import json
import logging
import re
from typing import Optional, Dict, List, Tuple

from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.raw import functions, types

LOGGER = logging.getLogger(__name__)


class IPGrabber:
    """Extract IP addresses from voice chats."""
    
    def __init__(self, client: Client):
        self.client = client
        self.cache: Dict[int, Dict] = {}
    
    async def extract_ip_from_chat(self, chat_id: int, session_id: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract IP and port from a voice chat."""
        try:
            # Resolve peer
            peer = await self.client.resolve_peer(chat_id)
            
            # Get chat info
            if isinstance(peer, types.InputPeerChannel):
                full = await self.client.invoke(
                    functions.channels.GetFullChannel(
                        channel=types.InputChannel(
                            channel_id=peer.channel_id,
                            access_hash=peer.access_hash
                        )
                    )
                )
            elif isinstance(peer, types.InputPeerChat):
                full = await self.client.invoke(
                    functions.messages.GetFullChat(chat_id=peer.chat_id)
                )
            else:
                return None, None
            
            # Check if voice chat is active
            call = getattr(full.full_chat, "call", None)
            if not call:
                LOGGER.info(f"No active voice chat in {chat_id}")
                return None, None
            
            # Get call parameters
            try:
                group_call = await self.client.invoke(
                    functions.phone.GetGroupCall(
                        call=types.InputGroupCall(
                            id=call.id,
                            access_hash=call.access_hash
                        ),
                        limit=100
                    )
                )
            except Exception as e:
                LOGGER.warning(f"Failed to get group call: {e}")
                return None, None
            
            # Extract IP from params
            call_obj = group_call.call
            params_raw = getattr(call_obj, "params", None)
            params_data = getattr(params_raw, "data", "{}") if params_raw else "{}"
            
            try:
                parsed = json.loads(params_data)
            except json.JSONDecodeError:
                parsed = {"raw": params_data}
            
            # Extract IPs from endpoints
            ips = self._extract_ips_from_params(parsed)
            
            if ips:
                ip, port = ips[0]
                LOGGER.info(f"✅ IP Extracted: {ip}:{port} from {chat_id}")
                return ip, port
            
            LOGGER.info(f"No IP found in {chat_id}")
            return None, None
            
        except FloodWait as e:
            LOGGER.warning(f"FloodWait: {e.value}s")
            raise
        except Exception as e:
            LOGGER.error(f"Error extracting IP: {e}")
            return None, None
    
    def _extract_ips_from_params(self, params: dict) -> List[Tuple[str, int]]:
        """Extract IP:port pairs from call parameters."""
        results = []
        
        # Check endpoints
        endpoints = params.get("endpoints", [])
        for endpoint in endpoints:
            if ":" in endpoint:
                parts = endpoint.rsplit(":", 1)
                if len(parts) == 2:
                    ip, port_str = parts
                    try:
                        port = int(port_str)
                        if re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
                            results.append((ip, port))
                    except (ValueError, TypeError):
                        continue
        
        # Check servers
        servers = params.get("servers", [])
        for server in servers:
            if isinstance(server, dict):
                ip = server.get("ip") or server.get("host")
                port = server.get("port", 0)
                if ip and port and re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
                    results.append((ip, port))
        
        return results
    
    async def get_chat_info(self, chat_id: int) -> Optional[Dict]:
        """Get chat information."""
        try:
            chat = await self.client.get_chat(chat_id)
            return {
                "id": chat.id,
                "title": chat.title or str(chat.id),
                "type": str(chat.type)
            }
        except Exception as e:
            LOGGER.error(f"Error getting chat info: {e}")
            return None

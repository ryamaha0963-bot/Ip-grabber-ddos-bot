"""Telegram bot handler for IP Grabber - Railway Version."""

import logging
import traceback
from typing import Optional

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery
)
from pyrogram.handlers import MessageHandler, CallbackQueryHandler

from session_manager import SessionManager
from ip_grabber import IPGrabber
from utils import format_session_info, format_session_list

LOGGER = logging.getLogger(__name__)


class IPGrabberBot:
    """Main bot handler."""
    
    def __init__(
        self,
        bot: Client,
        user_client: Client,
        session_manager: SessionManager,
        ip_grabber: IPGrabber,
        admin_id: int
    ):
        self.bot = bot
        self.user_client = user_client
        self.session_manager = session_manager
        self.ip_grabber = ip_grabber
        self.admin_id = admin_id
        
        LOGGER.info("🤖 Registering handlers...")
        self._register_handlers()
        LOGGER.info("✅ Handlers registered")
    
    def _register_handlers(self):
        """Register all message and callback handlers."""
        # Command handlers
        self.bot.add_handler(MessageHandler(self.start_command, filters.command("start")))
        self.bot.add_handler(MessageHandler(self.help_command, filters.command("help")))
        self.bot.add_handler(MessageHandler(self.sessions_command, filters.command("sessions")))
        self.bot.add_handler(MessageHandler(self.getip_command, filters.command("getip")))
        self.bot.add_handler(MessageHandler(self.addsession_command, filters.command("addsession")))
        self.bot.add_handler(MessageHandler(self.delsession_command, filters.command("delsession")))
        self.bot.add_handler(MessageHandler(self.extract_command, filters.command("extract")))
        self.bot.add_handler(MessageHandler(self.stats_command, filters.command("stats")))
        
        # Callback handlers
        self.bot.add_handler(CallbackQueryHandler(self.callback_handler))
    
    async def start_command(self, client: Client, message: Message):
        """Handle /start command."""
        await message.reply_text(
            "🔍 **IP Grabber Bot**\n\n"
            "Extract IP addresses from Telegram voice chats.\n\n"
            "**Commands:**\n"
            "/start - Show this message\n"
            "/help - Show help\n"
            "/sessions - List all sessions\n"
            "/addsession <id> <chat_id> <chat_name> - Add a session\n"
            "/delsession <id> - Delete a session\n"
            "/getip <session_id> - Get IP from a session\n"
            "/extract <chat_id> - Extract IP from a chat\n"
            "/stats - Show bot statistics\n\n"
            "**Example:**\n"
            "/getip S10\n"
            "/extract -1003329480093",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, client: Client, message: Message):
        """Handle /help command."""
        await self.start_command(client, message)
    
    async def stats_command(self, client: Client, message: Message):
        """Handle /stats command."""
        if not self._is_admin(message):
            await message.reply_text("❌ Only admin can view stats.")
            return
        
        sessions = self.session_manager.get_all_sessions()
        active_sessions = len(sessions)
        sessions_with_ip = sum(1 for s in sessions.values() if s.get("ip"))
        
        stats_text = f"""
📊 **Bot Statistics**

**Platform:** Railway
**Total Sessions:** {active_sessions}
**Sessions with IP:** {sessions_with_ip}
**Uptime:** Online 🟢
**Admin ID:** {self.admin_id}

**Session List:**
"""
        for idx, (sid, data) in enumerate(sessions.items(), 1):
            has_ip = "✅" if data.get("ip") else "❌"
            stats_text += f"{idx}. {sid} {has_ip} - {data.get('chat_name', 'Unknown')}\n"
        
        await message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
    
    async def sessions_command(self, client: Client, message: Message):
        """Handle /sessions command."""
        sessions = self.session_manager.get_all_sessions()
        text = format_session_list(sessions)
        
        # Add inline buttons for each session
        buttons = []
        for session_id in sessions.keys():
            buttons.append([
                InlineKeyboardButton(
                    f"📱 {session_id}",
                    callback_data=f"view_session:{session_id}"
                )
            ])
        
        # Add refresh button
        if buttons:
            buttons.append([InlineKeyboardButton("🔄 Refresh", callback_data="refresh_list")])
            reply_markup = InlineKeyboardMarkup(buttons)
        else:
            reply_markup = None
        
        await message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    
    async def addsession_command(self, client: Client, message: Message):
        """Handle /addsession command."""
        if not self._is_admin(message):
            await message.reply_text("❌ Only admin can manage sessions.")
            return
        
        args = message.text.split()
        if len(args) < 4:
            await message.reply_text(
                "❌ **Usage:**\n"
                "/addsession <session_id> <chat_id> <chat_name>\n\n"
                "**Example:**\n"
                "/addsession S10 -1003329480093 Damon Holiday",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        session_id = args[1]
        chat_id = int(args[2])
        chat_name = " ".join(args[3:])
        
        if self.session_manager.create_session(session_id, chat_id, chat_name):
            await message.reply_text(
                f"✅ **Session Created**\n\n"
                f"**ID:** {session_id}\n"
                f"**Chat ID:** {chat_id}\n"
                f"**Chat Name:** {chat_name}\n\n"
                f"Use `/getip {session_id}` to extract IP.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.reply_text(f"❌ Session '{session_id}' already exists.")
    
    async def delsession_command(self, client: Client, message: Message):
        """Handle /delsession command."""
        if not self._is_admin(message):
            await message.reply_text("❌ Only admin can manage sessions.")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.reply_text(
                "❌ **Usage:**\n"
                "/delsession <session_id>",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        session_id = args[1]
        
        if self.session_manager.delete_session(session_id):
            await message.reply_text(f"✅ Session '{session_id}' deleted.")
        else:
            await message.reply_text(f"❌ Session '{session_id}' not found.")
    
    async def getip_command(self, client: Client, message: Message):
        """Handle /getip command."""
        args = message.text.split()
        if len(args) < 2:
            await message.reply_text(
                "❌ **Usage:**\n"
                "/getip <session_id>\n\n"
                "**Example:**\n"
                "/getip S10",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        session_id = args[1]
        session = self.session_manager.get_session(session_id)
        
        if not session:
            await message.reply_text(f"❌ Session '{session_id}' not found.")
            return
        
        # Show extracting status
        status_msg = await message.reply_text(
            f"🔄 **Extracting IP from {session_id}...**\n"
            f"📡 Chat: {session['chat_name']}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Extract IP
            ip, port = await self.ip_grabber.extract_ip_from_chat(
                session["chat_id"],
                session_id
            )
            
            if ip and port:
                # Update session with IP
                self.session_manager.update_session_ip(session_id, ip, port)
                
                # Format response with copy button
                response = format_session_info(session_id, session["chat_name"], ip, port)
                
                await status_msg.delete()
                await message.reply_text(
                    response,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📋 Copy IP", callback_data=f"copy:{session_id}")]
                    ])
                )
            else:
                await status_msg.edit_text(
                    f"❌ **No IP extracted from {session_id}**\n\n"
                    f"💡 Tips:\n"
                    f"• Make sure the voice chat is active\n"
                    f"• Check if the bot has access to the chat\n"
                    f"• Try using /extract {session['chat_id']} directly",
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            error_trace = traceback.format_exc()
            LOGGER.error(f"Error in getip: {error_trace}")
            await status_msg.edit_text(
                f"❌ **Error:** {str(e)}\n\n"
                f"Check logs for more details.",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def extract_command(self, client: Client, message: Message):
        """Handle /extract command - direct extraction without session."""
        args = message.text.split()
        if len(args) < 2:
            await message.reply_text(
                "❌ **Usage:**\n"
                "/extract <chat_id>\n\n"
                "**Example:**\n"
                "/extract -1003329480093",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        chat_id = int(args[1])
        chat_info = await self.ip_grabber.get_chat_info(chat_id)
        
        if not chat_info:
            await message.reply_text("❌ Could not get chat information.")
            return
        
        status_msg = await message.reply_text(
            f"🔄 **Extracting IP from {chat_info['title']}...**",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            ip, port = await self.ip_grabber.extract_ip_from_chat(chat_id, "temp")
            
            if ip and port:
                await status_msg.delete()
                await message.reply_text(
                    f"🎯 **IP Extracted**\n\n"
                    f"**Chat:** {chat_info['title']}\n"
                    f"**IP:** {ip}\n"
                    f"**Port:** {port}\n\n"
                    f"Add this as a session:\n"
                    f"`/addsession S{len(self.session_manager.get_all_sessions()) + 1} {chat_id} {chat_info['title']}`",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await status_msg.edit_text(
                    f"❌ **No IP extracted from {chat_info['title']}**\n\n"
                    f"Make sure the voice chat is active.",
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            LOGGER.error(f"Error in extract: {e}")
            await status_msg.edit_text(f"❌ **Error:** {str(e)}")
    
    async def callback_handler(self, client: Client, callback_query: CallbackQuery):
        """Handle callback queries."""
        data = callback_query.data
        
        if data.startswith("view_session:"):
            session_id = data.split(":")[1]
            session = self.session_manager.get_session(session_id)
            
            if not session:
                await callback_query.answer("Session not found!", show_alert=True)
                return
            
            text = f"""📱 **Session: {session_id}**

**Chat:** {session['chat_name']}
**Chat ID:** {session['chat_id']}
**IP:** {session.get('ip', 'Not set')}
**Port:** {session.get('port', 'Not set')}
**Created:** {session.get('created_at', 'Unknown')}
**Last Extracted:** {session.get('last_extracted', 'Never')}

Use /getip {session_id} to extract IP."""
            
            await callback_query.message.edit_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Extract IP", callback_data=f"extract:{session_id}")],
                    [InlineKeyboardButton("📋 Copy IP", callback_data=f"copy:{session_id}")],
                    [InlineKeyboardButton("🗑️ Delete", callback_data=f"delete:{session_id}")],
                    [InlineKeyboardButton("◀️ Back", callback_data="back_to_sessions")]
                ])
            )
            await callback_query.answer()
        
        elif data.startswith("extract:"):
            session_id = data.split(":")[1]
            await callback_query.answer("Extracting IP...")
            # Trigger IP extraction
            await callback_query.message.reply_text(f"🔄 Extracting IP from {session_id}...")
            # Call getip logic
            # This is a simplified version - you'd want to reuse the getip logic
            session = self.session_manager.get_session(session_id)
            if session:
                ip, port = await self.ip_grabber.extract_ip_from_chat(session["chat_id"], session_id)
                if ip and port:
                    self.session_manager.update_session_ip(session_id, ip, port)
                    await callback_query.message.reply_text(
                        f"✅ IP Extracted: {ip}:{port}",
                        parse_mode=ParseMode.MARKDOWN
                    )
        
        elif data.startswith("copy:"):
            session_id = data.split(":")[1]
            session = self.session_manager.get_session(session_id)
            
            if session and session.get("ip"):
                copy_text = f"{session['ip']}:{session['port']}"
                await callback_query.answer(f"📋 Copied: {copy_text}", show_alert=True)
            else:
                await callback_query.answer("No IP to copy!", show_alert=True)
        
        elif data.startswith("delete:"):
            if not self._is_admin(callback_query.message):
                await callback_query.answer("Only admin can delete!", show_alert=True)
                return
            
            session_id = data.split(":")[1]
            if self.session_manager.delete_session(session_id):
                await callback_query.answer(f"✅ Session {session_id} deleted")
                await callback_query.message.delete()
            else:
                await callback_query.answer("Session not found!", show_alert=True)
        
        elif data == "back_to_sessions":
            await self.sessions_command(client, callback_query.message)
            await callback_query.answer()
        
        elif data == "refresh_list":
            await self.sessions_command(client, callback_query.message)
            await callback_query.answer()
    
    def _is_admin(self, message: Message) -> bool:
        """Check if message is from admin."""
        return message.from_user.id == self.admin_id

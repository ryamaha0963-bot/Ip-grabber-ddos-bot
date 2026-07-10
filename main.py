"""Main entry point for IP Grabber Bot - Railway Deployment."""

import asyncio
import logging
import sys
import os

from pyrogram import Client, idle

from config import Config
from session_manager import SessionManager
from ip_grabber import IPGrabber
from bot_handler import IPGrabberBot


def setup_logging():
    """Setup application logging."""
    # Create logs directory
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/bot.log", encoding="utf-8")
        ]
    )
    logging.getLogger("pyrogram").setLevel(logging.WARNING)


async def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    LOGGER = logging.getLogger(__name__)
    
    # Load configuration
    try:
        config = Config.from_env()
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\nRequired environment variables:")
        print("- API_ID")
        print("- API_HASH")
        print("- BOT_TOKEN")
        print("- SESSION_STRING")
        print("- ADMIN_ID")
        return 1
    
    LOGGER.info("🚀 Starting IP Grabber Bot on Railway...")
    LOGGER.info(f"Bot Token: {config.bot_token[:10]}...")
    
    # Initialize bot client
    bot = Client(
        "ip_grabber_bot",
        api_id=config.api_id,
        api_hash=config.api_hash,
        bot_token=config.bot_token,
        workdir="./"
    )
    
    # Initialize user client
    user = Client(
        "ip_grabber_user",
        api_id=config.api_id,
        api_hash=config.api_hash,
        session_string=config.session_string,
        workdir="./"
    )
    
    # Create data directory for persistent storage
    if not os.path.exists("data"):
        os.makedirs("data")
        LOGGER.info("📁 Created data directory")
    
    # Initialize components
    session_manager = SessionManager("data/sessions.json")
    ip_grabber = IPGrabber(user)
    
    # Start clients
    LOGGER.info("🔄 Starting bot client...")
    await bot.start()
    LOGGER.info("✅ Bot client started")
    
    LOGGER.info("🔄 Starting user client...")
    await user.start()
    LOGGER.info("✅ User client started")
    
    # Initialize bot handler
    bot_handler = IPGrabberBot(
        bot=bot,
        user_client=user,
        session_manager=session_manager,
        ip_grabber=ip_grabber,
        admin_id=config.admin_id
    )
    
    # Send startup notification to admin
    try:
        await bot.send_message(
            config.admin_id,
            f"✅ **IP Grabber Bot Started!**\n\n"
            f"**Platform:** 🚀 Railway\n"
            f"**Status:** Online 🟢\n"
            f"**Active Sessions:** {session_manager.get_active_sessions_count()}\n"
            f"**Admin ID:** {config.admin_id}\n\n"
            f"Use /help for commands.",
            parse_mode="markdown"
        )
        LOGGER.info("✅ Startup notification sent to admin")
    except Exception as e:
        LOGGER.warning(f"⚠️ Failed to send startup notification: {e}")
    
    LOGGER.info("✅ Bot is running on Railway. Press Ctrl+C to stop.")
    
    try:
        # Keep the bot running
        await idle()
    except KeyboardInterrupt:
        LOGGER.info("🛑 Keyboard interrupt received")
    finally:
        LOGGER.info("🔄 Shutting down...")
        await bot.stop()
        await user.stop()
        LOGGER.info("✅ Shutdown complete")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

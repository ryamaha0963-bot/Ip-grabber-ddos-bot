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
    # Create logs directory if it doesn't exist
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
    # Setup
    setup_logging()
    LOGGER = logging.getLogger(__name__)
    
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
    
    # Initialize clients
    bot = Client(
        "ip_grabber_bot",
        api_id=config.api_id,
        api_hash=config.api_hash,
        bot_token=config.bot_token,
        workdir="./"
    )
    
    user = Client(
        "ip_grabber_user",
        api_id=config.api_id,
        api_hash=config.api_hash,
        session_string=config.session_string,
        workdir="./"
    )
    
    # Initialize components
    session_manager = SessionManager("data/sessions.json")
    ip_grabber = IPGrabber(user)
    
    # Ensure data directory exists
    if not os.path.exists("data"):
        os.makedirs("data")
    
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
    
    # Send startup message
    try:
        await bot.send_message(
            config.admin_id,
            "✅ **IP Grabber Bot Started!**\n\n"
            f"**Platform:** Railway\n"
            f"**Active Sessions:** {session_manager.get_active_sessions_count()}\n"
            f"**Bot Status:** Online 🟢\n\n"
            "Use /help for commands.",
            parse_mode="markdown"
        )
        LOGGER.info("✅ Startup message sent to admin")
    except Exception as e:
        LOGGER.warning(f"Failed to send startup message: {e}")
    
    LOGGER.info("✅ Bot is running on Railway. Press Ctrl+C to stop.")
    
    try:
        await idle()
    except KeyboardInterrupt:
        LOGGER.info("🛑 Keyboard interrupt received")
    finally:
        LOGGER.info("🔄 Shutting down...")
        await bot.stop()
        await user.stop()
        LOGGER.info("✅ Shutdown complete")
    
    return 0


def run():
    """Run the application."""
    # Use uvloop on Linux (Railway uses Linux)
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        print("✓ Using uvloop for better performance")
    except ImportError:
        pass
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run()

"""
Main Telegram bot application for COPE Referral Bot
Integrates all components with wallet-referrer mapping logic
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
import re

from config import TELEGRAM_BOT_TOKEN
from database.db_manager import DatabaseManager
from bot.handlers import BotHandlers
from bot.trade_handlers import TradeHandlers
from chain.event_listener import COPEEventListener
from rewards.distribution import RewardDistributor
import schedule
import threading


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class COPEReferralBot:
    """Main bot application"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.handlers = BotHandlers(self.db)
        self.trade_handlers = TradeHandlers(self.db)
        self.event_listener = None
        self.distributor = RewardDistributor(self.db)
        self.application = None
    
    async def initialize(self):
        """Initialize database and components"""
        logger.info("Initializing COPE Referral Bot...")
        await self.db.init_db()
        logger.info("Database initialized")
        
        # Initialize event listener
        self.event_listener = COPEEventListener(self.db)
        await self.event_listener.initialize()
        logger.info("Event listener initialized")
    
    def setup_handlers(self):
        """Setup Telegram bot command handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.handle_start))
        self.application.add_handler(CommandHandler("connect", self.handlers.connect_command))
        self.application.add_handler(CommandHandler("connect_manual", self.handlers.connect_manual_command))
        self.application.add_handler(CommandHandler("referral", self.handlers.referral_command))
        self.application.add_handler(CommandHandler("stats", self.handlers.stats_command))
        self.application.add_handler(CommandHandler("leaderboard", self.handlers.leaderboard_command))
        self.application.add_handler(CommandHandler("rules", self.handlers.rules_command))
        self.application.add_handler(CommandHandler("claim", self.handlers.claim_command))
        self.application.add_handler(CommandHandler("withdraw", self.handlers.withdraw_command))
        self.application.add_handler(CommandHandler("buy", self.trade_handlers.trade_command))
        self.application.add_handler(CommandHandler("sell", self.trade_handlers.trade_command))
        
        # Message handlers (for signature and wallet address)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        # Callback query handlers (for inline buttons)
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
    
    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with optional referral code"""
        if context.args and context.args[0].startswith('ref_'):
            await self.handlers.handle_referral_start(update, context)
        else:
            await self.handlers.start_command(update, context)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages (signatures, wallet addresses, and WebApp data)"""
        # Check for WebApp data (from wallet connection)
        if update.message.web_app_data:
            await self.handlers.handle_webapp_data(update, context)
            return
        
        text = update.message.text.strip()
        
        # Check if it looks like a signature (hex string, typically 132 chars with 0x)
        if re.match(r'^0x[a-fA-F0-9]{130}$', text):
            await self.handlers.handle_signature(update, context)
        # Check if it looks like a wallet address
        elif re.match(r'^0x[a-fA-F0-9]{40}$', text):
            await self.handlers.handle_wallet_address(update, context)
        else:
            # Not a signature or address, ignore or provide help
            await update.message.reply_text(
                "❓ I didn't understand that. Use /connect to link your wallet or /help for commands."
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "stats":
            # Redirect to stats command
            await self.handlers.stats_command(update, context)
        elif query.data.startswith("copy_"):
            await query.answer("📋 Link copied! Share it with others.", show_alert=False)
        elif query.data.startswith("trade_"):
            await self.trade_handlers.handle_callback(update, context)
    
    def start_event_listener(self):
        """Start the BNB Chain event listener in background"""
        if self.event_listener:
            asyncio.create_task(self.event_listener.listen_for_events())
            logger.info("Event listener started")
    
    def setup_weekly_distribution(self):
        """Setup weekly reward distribution scheduler"""
        def run_distribution():
            """Run weekly distribution (call from scheduler thread)"""
            from datetime import datetime
            from config import WEEKLY_DISTRIBUTION_DAY, WEEKLY_DISTRIBUTION_HOUR
            
            # Calculate current period
            now = datetime.utcnow()
            distributor = RewardDistributor(self.db)
            period_start, period_end = distributor.calculate_weekly_period(now)
            
            # Run distribution
            asyncio.run(distributor.settle_weekly_rewards(period_start, period_end))
        
        # Schedule weekly distribution (every Monday at midnight UTC)
        schedule.every().monday.at("00:00").do(run_distribution)
        
        # Start scheduler in background thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                threading.Event().wait(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Weekly distribution scheduler started")
    
    async def run(self):
        """Run the bot"""
        # Initialize
        await self.initialize()
        
        # Create application
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).connect_timeout(30.0).read_timeout(30.0).build()
        
        # Setup handlers
        self.setup_handlers()
        
        # Start event listener
        self.start_event_listener()
        
        # Setup weekly distribution
        self.setup_weekly_distribution()
        
        # Start bot
        logger.info("Starting Telegram bot...")
        
        # Keep running

        try:
            async with self.application:
                await self.application.start()
                await self.application.updater.start_polling(drop_pending_updates=True)
                logger.info("COPE Referral Bot is running!")
                
                # Keep running until interrupted
                await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            if self.event_listener:
                self.event_listener.stop()


async def main():
    """Main entry point"""
    bot = COPEReferralBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())


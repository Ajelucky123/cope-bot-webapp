"""
Configuration file for COPE Telegram Referral Bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Token Details (Fixed Constants)
TOKEN_NAME = "COPE"
TOKEN_SYMBOL = "COPE"
TOKEN_CONTRACT = "0x14EB783EE20eD7970Ad5e008044002d2c71D9148"
CHAIN = "BNB Chain"

# BNB Chain RPC Configuration
BNB_CHAIN_RPC_URL = os.getenv("BNB_CHAIN_RPC_URL", "https://bsc-dataseed1.binance.org/")
BNB_CHAIN_RPC_WS_URL = os.getenv("BNB_CHAIN_RPC_WS_URL", "wss://bsc-ws-node.nariox.org:443")

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "database/cope_bot.db")

# Web App Configuration
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://ajelucky123.github.io/cope-bot-webapp/index.html")

# Reward Configuration
REFERRAL_REWARD_PERCENTAGE = 0.5  # 50% to referrer
COMMUNITY_POOL_PERCENTAGE = 0.5   # 50% to community pool
MIN_WITHDRAWAL_THRESHOLD = 100000  # 100,000 COPE minimum
COMMUNITY_POOL_UNLOCK_MCAP = 1000000  # 1,000,000 market cap

# Weekly Distribution
WEEKLY_DISTRIBUTION_DAY = 0  # Monday (0 = Monday, 6 = Sunday)
WEEKLY_DISTRIBUTION_HOUR = 0  # Midnight UTC

# Approved Liquidity Pools (add actual pool addresses)
APPROVED_LIQUIDITY_POOLS = [
    "0x7d39a0cfe597a92BEd702844d42B063204Ed4d85"
]

# Merkle Tree Configuration
MERKLE_TREE_DEPTH = 20

# Bot Messages
BOT_MESSAGES = {
    "welcome": "Welcome to COPE Referral Bot! 🚀\n\nUse /connect to register your wallet and start earning.",
    "wallet_connected": "✅ Wallet connected successfully!",
    "referral_link_generated": "🔗 Your referral link has been generated!",
    "no_wallet": "❌ Please connect your wallet first using /connect",
    "self_referral_error": "❌ You cannot refer yourself!",
    "wallet_already_mapped": "⚠️ This wallet is already mapped to a referrer.",
    "mapping_locked": "🔒 This wallet's referrer mapping is locked after first trade.",
}


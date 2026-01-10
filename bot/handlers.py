"""
Telegram bot command handlers for COPE Referral Bot
Implements all bot commands with wallet-referrer mapping logic
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from typing import Optional
import re
import os
import json
import logging

from database.db_manager import DatabaseManager
from utils.wallet_verification import (
    generate_verification_message, 
    verify_signature,
    generate_referral_code,
    format_wallet_address
)
from config import (
    TOKEN_NAME, TOKEN_SYMBOL, TOKEN_CONTRACT, CHAIN,
    MIN_WITHDRAWAL_THRESHOLD, BOT_MESSAGES
)

logger = logging.getLogger(__name__)


class BotHandlers:
    """Handles all Telegram bot commands"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - Initialize user"""
        user = update.effective_user
        await self.db.create_user(user.id, user.username)
        
        welcome_msg = f"""🚀 Welcome to {TOKEN_NAME} Referral Bot!

This bot helps you earn rewards by referring others to trade {TOKEN_NAME} on {CHAIN}.

**How it works:**
• Connect your wallet
• Share your referral link
• Earn 50% of COPE tax from referred wallets
• Withdraw rewards weekly (min 100,000 COPE)

Use /connect to link your wallet and get started!"""
        
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')
    
    async def connect_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /connect command - Direct wallet address input"""
        user = update.effective_user
        await self.db.create_user(user.id, user.username)
        
        # Check if wallet already connected
        existing_wallet = await self.db.get_wallet_by_telegram_id(user.id)
        if existing_wallet:
            await update.message.reply_text(
                f"✅ Wallet already connected: `{format_wallet_address(existing_wallet)}`\n\n"
                f"Use /referral to get your referral link!",
                parse_mode='Markdown'
            )
            return
        
        message_text = """🚀 **Connect Your Wallet**

To participate in the COPE Referral program, please send your **BNB Chain (BSC) wallet address** (starting with 0x).

**Benefits:**
✅ Earn 50% of trade tax from your referrals
✅ Weekly payouts in COPE
✅ Simple registration, no signature required!

*Please make sure you send the correct address. Rewards are distributed to this wallet.*"""
        
        await update.message.reply_text(
            message_text, 
            parse_mode='Markdown'
        )
        # Set state to wait for address
        context.user_data['waiting_for_address'] = True
    
    async def connect_manual_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /connect_manual command - Manual wallet connection via signature"""
        user = update.effective_user
        await self.db.create_user(user.id, user.username)
        
        # Check if wallet already connected
        existing_wallet = await self.db.get_wallet_by_telegram_id(user.id)
        if existing_wallet:
            await update.message.reply_text(
                f"✅ Wallet already connected: `{format_wallet_address(existing_wallet)}`\n\n"
                f"Use /referral to get your referral link!",
                parse_mode='Markdown'
            )
            return
        
        # Generate verification message
        message, nonce = generate_verification_message(user.id)
        
        instructions = f"""🔐 **Manual Wallet Connection**

1. Copy the message below
2. Sign it with your wallet (MetaMask, Trust Wallet, etc.)
3. Send the signature back here

**Message to sign:**
```
{message}
```

**How to sign:**
• MetaMask: Settings → Advanced → Show Hex Data → Sign Message
• Trust Wallet: Settings → Wallet → Sign Message
• Other wallets: Look for "Sign Message" feature

After signing, send your signature here."""
        
        await update.message.reply_text(instructions, parse_mode='Markdown')
        
        # Store nonce in context for verification
        context.user_data['pending_signature'] = {
            'message': message,
            'nonce': nonce
        }
    
    async def handle_signature(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle wallet signature submission"""
        user = update.effective_user
        signature = update.message.text.strip()
        
        # Check if we're expecting a signature
        pending = context.user_data.get('pending_signature')
        if not pending:
            await update.message.reply_text(
                "❌ No pending signature request. Use /connect to start wallet connection."
            )
            return
        
        # Ask for wallet address
        await update.message.reply_text(
            "✅ Signature received! Now please send your wallet address (0x...)"
        )
        context.user_data['pending_signature']['signature'] = signature
        context.user_data['pending_signature']['step'] = 'waiting_address'
    
    async def handle_wallet_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle direct wallet address submission"""
        user = update.effective_user
        wallet_address = update.message.text.strip().lower()
        
        # Validate address format
        if not re.match(r'^0x[a-fA-F0-9]{40}$', wallet_address):
            # Only reply if we were explicitly waiting for an address
            if context.user_data.get('waiting_for_address') or context.user_data.get('pending_signature'):
                await update.message.reply_text(
                    "❌ Invalid wallet address format. Please send a valid BSC address (0x...)."
                )
            return

        # Check if we are handling a manual signature flow (legacy) or direct registration
        pending = context.user_data.get('pending_signature')
        is_legacy_flow = pending and pending.get('step') == 'waiting_address'
        is_direct_flow = context.user_data.get('waiting_for_address')

        if not is_legacy_flow and not is_direct_flow:
            # Not in a connection flow, ignore
            return
        
        # Registration data
        signature = pending['signature'] if is_legacy_flow else None
        message = pending['message'] if is_legacy_flow else "Direct Registration"
        
        # Verify signature if it's the legacy flow
        if is_legacy_flow and not verify_signature(message, signature, wallet_address):
            await update.message.reply_text(
                "❌ Signature verification failed. Please try again with /connect."
            )
            context.user_data.pop('pending_signature', None)
            return
        
        # Connect wallet
        success = await self.db.connect_wallet(user.id, wallet_address, signature, message)
        if not success:
            await update.message.reply_text(
                "❌ This wallet is already connected to another Telegram account."
            )
            context.user_data.pop('pending_signature', None)
            context.user_data.pop('waiting_for_address', None)
            return
        
        # Check if user came from a referral link
        referrer_code = context.user_data.get('referrer_code')
        if referrer_code:
            # Get referrer wallet from code
            referrer_wallet = await self.db.get_wallet_by_referral_code(referrer_code)
            if referrer_wallet:
                # Prevent self-referral
                if referrer_wallet.lower() != wallet_address.lower():
                    # Create wallet-referrer mapping
                    mapping_success = await self.db.create_referral_mapping(
                        wallet_address, referrer_wallet
                    )
                    if mapping_success:
                        await update.message.reply_text(
                            f"✅ {BOT_MESSAGES['wallet_connected']}\n\n"
                            f"Wallet: `{format_wallet_address(wallet_address)}`\n\n"
                            f"🎉 You've been referred! Your wallet is now mapped to your referrer.\n"
                            f"All your future COPE trades will credit rewards to them.\n\n"
                            f"Use /referral to get your own referral link!",
                            parse_mode='Markdown'
                        )
                    else:
                        await update.message.reply_text(
                            f"✅ {BOT_MESSAGES['wallet_connected']}\n\n"
                            f"Wallet: `{format_wallet_address(wallet_address)}`\n\n"
                            f"⚠️ Could not create referral mapping (wallet may already be mapped).\n\n"
                            f"Use /referral to get your referral link!",
                            parse_mode='Markdown'
                        )
                else:
                    await update.message.reply_text(
                        f"✅ {BOT_MESSAGES['wallet_connected']}\n\n"
                        f"Wallet: `{format_wallet_address(wallet_address)}`\n\n"
                        f"⚠️ Self-referral prevented.\n\n"
                        f"Use /referral to get your referral link!",
                        parse_mode='Markdown'
                    )
                context.user_data.pop('referrer_code', None)
            else:
                await update.message.reply_text(
                    f"✅ {BOT_MESSAGES['wallet_connected']}\n\n"
                    f"Wallet: `{format_wallet_address(wallet_address)}`\n\n"
                    f"Use /referral to get your referral link!",
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(
                f"✅ {BOT_MESSAGES['wallet_connected']}\n\n"
                f"Wallet: `{format_wallet_address(wallet_address)}`\n\n"
                f"Use /referral to get your referral link!",
                parse_mode='Markdown'
            )
        context.user_data.pop('pending_signature', None)
    
    async def handle_webapp_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle wallet connection data from WebApp"""
        user = update.effective_user
        
        try:
            # Parse WebApp data
            data_str = update.message.web_app_data.data
            data = json.loads(data_str)
            
            wallet_address = data.get('walletAddress', '').strip()
            signature = data.get('signature', '').strip()
            message = data.get('message', '')
            telegram_id = data.get('telegramId')
            
            # Verify Telegram ID matches
            if telegram_id and int(telegram_id) != user.id:
                await update.message.reply_text(
                    "❌ Security error: Telegram ID mismatch. Please try again."
                )
                return
            
            # Validate wallet address
            if not re.match(r'^0x[a-fA-F0-9]{40}$', wallet_address):
                await update.message.reply_text(
                    "❌ Invalid wallet address format."
                )
                return
            
            # Verify signature
            if not verify_signature(message, signature, wallet_address):
                await update.message.reply_text(
                    "❌ Signature verification failed. Please try again."
                )
                return
            
            # Connect wallet
            success = await self.db.connect_wallet(user.id, wallet_address, signature, message)
            if not success:
                await update.message.reply_text(
                    "❌ This wallet is already connected to another Telegram account."
                )
                return
            
            # Check if user came from a referral link
            referrer_code = context.user_data.get('referrer_code')
            if referrer_code:
                # Get referrer wallet from code
                referrer_wallet = await self.db.get_wallet_by_referral_code(referrer_code)
                if referrer_wallet:
                    # Prevent self-referral
                    if referrer_wallet.lower() != wallet_address.lower():
                        # Create wallet-referrer mapping
                        mapping_success = await self.db.create_referral_mapping(
                            wallet_address, referrer_wallet
                        )
                        if mapping_success:
                            await update.message.reply_text(
                                f"✅ {BOT_MESSAGES['wallet_connected']}\n\n"
                                f"Wallet: `{format_wallet_address(wallet_address)}`\n\n"
                                f"🎉 You've been referred! Your wallet is now mapped to your referrer.\n"
                                f"All your future COPE trades will credit rewards to them.\n\n"
                                f"Use /referral to get your own referral link!",
                                parse_mode='Markdown'
                            )
                            context.user_data.pop('referrer_code', None)
                            return
            
            await update.message.reply_text(
                f"✅ {BOT_MESSAGES['wallet_connected']}\n\n"
                f"Wallet: `{format_wallet_address(wallet_address)}`\n\n"
                f"Use /referral to get your referral link!",
                parse_mode='Markdown'
            )
            
        except json.JSONDecodeError:
            await update.message.reply_text(
                "❌ Invalid data received. Please try connecting again with /connect."
            )
        except Exception as e:
            logger.error(f"Error handling WebApp data: {e}")
            await update.message.reply_text(
                "❌ An error occurred. Please try again with /connect."
            )
    
    async def referral_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /referral command - Generate referral link"""
        user = update.effective_user
        
        # Check if wallet is connected
        wallet_address = await self.db.get_wallet_by_telegram_id(user.id)
        if not wallet_address:
            await update.message.reply_text(BOT_MESSAGES['no_wallet'])
            return
        
        # Get or create referral code
        referral_code = await self.db.get_or_create_referral_code(wallet_address)
        referral_link = f"https://t.me/{context.bot.username}?start=ref_{referral_code}"
        
        message = f"""🔗 **Your Referral Link**

```
{referral_link}
```

**How it works:**
1. Share this link with others
2. When they connect their wallet and trade {TOKEN_NAME}, you earn 50% of the tax
3. Their wallet is permanently mapped to you as referrer
4. All their future trades credit rewards to you

**Token Contract:** `{TOKEN_CONTRACT}`
**Chain:** {CHAIN}

Share your link and start earning! 🚀"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_{referral_code}")],
            [InlineKeyboardButton("📊 View Stats", callback_data="stats")]
        ])
        
        await update.message.reply_text(message, parse_mode='Markdown', reply_markup=keyboard)
    
    async def handle_referral_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle referral link clicks (/start with referral code)"""
        user = update.effective_user
        args = context.args
        
        if not args or not args[0].startswith('ref_'):
            await self.start_command(update, context)
            return
        
        # Extract referrer code
        referrer_code = args[0][4:]  # Remove 'ref_' prefix
        
        # Get referrer wallet from code (simplified - in production, store code->wallet mapping)
        # For now, we'll need to find wallet by code or use a different approach
        # This is a simplified version - you may want to store referral codes in DB
        
        await update.message.reply_text(
            f"👋 Welcome! You were referred by someone.\n\n"
            f"Use /connect to link your wallet and start trading {TOKEN_NAME}!\n\n"
            f"Note: Your referrer will be assigned when you connect your wallet."
        )
        
        # Store referrer code for later mapping
        context.user_data['referrer_code'] = referrer_code
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command - Show referral statistics"""
        user = update.effective_user
        
        # Check if wallet is connected
        wallet_address = await self.db.get_wallet_by_telegram_id(user.id)
        if not wallet_address:
            # If handled via callback query, answer the query with an alert
            if update.callback_query:
                # Use a specific message or default
                msg = BOT_MESSAGES.get('no_wallet', "❌ Please connect your wallet first.")
                try:
                    await update.callback_query.answer(msg, show_alert=True)
                except Exception:
                    # Already answered, just reply
                    await update.callback_query.message.reply_text(msg)
            else:
                await update.message.reply_text(BOT_MESSAGES['no_wallet'])
            return
        
        # Get stats
        stats = await self.db.get_referral_stats(wallet_address)
        
        status_emoji = "✅" if stats['withdrawable'] else "⏳"
        status_text = "Eligible" if stats['withdrawable'] else "Below threshold"
        
        message = f"""📊 **Your Referral Stats**

👤 **Referrals:** {stats['referred_count']} active wallets
📈 **Trade Volume:** {stats['total_volume']:,.2f} {TOKEN_SYMBOL}
💰 **Accrued Reward:** {stats['accrued_rewards']:,.2f} {TOKEN_SYMBOL}

🏦 **Withdraw Status:** {status_emoji} {status_text}
📉 **Min. Threshold:** {MIN_WITHDRAWAL_THRESHOLD:,} {TOKEN_SYMBOL}

*Note: Rewards are calculated based on 50% of the COPE trade tax generated by your referrals.*"""
        
        # If this was triggered by a button click (CallbackQuery)
        if update.callback_query:
            try:
                await update.callback_query.edit_message_text(message, parse_mode='Markdown')
            except Exception:
                # If message is the same or can't be edited, just reply
                await update.callback_query.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(message, parse_mode='Markdown')
    
    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /leaderboard command - Show top referrers"""
        leaderboard = await self.db.get_leaderboard(limit=10)
        
        if not leaderboard:
            await update.message.reply_text("📊 No referrals yet. Be the first!")
            return
        
        message = "🏆 **Top Referrers**\n\n"
        for i, (wallet, rewards, count) in enumerate(leaderboard, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            message += f"{medal} `{format_wallet_address(wallet)}`\n"
            message += f"   Rewards: {rewards:,.2f} {TOKEN_SYMBOL}\n"
            message += f"   Referrals: {count}\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def rules_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /rules command - Plain-English explanation"""
        message = f"""📖 **{TOKEN_NAME} Referral Bot Rules**

**How Referrals Work:**
• Connect your wallet to get a unique referral link
• When someone uses your link and connects their wallet, they become your referral
• Their wallet is **permanently mapped** to you as referrer
• Mapping is **locked on first trade** - cannot be changed

**Rewards:**
• You earn **50% of COPE tax** from all trades by referred wallets
• The other **50% goes to Community Tax Pool**
• Rewards are denominated in {TOKEN_SYMBOL} tokens
• Rewards accrue off-chain and settle weekly

**Withdrawal:**
• Minimum withdrawal: **{MIN_WITHDRAWAL_THRESHOLD:,} {TOKEN_SYMBOL}**
• Rewards below threshold roll over to next cycle
• Weekly distribution via Merkle tree claims

**Community Pool:**
• Unlocks when {TOKEN_NAME} reaches **1,000,000 market cap**
• Distributed pro-rata to wallets with trading activity
• Passive holders excluded

**Protections:**
• Self-referral is prevented
• Referrer assignment is permanent after first trade
• No minimum trade size or frequency caps

**Token Contract:** `{TOKEN_CONTRACT}`
**Chain:** {CHAIN}"""
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def claim_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /claim command - Claim status & next distribution"""
        user = update.effective_user
        
        wallet_address = await self.db.get_wallet_by_telegram_id(user.id)
        if not wallet_address:
            await update.message.reply_text(BOT_MESSAGES['no_wallet'])
            return
        
        # Get stats
        stats = await self.db.get_referral_stats(wallet_address)
        
        # Calculate next distribution (simplified - in production, calculate actual next Monday)
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0 and now.hour < 0:  # If it's Monday before midnight
            days_until_monday = 0
        else:
            days_until_monday = days_until_monday if days_until_monday > 0 else 7
        next_distribution = now + timedelta(days=days_until_monday)
        next_distribution = next_distribution.replace(hour=0, minute=0, second=0, microsecond=0)
        
        message = f"""💰 **Claim Status**

**Wallet:** `{format_wallet_address(wallet_address)}`

**Accrued Rewards:** {stats['accrued_rewards']:,.2f} {TOKEN_SYMBOL}

**Withdrawal Eligibility:** {'✅ Eligible' if stats['withdrawable'] else '⏳ Below threshold'}

**Next Distribution:** {next_distribution.strftime('%Y-%m-%d %H:%M UTC')}

**How to Claim:**
1. Wait for weekly distribution
2. If eligible (≥{MIN_WITHDRAWAL_THRESHOLD:,} {TOKEN_SYMBOL}), claim on-chain
3. Merkle root will be updated weekly

Check back after the distribution period!"""
        
        await update.message.reply_text(message, parse_mode='Markdown')

    async def withdraw_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /withdraw command - check eligibility and instructions"""
        user = update.effective_user
        
        # Check if wallet is connected
        wallet_address = await self.db.get_wallet_by_telegram_id(user.id)
        if not wallet_address:
            await update.message.reply_text(BOT_MESSAGES['no_wallet'])
            return
            
        # Get current stats (unsettled)
        stats = await self.db.get_referral_stats(wallet_address)
        # Get settled rewards (ready for claim)
        settled_total = await self.db.get_settled_rewards_total(wallet_address)
        
        status_emoji = "✅" if stats['withdrawable'] else "⏳"
        eligibility = "Eligible for next settlement" if stats['withdrawable'] else "Below minimum threshold"
        
        message = f"""💰 **COPE Withdrawal & Rewards**

🏦 **Settled Rewards:** `{settled_total:,.2f} {TOKEN_SYMBOL}`
*These have been finalized in previous cycles and are available for on-chain claim.*

⏳ **Accrued (This Cycle):** `{stats['accrued_rewards']:,.2f} {TOKEN_SYMBOL}`
*These will be settled in the next weekly distribution (Every Monday 00:00 UTC).*

📊 **Status:** {status_emoji} {eligibility}
📉 **Min. Threshold:** `{MIN_WITHDRAWAL_THRESHOLD:,} {TOKEN_SYMBOL}`

**How to Claim:**
1. Wait for the weekly settlement (Monday).
2. If your Accrued Rewards exceed the threshold, they will be added to the Merkle tree.
3. Once settled, you can claim them on-chain using the claim portal (URL coming soon).

_Note: Self-referrals are excluded from rewards._"""
        
        await update.message.reply_text(message, parse_mode='Markdown')


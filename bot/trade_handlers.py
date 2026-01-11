"""
Trade handlers for COPE Telegram Bot
Implements Buy and Sell modes with UI logic matching the screenshot
"""
import logging
import asyncio
from typing import Dict, Optional, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import (
    TOKEN_CONTRACT, DEX_NAME, BSC_SCAN_URL, DEX_SCREENER_URL,
    DEFAULT_GAS_SETTINGS, DEFAULT_BUY_AMOUNTS, DEFAULT_SELL_AMOUNTS
)
from database.db_manager import DatabaseManager
from chain.token_utils import TokenUtils

import html

logger = logging.getLogger(__name__)

class TradeHandlers:
    """Handles /buy, /sell and associated trading interface logic"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.token_utils = TokenUtils()
        # In-memory session state for users (simple version)
        # In prod, this should be in DB if it needs to persist across reboots
        self.user_sessions = {} # telegram_id -> {mode, gas, amount_selection, etc}

    def _get_user_session(self, user_id: int):
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                "mode": "buy",
                "gas": "1.1",
                "amount": "0.1", # Default amount selection
                "wallet_index": 1
            }
        self.user_sessions[user_id]["amount"] = self.user_sessions[user_id].get("amount", "0.1")
        return self.user_sessions[user_id]

    async def _format_trade_message(self, user_id: int, token_data: Dict, balances: Dict) -> str:
        session = self._get_user_session(user_id)
        mode = session["mode"].upper()
        
        # Format currency/numbers
        try:
            price = float(token_data.get("price", 0))
            mcap = float(token_data.get("mcap", 0))
            liquidity = float(token_data.get("liquidity", 0))
        except (ValueError, TypeError):
            price = mcap = liquidity = 0.0

        name = html.escape(token_data.get('name', 'Unknown'))
        symbol = html.escape(token_data.get('symbol', 'TOKEN'))
        
        message = (
            f"🟢 {mode} MODE 🟢\n\n"
            f"🌕 {name} • ${symbol}\n"
            f"<code>{token_data['address']}</code>\n"
            f"Dex: {html.escape(token_data.get('dex', 'Unknown'))}\n\n"
            f"📊 Market Cap: ${mcap:,.2f}\n"
            f"💰 Price: ${price:.8f}\n"
            f"🏛 Liquidity: ${liquidity:,.2f}\n\n"
            f"💼 W{session['wallet_index']} (Wallet {session['wallet_index']}): {balances.get('bnb', 0.0):.2f} BNB\n\n"
            f"📈 <a href='{BSC_SCAN_URL}{token_data['address']}'>BSCScan</a> • "
            f"<a href='{DEX_SCREENER_URL}{token_data['address']}'>DexScreener</a>"
        )
        return message

    def _get_trade_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        session = self._get_user_session(user_id)
        mode = session["mode"]
        current_gas = session["gas"]
        current_amount = session["amount"]
        
        # Switch mode button
        other_mode = "sell" if mode == "buy" else "buy"
        switch_text = f"↔️ Switch to {other_mode.upper()} MODE"
        
        keyboard = [
            [
                InlineKeyboardButton(switch_text, callback_query_data=f"trade_mode_{other_mode}"),
                InlineKeyboardButton("🔄 Refresh", callback_query_data="trade_refresh")
            ]
        ]
        
        # Amount buttons
        amounts = DEFAULT_BUY_AMOUNTS if mode == "buy" else DEFAULT_SELL_AMOUNTS
        amount_row = []
        # Group into 3 items per row
        for i, val in enumerate(amounts):
            display_val = f"{val} {'BNB' if mode == 'buy' else ''}"
            # Add checkmark if selected
            if str(val) == str(current_amount):
                display_val += " ✅"
            
            amount_row.append(InlineKeyboardButton(f"💰 {display_val}", callback_query_data=f"trade_amount_{val}"))
            
            if len(amount_row) == 3:
                keyboard.append(amount_row)
                amount_row = []
        
        # Handle remaining amount buttons (e.g., 'X BNB' or 'X %')
        custom_amount_text = f"💰 X {'BNB' if mode == 'buy' else '%'}"
        amount_row.append(InlineKeyboardButton(custom_amount_text, callback_query_data="trade_amount_custom"))
        keyboard.append(amount_row)
        
        # Gas Settings
        keyboard.append([InlineKeyboardButton("-----Gas Settings-----", callback_query_data="none")])
        
        gas_row = [InlineKeyboardButton("🏮 X", callback_query_data="trade_gas_custom")]
        for g in DEFAULT_GAS_SETTINGS:
            btn_text = g
            if g == current_gas:
                btn_text += " ✅"
            gas_row.append(InlineKeyboardButton(btn_text, callback_query_data=f"trade_gas_{g}"))
        keyboard.append(gas_row)
        
        # Wallet Button
        keyboard.append([InlineKeyboardButton(f"🟢 W{session['wallet_index']}", callback_query_data="trade_wallet_select")])
        
        # Bottom Buttons
        keyboard.append([InlineKeyboardButton("💰 Share & Earn", callback_query_data="trade_share")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_query_data="main_menu")])
        
        return InlineKeyboardMarkup(keyboard)

    async def trade_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Entry point for /buy and /sell commands"""
        try:
            user_id = update.effective_user.id
            command = update.message.text.lower()
            
            session = self._get_user_session(user_id)
            session["mode"] = "buy" if "buy" in command else "sell"
            
            # Get user's wallet address from DB
            wallet_address = await self.db.get_wallet_by_telegram_id(user_id)
            if not wallet_address:
                await update.message.reply_text(
                    "❌ Please connect your wallet first using /connect"
                )
                return

            # Fetch data
            token_data = await self.token_utils.get_token_data(TOKEN_CONTRACT)
            balances = await self.token_utils.get_wallet_balances(wallet_address)
            
            message = await self._format_trade_message(user_id, token_data, balances)
            reply_markup = self._get_trade_keyboard(user_id)
            
            await update.message.reply_html(message, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Error in trade_command: {e}", exc_info=True)
            await update.message.reply_text("❌ An error occurred while processing the trade command.")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button clicks for the trading UI"""
        query = update.callback_query
        try:
            user_id = query.from_user.id
            data = query.data
            
            session = self._get_user_session(user_id)
            
            was_updated = False
            
            if data.startswith("trade_mode_"):
                session["mode"] = data.split("_")[-1]
                was_updated = True
            elif data.startswith("trade_gas_"):
                session["gas"] = data.split("_")[-1]
                was_updated = True
            elif data.startswith("trade_amount_"):
                session["amount"] = data.split("_")[-1]
                was_updated = True
            elif data == "trade_refresh":
                was_updated = True
            
            if was_updated:
                # Re-fetch data and update message
                wallet_address = await self.db.get_wallet_by_telegram_id(user_id)
                token_data = await self.token_utils.get_token_data(TOKEN_CONTRACT)
                balances = await self.token_utils.get_wallet_balances(wallet_address)
                
                message = await self._format_trade_message(user_id, token_data, balances)
                reply_markup = self._get_trade_keyboard(user_id)
                
                try:
                    await query.edit_message_text(
                        message, 
                        reply_markup=reply_markup, 
                        parse_mode='HTML'
                    )
                except Exception as e:
                    if "Message is not modified" not in str(e):
                        logger.error(f"Error editing message: {e}")
            
            await query.answer()
        except Exception as e:
            logger.error(f"Error in handle_callback: {e}", exc_info=True)
            await query.answer("❌ An error occurred.", show_alert=True)

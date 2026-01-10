"""
Database manager for COPE Telegram Referral Bot
Handles all database operations with wallet-referrer mapping logic
"""
import aiosqlite
import os
import hashlib
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from config import DATABASE_PATH


class DatabaseManager:
    """Manages all database operations for the referral bot"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    async def init_db(self):
        """Initialize database with schema"""
        async with aiosqlite.connect(self.db_path) as db:
            # Read and execute schema
            schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
            with open(schema_path, 'r') as f:
                schema = f.read()
            await db.executescript(schema)
            await db.commit()
    
    # User and Wallet Operations
    async def create_user(self, telegram_id: int, username: Optional[str] = None) -> bool:
        """Create or update a Telegram user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO users (telegram_id, username, updated_at) VALUES (?, ?, ?)",
                (telegram_id, username, datetime.utcnow())
            )
            await db.commit()
            return True
    
    async def connect_wallet(self, telegram_id: int, wallet_address: str, 
                           signature: Optional[str] = None, message: Optional[str] = None) -> bool:
        """
        Connect a wallet to a Telegram user
        Returns True if successful, False if wallet already connected to another user
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Check if wallet is already connected to another user
            async with db.execute(
                "SELECT telegram_id FROM wallets WHERE wallet_address = ?",
                (wallet_address.lower(),)
            ) as cursor:
                existing = await cursor.fetchone()
                if existing and existing[0] != telegram_id:
                    return False
            
            # Insert or update wallet connection
            await db.execute(
                """INSERT OR REPLACE INTO wallets 
                   (telegram_id, wallet_address, signature, message, connected_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (telegram_id, wallet_address.lower(), signature, message, datetime.utcnow())
            )
            await db.commit()
            return True
    
    async def get_wallet_by_telegram_id(self, telegram_id: int) -> Optional[str]:
        """Get wallet address for a Telegram user"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT wallet_address FROM wallets WHERE telegram_id = ?",
                (telegram_id,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def get_telegram_id_by_wallet(self, wallet_address: str) -> Optional[int]:
        """Get Telegram ID for a wallet address"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT telegram_id FROM wallets WHERE wallet_address = ?",
                (wallet_address.lower(),)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    # Referral Code Operations
    async def get_or_create_referral_code(self, wallet_address: str) -> str:
        """Get existing referral code for wallet or create a new one"""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if code exists
            async with db.execute(
                "SELECT referral_code FROM referral_codes WHERE referrer_wallet = ?",
                (wallet_address.lower(),)
            ) as cursor:
                result = await cursor.fetchone()
                if result:
                    return result[0]
            
            # Create new code (using same logic as wallet_verification)
            hash_obj = hashlib.sha256(wallet_address.encode())
            referral_code = hash_obj.hexdigest()[:16]
            
            # Ensure uniqueness (handle collisions)
            attempts = 0
            while attempts < 10:
                async with db.execute(
                    "SELECT id FROM referral_codes WHERE referral_code = ?",
                    (referral_code,)
                ) as cursor:
                    if not await cursor.fetchone():
                        break
                hash_obj = hashlib.sha256((wallet_address + str(attempts)).encode())
                referral_code = hash_obj.hexdigest()[:16]
                attempts += 1
            
            await db.execute(
                "INSERT INTO referral_codes (referral_code, referrer_wallet) VALUES (?, ?)",
                (referral_code, wallet_address.lower())
            )
            await db.commit()
            return referral_code
    
    async def get_wallet_by_referral_code(self, referral_code: str) -> Optional[str]:
        """Get referrer wallet address for a referral code"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT referrer_wallet FROM referral_codes WHERE referral_code = ?",
                (referral_code,)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    # Wallet-Referrer Mapping Operations (Core Logic)
    async def create_referral_mapping(self, referred_wallet: str, referrer_wallet: str) -> bool:
        """
        Create a wallet-referrer mapping
        Returns True if successful, False if wallet already mapped or self-referral
        """
        # Prevent self-referral
        if referred_wallet.lower() == referrer_wallet.lower():
            return False
        
        async with aiosqlite.connect(self.db_path) as db:
            # Check if wallet is already mapped
            async with db.execute(
                "SELECT id FROM wallet_referrer_mapping WHERE referred_wallet = ?",
                (referred_wallet.lower(),)
            ) as cursor:
                if await cursor.fetchone():
                    return False  # Already mapped
            
            # Create mapping
            await db.execute(
                """INSERT INTO wallet_referrer_mapping 
                   (referred_wallet, referrer_wallet, mapped_at, is_locked)
                   VALUES (?, ?, ?, 0)""",
                (referred_wallet.lower(), referrer_wallet.lower(), datetime.utcnow())
            )
            await db.commit()
            return True
    
    async def get_referrer_for_wallet(self, wallet_address: str) -> Optional[str]:
        """
        Get the referrer wallet for a given referred wallet
        Returns None if wallet is not mapped
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT referrer_wallet FROM wallet_referrer_mapping WHERE referred_wallet = ?",
                (wallet_address.lower(),)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] if result else None
    
    async def lock_mapping_on_first_trade(self, referred_wallet: str, 
                                         transaction_hash: str, trade_timestamp: datetime):
        """
        Lock the referrer mapping when first trade occurs
        This prevents retroactive changes to referrer assignment
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE wallet_referrer_mapping 
                   SET is_locked = 1, first_trade_hash = ?, first_trade_at = ?
                   WHERE referred_wallet = ? AND is_locked = 0""",
                (transaction_hash, trade_timestamp, referred_wallet.lower())
            )
            await db.commit()
    
    async def is_mapping_locked(self, wallet_address: str) -> bool:
        """Check if a wallet's referrer mapping is locked"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT is_locked FROM wallet_referrer_mapping WHERE referred_wallet = ?",
                (wallet_address.lower(),)
            ) as cursor:
                result = await cursor.fetchone()
                return result[0] == 1 if result else False
    
    # Swap Event Operations
    async def record_swap_event(self, transaction_hash: str, trader_wallet: str,
                               swap_type: str, cope_amount: float, bnb_amount: float,
                               cope_tax_amount: float, block_number: int, 
                               block_timestamp: datetime) -> bool:
        """Record a COPE swap event (buy or sell)"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    """INSERT INTO swap_events 
                       (transaction_hash, trader_wallet, swap_type, cope_amount, 
                        bnb_amount, cope_tax_amount, block_number, block_timestamp)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (transaction_hash, trader_wallet.lower(), swap_type, cope_amount,
                     bnb_amount, cope_tax_amount, block_number, block_timestamp)
                )
                await db.commit()
                
                # Lock mapping on first trade if not already locked
                if not await self.is_mapping_locked(trader_wallet):
                    await self.lock_mapping_on_first_trade(
                        trader_wallet, transaction_hash, block_timestamp
                    )
                
                return True
            except aiosqlite.IntegrityError:
                return False  # Transaction already recorded
    
    # Reward Operations
    async def get_referral_stats(self, referrer_wallet: str) -> Dict:
        """
        Get referral statistics for a referrer wallet
        Returns: {
            'referred_count': int,
            'total_tax_generated': float,
            'accrued_rewards': float,
            'withdrawable': bool
        }
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Count referred wallets
            async with db.execute(
                "SELECT COUNT(*) FROM wallet_referrer_mapping WHERE referrer_wallet = ?",
                (referrer_wallet.lower(),)
            ) as cursor:
                referred_count = (await cursor.fetchone())[0]
            
            # Calculate total tax generated and accrued rewards
            # Sum all tax and volume from swap events where trader is a referred wallet
            async with db.execute(
                """SELECT SUM(se.cope_tax_amount), SUM(se.cope_amount)
                   FROM swap_events se
                   JOIN wallet_referrer_mapping wrm ON se.trader_wallet = wrm.referred_wallet
                   WHERE wrm.referrer_wallet = ?""",
                (referrer_wallet.lower(),)
            ) as cursor:
                result = await cursor.fetchone()
                total_tax = result[0] or 0.0
                total_volume = result[1] or 0.0
            
            accrued_rewards = total_tax * 0.5  # 50% to referrer
            withdrawable = accrued_rewards >= 100000  # 100,000 COPE threshold
            
            return {
                'referred_count': referred_count,
                'total_tax_generated': float(total_tax),
                'total_volume': float(total_volume),
                'accrued_rewards': float(accrued_rewards),
                'withdrawable': withdrawable
            }
    
    async def get_leaderboard(self, limit: int = 10) -> List[Tuple[str, float, int]]:
        """
        Get leaderboard of top referrers by accrued rewards
        Returns: List of (wallet_address, accrued_rewards, referred_count)
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """SELECT 
                       wrm.referrer_wallet,
                       SUM(se.cope_tax_amount) * 0.5 as accrued_rewards,
                       COUNT(DISTINCT wrm.referred_wallet) as referred_count
                   FROM wallet_referrer_mapping wrm
                   JOIN swap_events se ON se.trader_wallet = wrm.referred_wallet
                   GROUP BY wrm.referrer_wallet
                   ORDER BY accrued_rewards DESC
                   LIMIT ?""",
                (limit,)
            ) as cursor:
                return await cursor.fetchall()
    
    async def calculate_weekly_rewards(self, period_start: datetime, 
                                      period_end: datetime) -> Dict[str, float]:
        """
        Calculate referral rewards for a weekly period using wallet-referrer mapping
        Returns: Dict mapping referrer_wallet -> reward_amount
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Get all swap events in period with their referrers
            async with db.execute(
                """SELECT 
                       wrm.referrer_wallet,
                       SUM(se.cope_tax_amount) * 0.5 as reward
                   FROM swap_events se
                   JOIN wallet_referrer_mapping wrm ON se.trader_wallet = wrm.referred_wallet
                   WHERE se.block_timestamp >= ? AND se.block_timestamp < ?
                   GROUP BY wrm.referrer_wallet""",
                (period_start, period_end)
            ) as cursor:
                results = await cursor.fetchall()
                return {row[0]: float(row[1]) for row in results}
    
    async def save_weekly_rewards(self, period_start: datetime, period_end: datetime,
                                  rewards: Dict[str, float], merkle_root: str):
        """Save weekly reward settlement to database"""
        async with aiosqlite.connect(self.db_path) as db:
            for referrer_wallet, reward_amount in rewards.items():
                # Calculate total tax for this referrer in period
                async with db.execute(
                    """SELECT SUM(cope_tax_amount) 
                       FROM swap_events se
                       JOIN wallet_referrer_mapping wrm ON se.trader_wallet = wrm.referred_wallet
                       WHERE wrm.referrer_wallet = ? 
                       AND se.block_timestamp >= ? AND se.block_timestamp < ?""",
                    (referrer_wallet, period_start, period_end)
                ) as cursor:
                    total_tax = (await cursor.fetchone())[0] or 0.0
                
                await db.execute(
                    """INSERT INTO referral_rewards 
                       (referrer_wallet, reward_period_start, reward_period_end,
                        total_tax_generated, referral_reward, community_pool_contribution,
                        is_settled, merkle_root, settled_at)
                       VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)""",
                    (referrer_wallet, period_start, period_end, float(total_tax),
                     reward_amount, float(total_tax) * 0.5, merkle_root, datetime.utcnow())
                )
            await db.commit()


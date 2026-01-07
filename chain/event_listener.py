"""
BNB Chain event listener for COPE token swaps
Tracks buy/sell events and calculates tax amounts
"""
from web3 import Web3
from typing import Optional, Dict, List
from datetime import datetime
import asyncio
import logging

from config import BNB_CHAIN_RPC_URL, TOKEN_CONTRACT, APPROVED_LIQUIDITY_POOLS
from database.db_manager import DatabaseManager


logger = logging.getLogger(__name__)


class COPEEventListener:
    """Listens for COPE token swap events on BNB Chain"""
    
    # ERC20 Transfer event signature
    TRANSFER_EVENT_SIGNATURE = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
    
    def __init__(self, db_manager: DatabaseManager, w3: Optional[Web3] = None):
        self.db = db_manager
        self.w3 = w3 or Web3(Web3.HTTPProvider(BNB_CHAIN_RPC_URL))
        self.token_contract = TOKEN_CONTRACT
        self.is_running = False
        self.last_processed_block = None
    
    async def initialize(self):
        """Initialize event listener - get last processed block"""
        # In production, store last processed block in database
        # For now, start from current block minus some lookback
        try:
            current_block = self.w3.eth.block_number
            self.last_processed_block = max(current_block - 1000, 0)  # Lookback 1000 blocks
            logger.info(f"Initialized event listener at block {self.last_processed_block}")
        except Exception as e:
            logger.error(f"Failed to initialize event listener: {e}")
            raise
    
    def get_swap_type(self, from_address: str, to_address: str) -> Optional[str]:
        """
        Determine if a transfer is a buy or sell
        Buy: Transfer to approved pool (user receives COPE)
        Sell: Transfer from approved pool (user sends COPE)
        """
        from_lower = from_address.lower()
        to_lower = to_address.lower()
        
        # Check if this involves an approved liquidity pool
        pool_addresses = [pool.lower() for pool in APPROVED_LIQUIDITY_POOLS]
        
        if to_lower in pool_addresses:
            return "sell"  # User sending COPE to pool = sell
        elif from_lower in pool_addresses:
            return "buy"   # User receiving COPE from pool = buy
        
        return None  # Not a swap event
    
    def calculate_tax(self, amount: int, swap_type: str) -> float:
        """
        Calculate COPE tax amount from transfer
        Note: This assumes the tax is already deducted in the transfer amount
        In production, you may need to compare expected vs actual amounts
        or listen to specific tax events if the contract emits them
        """
        # COPE token typically has a tax (e.g., 5-10%)
        # The tax is usually deducted automatically by the contract
        # This is a simplified calculation - adjust based on actual contract logic
        
        # For now, we'll need to track the difference between expected and actual amounts
        # or listen to specific tax events if available
        
        # Simplified: Assume we can detect tax by comparing transfer amounts
        # In production, you may need to:
        # 1. Query the contract for tax rate
        # 2. Compare expected amount vs actual amount
        # 3. Listen to specific tax events if contract emits them
        
        # Placeholder: Return 5% as tax (adjust based on actual contract)
        tax_rate = 0.06  # 5% - UPDATE THIS BASED ON ACTUAL CONTRACT
        tax_amount = float(amount) * tax_rate
        
        return tax_amount
    
    async def process_transfer_event(self, event: Dict, block_timestamp: datetime):
        """
        Process a Transfer event and record swap if applicable
        Uses wallet-referrer mapping to assign rewards
        """
        try:
            # Parse event data
            from_address = "0x" + event['topics'][1].hex()[-40:]
            to_address = "0x" + event['topics'][2].hex()[-40:]
            amount = int(event['data'], 16)
            
            # Check if this is a swap (involves approved pool)
            swap_type = self.get_swap_type(from_address, to_address)
            if not swap_type:
                return  # Not a swap event
            
            # Determine trader wallet
            trader_wallet = to_address if swap_type == "buy" else from_address
            
            # Get referrer for this wallet using wallet-referrer mapping
            referrer = await self.db.get_referrer_for_wallet(trader_wallet)
            
            # If no referrer, this trade doesn't generate referral rewards
            # But we still record it for community pool tracking
            if not referrer:
                logger.debug(f"No referrer for wallet {trader_wallet}, skipping referral reward")
                # Still record for community pool, but skip referral reward assignment
                return
            
            # Calculate tax amount
            cope_amount = amount / 1e18  # Convert from wei (assuming 18 decimals)
            tax_amount = self.calculate_tax(cope_amount, swap_type)
            
            if tax_amount <= 0:
                return  # No tax, skip
            
            # Get transaction details
            tx_hash = event['transactionHash'].hex()
            block_number = event['blockNumber']
            
            # Record swap event
            # Note: BNB amount would need to be calculated from the swap event
            # For now, we'll set it to 0 and update later if needed
            await self.db.record_swap_event(
                transaction_hash=tx_hash,
                trader_wallet=trader_wallet,
                swap_type=swap_type,
                cope_amount=cope_amount,
                bnb_amount=0.0,  # Would need to calculate from swap event
                cope_tax_amount=tax_amount,
                block_number=block_number,
                block_timestamp=block_timestamp
            )
            
            logger.info(
                f"Recorded {swap_type} swap: {trader_wallet[:10]}... "
                f"Tax: {tax_amount:.2f} COPE, Referrer: {referrer[:10]}..."
            )
            
        except Exception as e:
            logger.error(f"Error processing transfer event: {e}")
    
    async def listen_for_events(self):
        """Main event listening loop"""
        self.is_running = True
        logger.info("Starting COPE event listener...")
        
        while self.is_running:
            try:
                current_block = self.w3.eth.block_number
                
                if self.last_processed_block is None:
                    await self.initialize()
                
                # Process blocks in batches
                if current_block > self.last_processed_block:
                    end_block = min(self.last_processed_block + 100, current_block)
                    
                    logger.info(f"Processing blocks {self.last_processed_block} to {end_block}")
                    
                    # Get Transfer events for COPE token
                    transfer_filter = self.w3.eth.filter({
                        'fromBlock': self.last_processed_block,
                        'toBlock': end_block,
                        'address': self.token_contract,
                        'topics': [self.TRANSFER_EVENT_SIGNATURE]
                    })
                    
                    events = transfer_filter.get_all_entries()
                    
                    # Process each event
                    for event in events:
                        # Get block timestamp
                        block = self.w3.eth.get_block(event['blockNumber'])
                        block_timestamp = datetime.utcfromtimestamp(block['timestamp'])
                        
                        await self.process_transfer_event(event, block_timestamp)
                    
                    self.last_processed_block = end_block
                    
                    # Save last processed block (in production, save to DB)
                
                # Wait before next check
                await asyncio.sleep(12)  # BNB Chain block time ~3s, check every 4 blocks
                
            except Exception as e:
                logger.error(f"Error in event listener loop: {e}")
                await asyncio.sleep(30)  # Wait longer on error
    
    def stop(self):
        """Stop the event listener"""
        self.is_running = False
        logger.info("Stopping COPE event listener...")


# Alternative: Listen to DEX swap events directly
# This would require knowing the DEX contract addresses (PancakeSwap, etc.)
class DEXSwapEventListener:
    """
    Alternative approach: Listen to DEX swap events directly
    This can be more accurate for detecting swaps and calculating amounts
    """
    
    def __init__(self, db_manager: DatabaseManager, w3: Optional[Web3] = None):
        self.db = db_manager
        self.w3 = w3 or Web3(Web3.HTTPProvider(BNB_CHAIN_RPC_URL))
        # PancakeSwap V2 Swap event signature
        self.SWAP_EVENT_SIGNATURE = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
    
    async def process_swap_event(self, event: Dict):
        """
        Process PancakeSwap Swap event
        This gives us more accurate swap data including BNB amounts
        """
        # Implementation would parse Swap event from PancakeSwap
        # and extract: amount0In, amount1In, amount0Out, amount1Out
        # Then determine which is COPE and which is BNB
        pass


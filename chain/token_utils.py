"""
Token utility functions for fetching market data and balances
"""
import aiohttp
import logging
from typing import Dict, Optional
from web3 import Web3
from config import TOKEN_CONTRACT, BNB_CHAIN_RPC_URL

logger = logging.getLogger(__name__)

class TokenUtils:
    def __init__(self, w3: Optional[Web3] = None):
        self.w3 = w3 or Web3(Web3.HTTPProvider(BNB_CHAIN_RPC_URL))
        self.token_contract = TOKEN_CONTRACT

    async def get_token_data(self, token_address: str) -> Dict:
        """
        Fetch token market data (Price, Market Cap, Liquidity)
        Using DexScreener API as a primary source
        """
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        pairs = data.get("pairs", [])
                        if pairs:
                            # Use the first pair (typically the one with most liquidity)
                            pair = pairs[0]
                            return {
                                "name": pair.get("baseToken", {}).get("name", "Unknown"),
                                "symbol": pair.get("baseToken", {}).get("symbol", "TOKEN"),
                                "price": pair.get("priceUsd", "0.00"),
                                "mcap": pair.get("fdv", "0"),  # Using FDV as Market Cap proxy
                                "liquidity": pair.get("liquidity", {}).get("usd", "0"),
                                "dex": pair.get("dexId", "Unknown"),
                                "address": token_address
                            }
        except Exception as e:
            logger.error(f"Error fetching token data: {e}")
        
        # Fallback/Default values if API fails
        return {
            "name": "COPE",
            "symbol": "COPE",
            "price": "0.00",
            "mcap": "0",
            "liquidity": "0",
            "dex": "PancakeSwap",
            "address": token_address
        }

    async def get_wallet_balances(self, wallet_address: str) -> Dict:
        """
        Fetch BNB and COPE balances for a wallet
        """
        try:
            # BNB Balance
            bnb_balance_wei = self.w3.eth.get_balance(Web3.to_checksum_address(wallet_address))
            bnb_balance = self.w3.from_wei(bnb_balance_wei, 'ether')

            # COPE Balance (simplified ERC20 call)
            # In a real scenario, you'd load the ABI and call balanceOf
            # For now, we'll return a placeholder or mock it if needed
            cope_balance = 0.0 # Placeholder
            
            return {
                "bnb": float(bnb_balance),
                "cope": float(cope_balance)
            }
        except Exception as e:
            logger.error(f"Error fetching wallet balances: {e}")
            return {"bnb": 0.0, "cope": 0.0}

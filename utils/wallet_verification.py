"""
Wallet signature verification for Telegram bot
Handles wallet connection via signature (no transaction required)
"""
from eth_account import Account
from eth_account.messages import encode_defunct
from typing import Optional, Tuple
import hashlib
import secrets


def generate_verification_message(telegram_id: int, nonce: Optional[str] = None) -> Tuple[str, str]:
    """
    Generate a message for wallet signature verification
    Returns: (message, nonce)
    """
    if nonce is None:
        nonce = secrets.token_hex(16)
    
    message = f"""COPE Referral Bot - Wallet Connection

Telegram ID: {telegram_id}
Nonce: {nonce}

Sign this message to connect your wallet to the referral bot.
This does not require a transaction or cost any gas."""
    
    return message, nonce


def verify_signature(message: str, signature: str, wallet_address: str) -> bool:
    """
    Verify that a signature was created by the wallet address
    Returns True if signature is valid
    """
    try:
        # Encode the message in Ethereum format
        encoded_message = encode_defunct(text=message)
        
        # Recover the address from the signature
        recovered_address = Account.recover_message(encoded_message, signature=signature)
        
        # Compare addresses (case-insensitive)
        return recovered_address.lower() == wallet_address.lower()
    except Exception as e:
        print(f"Signature verification error: {e}")
        return False


def generate_referral_code(wallet_address: str) -> str:
    """
    Generate a unique referral code for a wallet
    Uses wallet address hash for consistency
    """
    hash_obj = hashlib.sha256(wallet_address.encode())
    return hash_obj.hexdigest()[:16]


def format_wallet_address(address: str) -> str:
    """Format wallet address for display (truncate middle)"""
    if len(address) < 10:
        return address
    return f"{address[:6]}...{address[-4]}"


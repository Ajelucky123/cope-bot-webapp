"""
Weekly reward distribution logic
Handles Merkle tree generation and reward settlement
"""
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from merklelib import MerkleTree
import hashlib
import logging

from database.db_manager import DatabaseManager
from config import MIN_WITHDRAWAL_THRESHOLD


logger = logging.getLogger(__name__)


class RewardDistributor:
    """Handles weekly reward distribution using wallet-referrer mapping"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def calculate_weekly_period(self, date: datetime) -> Tuple[datetime, datetime]:
        """
        Calculate weekly period (Monday 00:00 UTC to Sunday 23:59:59 UTC)
        Returns: (period_start, period_end)
        """
        # Get Monday of the week
        days_since_monday = date.weekday()
        monday = date - timedelta(days=days_since_monday)
        period_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get Sunday 23:59:59 of the week
        period_end = period_start + timedelta(days=7) - timedelta(seconds=1)
        
        return period_start, period_end
    
    async def generate_merkle_tree(self, rewards: Dict[str, float]) -> Tuple[MerkleTree, Dict[str, str]]:
        """
        Generate Merkle tree for reward distribution
        Returns: (merkle_tree, leaf_data_dict)
        
        Only includes wallets with rewards >= MIN_WITHDRAWAL_THRESHOLD
        """
        # Filter rewards by threshold
        eligible_rewards = {
            wallet: amount 
            for wallet, amount in rewards.items() 
            if amount >= MIN_WITHDRAWAL_THRESHOLD
        }
        
        if not eligible_rewards:
            logger.warning("No eligible rewards for distribution (all below threshold)")
            return None, {}
        
        # Create leaf data: hash of (wallet_address, reward_amount)
        leaves = []
        leaf_data = {}
        
        for wallet, amount in eligible_rewards.items():
            # Create leaf: hash(wallet_address + amount)
            leaf_string = f"{wallet.lower()}{int(amount * 1e18)}"  # Amount in smallest unit
            leaf_hash = hashlib.sha256(leaf_string.encode()).hexdigest()
            leaves.append(leaf_hash)
            leaf_data[leaf_hash] = {
                'wallet': wallet.lower(),
                'amount': amount
            }
        
        # Generate Merkle tree
        merkle_tree = MerkleTree(leaves)
        
        logger.info(f"Generated Merkle tree with {len(leaves)} eligible claims")
        
        return merkle_tree, leaf_data
    
    async def settle_weekly_rewards(self, period_start: datetime, period_end: datetime) -> str:
        """
        Settle weekly rewards for a period
        Uses wallet-referrer mapping to calculate rewards
        
        Returns: Merkle root hash
        """
        logger.info(f"Settling weekly rewards for period {period_start} to {period_end}")
        
        # Calculate rewards using wallet-referrer mapping
        rewards = await self.db.calculate_weekly_rewards(period_start, period_end)
        
        if not rewards:
            logger.info("No rewards to settle for this period")
            return None
        
        # Generate Merkle tree
        merkle_tree, leaf_data = await self.generate_merkle_tree(rewards)
        
        if merkle_tree is None:
            logger.warning("No eligible rewards above threshold")
            return None
        
        # Get Merkle root
        merkle_root = merkle_tree.merkle_root
        
        # Save to database
        await self.db.save_weekly_rewards(period_start, period_end, rewards, merkle_root)
        
        logger.info(f"Weekly rewards settled. Merkle root: {merkle_root}")
        logger.info(f"Total eligible wallets: {len(leaf_data)}")
        logger.info(f"Total reward amount: {sum(r for r in rewards.values() if r >= MIN_WITHDRAWAL_THRESHOLD):,.2f} COPE")
        
        return merkle_root
    
    async def get_claim_proof(self, wallet_address: str, period_start: datetime, 
                             period_end: datetime) -> Optional[Dict]:
        """
        Get Merkle proof for a wallet's claim
        Returns: {
            'wallet': str,
            'amount': float,
            'proof': List[str],
            'merkle_root': str
        }
        """
        # Get rewards for period
        rewards = await self.db.calculate_weekly_rewards(period_start, period_end)
        
        if wallet_address.lower() not in rewards:
            return None
        
        amount = rewards[wallet_address.lower()]
        if amount < MIN_WITHDRAWAL_THRESHOLD:
            return None
        
        # Generate Merkle tree
        merkle_tree, leaf_data = await self.generate_merkle_tree(rewards)
        
        if merkle_tree is None:
            return None
        
        # Find leaf hash for this wallet
        wallet_lower = wallet_address.lower()
        leaf_hash = None
        for hash_val, data in leaf_data.items():
            if data['wallet'] == wallet_lower:
                leaf_hash = hash_val
                break
        
        if not leaf_hash:
            return None
        
        # Get proof
        proof = merkle_tree.get_proof(leaf_hash)
        
        return {
            'wallet': wallet_lower,
            'amount': amount,
            'proof': proof,
            'merkle_root': merkle_tree.merkle_root
        }


# Pseudocode for on-chain claim contract interface
"""
On-Chain Claim Contract Interface Assumptions:

contract COPERewardClaim {
    mapping(bytes32 => bool) public claimed;
    bytes32 public merkleRoot;
    
    function updateMerkleRoot(bytes32 _newRoot) external onlyOwner {
        merkleRoot = _newRoot;
    }
    
    function claim(
        address wallet,
        uint256 amount,
        bytes32[] calldata proof
    ) external {
        require(!claimed[keccak256(abi.encodePacked(wallet, amount))], "Already claimed");
        
        bytes32 leaf = keccak256(abi.encodePacked(wallet, amount));
        require(MerkleProof.verify(proof, merkleRoot, leaf), "Invalid proof");
        
        claimed[keccak256(abi.encodePacked(wallet, amount))] = true;
        IERC20(COPE_TOKEN).transfer(wallet, amount);
    }
}
"""


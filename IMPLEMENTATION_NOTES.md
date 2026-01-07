# Implementation Notes - COPE Telegram Referral Bot

## Wallet-Referrer Mapping Logic

The core wallet-referrer mapping logic is implemented as follows:

### 1. Mapping Creation
- When a user clicks a referral link (`/start ref_XXXXX`), the referral code is stored in `context.user_data['referrer_code']`
- When the user connects their wallet via `/connect`, the system:
  1. Verifies the wallet signature
  2. Connects the wallet to the Telegram account
  3. Checks if there's a pending referral code
  4. If yes, retrieves the referrer wallet from the referral code
  5. Creates a mapping: `referred_wallet → referrer_wallet` in `wallet_referrer_mapping` table
  6. Mapping is created with `is_locked = 0` initially

### 2. Mapping Lock on First Trade
- When a swap event is recorded via `record_swap_event()`:
  - The system checks if the trader wallet has a referrer mapping
  - If mapping exists and `is_locked = 0`, it locks the mapping:
    - Sets `is_locked = 1`
    - Records `first_trade_hash` and `first_trade_at`
  - This prevents retroactive changes to referrer assignment

### 3. Reward Assignment
- For each swap event:
  ```python
  trader = swap_event.trader_wallet
  referrer = get_referrer_for_wallet(trader)  # From wallet_referrer_mapping
  tax = calculate_tax(swap_event)
  
  if referrer:
      rewards[referrer] += tax * 0.5  # 50% to referrer
      community_pool += tax * 0.5      # 50% to community pool
  ```

### 4. Database Schema
Key table: `wallet_referrer_mapping`
- `referred_wallet` (UNIQUE) - The wallet that was referred
- `referrer_wallet` - The wallet that referred them
- `is_locked` - Whether mapping is locked after first trade
- `first_trade_hash` - Transaction hash of first trade
- `first_trade_at` - Timestamp of first trade

## Important Implementation Details

### Tax Calculation
The current implementation in `chain/event_listener.py` uses a placeholder 5% tax rate:
```python
tax_rate = 0.05  # 5% - UPDATE THIS BASED ON ACTUAL CONTRACT
```

**Action Required:** Update this based on your actual COPE token contract. You may need to:
1. Query the contract for the actual tax rate
2. Compare expected vs actual transfer amounts
3. Listen to specific tax events if the contract emits them

### Liquidity Pool Detection
The system identifies swaps by checking if transfers involve approved liquidity pools:
- Buy: Transfer FROM pool TO user (user receives COPE)
- Sell: Transfer FROM user TO pool (user sends COPE)

**Action Required:** Add actual PancakeSwap pool addresses to `APPROVED_LIQUIDITY_POOLS` in `config.py`.

### Referral Code System
- Referral codes are generated from wallet address hash (16 characters)
- Codes are stored in `referral_codes` table
- Each wallet has one referral code (reused if exists)
- Codes are used in referral links: `https://t.me/botname?start=ref_XXXXX`

### Weekly Distribution
- Runs every Monday at 00:00 UTC
- Calculates rewards for previous week using wallet-referrer mapping
- Filters wallets with rewards ≥ 100,000 COPE
- Generates Merkle tree
- Updates Merkle root (requires on-chain contract deployment)

### On-Chain Claim Contract
The system assumes a Merkle tree-based claim contract exists on BNB Chain. See pseudocode in `rewards/distribution.py` for the expected interface.

**Action Required:** Deploy a claim contract that:
1. Accepts Merkle proofs
2. Prevents double claims
3. Transfers COPE tokens to claimers

## Abuse Prevention

### Implemented
- ✅ Self-referral prevention (wallet cannot refer itself)
- ✅ Mapping lock on first trade (permanent assignment)
- ✅ Withdrawal threshold enforcement (100,000 COPE minimum)

### Not Implemented (By Design)
- ❌ Minimum trade size
- ❌ Trade frequency caps
- ❌ Progressive reward decay

## Testing Checklist

Before deploying:

1. [ ] Update tax calculation logic based on actual contract
2. [ ] Add actual liquidity pool addresses
3. [ ] Test wallet connection and signature verification
4. [ ] Test referral link generation and mapping creation
5. [ ] Test swap event detection and reward assignment
6. [ ] Test mapping lock on first trade
7. [ ] Test weekly distribution and Merkle tree generation
8. [ ] Deploy and test on-chain claim contract
9. [ ] Verify self-referral prevention works
10. [ ] Test with multiple referral chains

## Deployment Steps

1. Set up environment variables (`.env` file)
2. Install dependencies: `pip install -r requirements.txt`
3. Run bot: `python main.py`
4. Monitor logs for event listener and distribution
5. Deploy claim contract to BNB Chain
6. Update Merkle root on contract after each weekly distribution

## Monitoring

Key metrics to monitor:
- Number of wallet connections
- Number of referral mappings created
- Swap events detected per day
- Total rewards accrued
- Weekly distribution success
- On-chain claim transactions


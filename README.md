# COPE Telegram Referral Bot

A Telegram bot-based referral and community incentive system for COPE token on BNB Chain. The system uses off-chain tracking and on-chain weekly reward distribution.

## Features

- **Wallet Connection**: Connect wallet via signature (no transaction required)
- **Referral System**: Generate unique referral links and earn 50% of COPE tax from referred wallets
- **Wallet-Referrer Mapping**: Permanent referrer assignment locked on first trade
- **Reward Tracking**: Off-chain accrual of referral rewards denominated in COPE
- **Weekly Distribution**: Automated weekly reward settlement via Merkle tree
- **Community Pool**: 50% of tax goes to community pool (unlocks at 1M market cap)

## Token Details

- **Token Name**: COPE
- **Symbol**: COPE
- **Chain**: BNB Chain
- **Contract**: `0x14EB783EE20eD7970Ad5e008044002d2c71D9148`

## Core Logic

### Wallet-Referrer Mapping

1. When a user clicks a referral link and connects their wallet, the bot records:
   ```
   referred_wallet → referrer_wallet
   ```

2. Once a wallet is mapped, **all future COPE trades** from that wallet are credited to the same referrer.

3. Mapping is **locked on first trade** to prevent retroactive changes.

4. Only one referrer per wallet; no multi-level referrals.

### Reward Distribution

- **50% of COPE tax** → Referrer
- **50% of COPE tax** → Community Tax Pool
- Applies to both buys and sells
- No minimum trade size or frequency caps
- Minimum withdrawal: **100,000 COPE**

## Setup

### Prerequisites

- Python 3.8+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- BNB Chain RPC endpoint (or use public endpoints)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd copebot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your TELEGRAM_BOT_TOKEN
```

4. Initialize database:
```bash
# Database will be created automatically on first run
```

5. Update configuration:
   - Edit `config.py` to add approved liquidity pool addresses
   - Update tax calculation logic in `chain/event_listener.py` based on actual contract

6. Run the bot:
```bash
python main.py
```

## Telegram Commands

- `/start` - Initialize user and show welcome message
- `/connect` - Connect wallet via signature
- `/referral` - Generate and display referral link
- `/stats` - Show referral statistics (referred count, rewards, etc.)
- `/leaderboard` - Display top referrers by rewards
- `/rules` - Plain-English explanation of the system
- `/claim` - Check claim status and next distribution time

## Project Structure

```
copebot/
├── bot/
│   ├── __init__.py
│   ├── main.py          # Main bot application
│   └── handlers.py      # Command handlers
├── chain/
│   └── event_listener.py # BNB Chain event listener
├── database/
│   ├── schema.sql       # Database schema
│   └── db_manager.py    # Database operations
├── rewards/
│   └── distribution.py  # Weekly reward distribution
├── utils/
│   └── wallet_verification.py # Signature verification
├── config.py            # Configuration
├── main.py              # Entry point
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## Database Schema

The system uses SQLite with the following key tables:

- `users` - Telegram users
- `wallets` - Connected wallets
- `wallet_referrer_mapping` - **Core mapping logic** (referred_wallet → referrer_wallet)
- `swap_events` - COPE buy/sell transactions
- `referral_rewards` - Accrued rewards per referrer
- `community_tax_pool` - Community pool tracking
- `claim_history` - On-chain claim records

## Event Tracking

The bot listens for COPE token Transfer events on BNB Chain and:

1. Identifies swaps (buys/sells) involving approved liquidity pools
2. Calculates tax amount from each trade
3. Uses wallet-referrer mapping to assign rewards
4. Records swap events and updates reward accruals

## Weekly Distribution

Every Monday at 00:00 UTC:

1. Calculate accrued rewards for the previous week using wallet-referrer mapping
2. Filter wallets with rewards ≥ 100,000 COPE
3. Generate Merkle tree
4. Update Merkle root on-chain
5. Enable on-chain claims

## Abuse Prevention

- **Self-referral protection**: A wallet cannot refer itself
- **Mapping lock**: Referrer assignment is permanent after first trade
- **Withdrawal threshold**: Minimum 100,000 COPE required

## Important Notes

1. **Tax Calculation**: Update the tax calculation logic in `chain/event_listener.py` based on your actual COPE token contract. The current implementation uses a placeholder 5% tax rate.

2. **Liquidity Pools**: Add actual PancakeSwap pool addresses to `APPROVED_LIQUIDITY_POOLS` in `config.py`.

3. **RPC Endpoint**: Use a reliable BNB Chain RPC endpoint. Public endpoints may have rate limits.

4. **Referral Code Mapping**: The current implementation uses a simplified referral code system. You may want to store referral codes in the database for better tracking.

5. **Merkle Tree Contract**: Deploy a claim contract on BNB Chain that accepts Merkle proofs. See pseudocode in `rewards/distribution.py`.

## License

[Add your license here]

## Support

[Add support information here]


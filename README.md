# COPE Telegram Referral Bot & Web App

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

## Web App

This repository includes the Web App used for easy wallet connection in Telegram.

### GitHub Pages Deployment
The `webapp` folder is designed to be hosted on GitHub Pages.
- **URL**: `https://YOUR_USERNAME.github.io/REPO_NAME/index.html`
- **Setup**: Enable GitHub Pages in repository settings pointing to the `root` or `webapp` folder (depending on where you serve it from, currently in `webapp/`).

### Customization
You can customize `webapp/index.html` to change colors, styling, or add wallet options.

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
├── bot/                 # Main bot application
├── chain/               # BNB Chain event listener
├── database/            # Database operations
├── rewards/             # Weekly reward distribution
├── utils/               # Helpers
├── webapp/              # Web App for wallet connection
├── config.py            # Configuration
├── main.py              # Entry point
├── requirements.txt     # Dependencies
└── README.md            # This file
```

## Database Schema

The system uses SQLite with the following key tables:
- `users`, `wallets`, `wallet_referrer_mapping`, `swap_events`, `referral_rewards`, `community_tax_pool`, `claim_history`

## License

[Add your license here]

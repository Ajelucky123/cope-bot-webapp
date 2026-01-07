-- COPE Telegram Referral Bot Database Schema
-- BNB Chain Referral System with Wallet-Referrer Mapping

-- Users table: Telegram users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Wallets table: Connected wallets
CREATE TABLE IF NOT EXISTS wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id BIGINT NOT NULL,
    wallet_address VARCHAR(42) UNIQUE NOT NULL, -- Ethereum-style address (0x...)
    signature TEXT, -- Signature for verification
    message TEXT, -- Original message that was signed
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (telegram_id) REFERENCES users(telegram_id) ON DELETE CASCADE
);

-- Referral codes table: Maps referral codes to referrer wallets
CREATE TABLE IF NOT EXISTS referral_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referral_code VARCHAR(16) UNIQUE NOT NULL, -- Unique referral code
    referrer_wallet VARCHAR(42) NOT NULL, -- Wallet that owns this code
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (referrer_wallet) REFERENCES wallets(wallet_address)
);

-- Wallet-Referrer Mapping table: Core mapping logic
-- This table stores the permanent referrer assignment per wallet
CREATE TABLE IF NOT EXISTS wallet_referrer_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referred_wallet VARCHAR(42) NOT NULL UNIQUE, -- The wallet that was referred
    referrer_wallet VARCHAR(42) NOT NULL, -- The wallet that referred them
    mapped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When the mapping was created
    first_trade_hash VARCHAR(66), -- Transaction hash of first trade (locks mapping)
    first_trade_at TIMESTAMP, -- When first trade occurred (locks mapping)
    is_locked BOOLEAN DEFAULT 0, -- 1 = locked after first trade, 0 = not yet locked
    FOREIGN KEY (referred_wallet) REFERENCES wallets(wallet_address),
    FOREIGN KEY (referrer_wallet) REFERENCES wallets(wallet_address)
);

-- Swap events table: All COPE buy/sell transactions
CREATE TABLE IF NOT EXISTS swap_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_hash VARCHAR(66) UNIQUE NOT NULL,
    trader_wallet VARCHAR(42) NOT NULL, -- Wallet that executed the trade
    swap_type VARCHAR(10) NOT NULL, -- 'buy' or 'sell'
    cope_amount DECIMAL(36, 18), -- COPE tokens involved
    bnb_amount DECIMAL(36, 18), -- BNB involved
    cope_tax_amount DECIMAL(36, 18) NOT NULL, -- Tax amount in COPE
    block_number BIGINT NOT NULL,
    block_timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trader_wallet) REFERENCES wallets(wallet_address)
);

-- Rewards table: Accrued referral rewards per referrer
CREATE TABLE IF NOT EXISTS referral_rewards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_wallet VARCHAR(42) NOT NULL,
    reward_period_start TIMESTAMP NOT NULL, -- Start of weekly period
    reward_period_end TIMESTAMP NOT NULL, -- End of weekly period
    total_tax_generated DECIMAL(36, 18) DEFAULT 0, -- Total tax from all referred wallets
    referral_reward DECIMAL(36, 18) DEFAULT 0, -- 50% of tax (referrer's share)
    community_pool_contribution DECIMAL(36, 18) DEFAULT 0, -- 50% of tax (community pool)
    is_settled BOOLEAN DEFAULT 0, -- Whether rewards have been distributed
    merkle_root VARCHAR(66), -- Merkle root for this period (if settled)
    settled_at TIMESTAMP,
    FOREIGN KEY (referrer_wallet) REFERENCES wallets(wallet_address)
);

-- Community tax pool table: Tracks community pool accumulation
CREATE TABLE IF NOT EXISTS community_tax_pool (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    total_contribution DECIMAL(36, 18) DEFAULT 0, -- Total COPE in pool
    market_cap_at_unlock DECIMAL(36, 18), -- Market cap when unlocked (1M target)
    is_unlocked BOOLEAN DEFAULT 0, -- 1 = unlocked at 1M mcap
    snapshot_taken_at TIMESTAMP, -- When snapshot was taken
    distribution_completed BOOLEAN DEFAULT 0, -- Whether distribution happened
    merkle_root VARCHAR(66), -- Merkle root for distribution
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trading activity snapshot: For community pool eligibility
CREATE TABLE IF NOT EXISTS trading_activity_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_address VARCHAR(42) NOT NULL,
    snapshot_period_start TIMESTAMP NOT NULL,
    snapshot_period_end TIMESTAMP NOT NULL,
    total_volume DECIMAL(36, 18) DEFAULT 0, -- Total trading volume
    buy_count INTEGER DEFAULT 0,
    sell_count INTEGER DEFAULT 0,
    is_eligible BOOLEAN DEFAULT 1, -- Eligible for community pool (has trading activity)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wallet_address) REFERENCES wallets(wallet_address)
);

-- Claim history: Track on-chain claims
CREATE TABLE IF NOT EXISTS claim_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_address VARCHAR(42) NOT NULL,
    reward_period_start TIMESTAMP NOT NULL,
    reward_period_end TIMESTAMP NOT NULL,
    claim_amount DECIMAL(36, 18) NOT NULL,
    transaction_hash VARCHAR(66), -- On-chain claim tx hash
    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wallet_address) REFERENCES wallets(wallet_address)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_wallets_telegram_id ON wallets(telegram_id);
CREATE INDEX IF NOT EXISTS idx_wallets_address ON wallets(wallet_address);
CREATE INDEX IF NOT EXISTS idx_referral_codes_code ON referral_codes(referral_code);
CREATE INDEX IF NOT EXISTS idx_referral_codes_wallet ON referral_codes(referrer_wallet);
CREATE INDEX IF NOT EXISTS idx_mapping_referred ON wallet_referrer_mapping(referred_wallet);
CREATE INDEX IF NOT EXISTS idx_mapping_referrer ON wallet_referrer_mapping(referrer_wallet);
CREATE INDEX IF NOT EXISTS idx_swap_events_trader ON swap_events(trader_wallet);
CREATE INDEX IF NOT EXISTS idx_swap_events_timestamp ON swap_events(block_timestamp);
CREATE INDEX IF NOT EXISTS idx_rewards_referrer ON referral_rewards(referrer_wallet);
CREATE INDEX IF NOT EXISTS idx_rewards_period ON referral_rewards(reward_period_start, reward_period_end);
CREATE INDEX IF NOT EXISTS idx_claim_history_wallet ON claim_history(wallet_address);


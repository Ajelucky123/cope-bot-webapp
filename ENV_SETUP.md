# Environment Variables Setup

## Required Variables

### `TELEGRAM_BOT_TOKEN` (REQUIRED)
**This is the only required variable!**

Get your Telegram bot token from [@BotFather](https://t.me/botfather) on Telegram:

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the instructions to create a new bot
4. Copy the token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Paste it in your `.env` file

**Example:**
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

## Optional Variables

### `BNB_CHAIN_RPC_URL`
BNB Chain RPC endpoint for reading blockchain data.

**Default:** `https://bsc-dataseed1.binance.org/`

**Recommended:** Use a reliable RPC provider like:
- [Ankr](https://www.ankr.com/rpc/)
- [QuickNode](https://www.quicknode.com/)
- [Infura](https://www.infura.io/)
- [Alchemy](https://www.alchemy.com/)

**Example:**
```
BNB_CHAIN_RPC_URL=https://bsc-dataseed1.binance.org/
```

### `BNB_CHAIN_RPC_WS_URL`
WebSocket RPC endpoint (currently not used, but reserved for future use).

**Default:** `wss://bsc-ws-node.nariox.org:443`

**Example:**
```
BNB_CHAIN_RPC_WS_URL=wss://bsc-ws-node.nariox.org:443
```

### `DATABASE_PATH`
Path to the SQLite database file.

**Default:** `database/cope_bot.db`

**Example:**
```
DATABASE_PATH=database/cope_bot.db
```

## Complete `.env` File Example

```env
# Telegram Bot Token (REQUIRED)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# BNB Chain RPC (Optional - uses defaults if not set)
BNB_CHAIN_RPC_URL=https://bsc-dataseed1.binance.org/
BNB_CHAIN_RPC_WS_URL=wss://bsc-ws-node.nariox.org:443

# Database Path (Optional - uses default if not set)
DATABASE_PATH=database/cope_bot.db
```

## Minimum Required `.env` File

If you want to use all defaults, you only need:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

## Security Notes

⚠️ **Important:**
- Never commit your `.env` file to version control
- The `.env` file is already in `.gitignore`
- Keep your `TELEGRAM_BOT_TOKEN` secret
- If your token is compromised, revoke it in @BotFather and create a new one


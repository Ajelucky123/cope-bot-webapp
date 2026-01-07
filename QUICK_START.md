# Quick Start Guide

## Prerequisites

1. Python 3.8 or higher installed
2. Telegram bot token set in `.env` file ✅ (You've done this!)

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Verify Your `.env` File

Make sure your `.env` file contains at minimum:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 3. Run the Bot

```bash
python main.py
```

Or if you prefer:

```bash
python -m bot.main
```

## What to Expect

When you run the bot, you should see:

```
Initializing COPE Referral Bot...
Database initialized
Event listener initialized
Starting Telegram bot...
COPE Referral Bot is running!
```

## Testing the Bot

1. Open Telegram and search for your bot (the username you set in @BotFather)
2. Send `/start` to initialize
3. Send `/connect` to connect your wallet
4. Send `/referral` to get your referral link (after connecting wallet)
5. Send `/stats` to see your statistics
6. Send `/rules` to see the rules

## Troubleshooting

### Bot doesn't respond
- Check that `TELEGRAM_BOT_TOKEN` is correct in `.env`
- Make sure the token doesn't have extra spaces
- Verify the bot is running (check console output)

### Database errors
- The database will be created automatically on first run
- Make sure the `database/` directory exists or can be created
- Check file permissions

### RPC connection errors
- The bot uses public BNB Chain RPC endpoints by default
- If you see connection errors, consider using a paid RPC provider
- Update `BNB_CHAIN_RPC_URL` in `.env` with a reliable provider

### Event listener errors
- The event listener starts automatically
- It may take a moment to sync with the blockchain
- Check logs for any specific error messages

## Next Steps

1. **Test wallet connection**: Use `/connect` and follow the signature process
2. **Test referral system**: Create a referral link and test with another wallet
3. **Monitor events**: Check logs to see if swap events are being detected
4. **Configure RPC**: For production, use a reliable RPC provider

## Production Deployment

For production deployment:

1. Use a process manager like `pm2` or `supervisor`
2. Set up proper logging (file rotation, etc.)
3. Use a reliable RPC provider (Ankr, QuickNode, etc.)
4. Set up monitoring and alerts
5. Deploy the on-chain claim contract (see `rewards/distribution.py`)

## Support

If you encounter issues:
1. Check the console logs for error messages
2. Verify all environment variables are set correctly
3. Ensure all dependencies are installed
4. Check that the database directory is writable


# Local Testing Setup with ngrok

## Step 1: Install ngrok

1. Download ngrok from: https://ngrok.com/download
2. Extract the ngrok.exe file
3. Add it to your PATH or place it in a convenient location

Or install via package manager:
```bash
# Using Chocolatey (Windows)
choco install ngrok

# Using Scoop (Windows)
scoop install ngrok
```

## Step 2: Start the Web App Server

**Option A: Use the batch file**
```bash
start_webapp.bat
```

**Option B: Manual start**
```bash
cd webapp
python -m http.server 8000
```

The server will run on `http://localhost:8000`

## Step 3: Start ngrok

Open a **new terminal window** and run:

```bash
ngrok http 8000
```

You'll see output like:
```
Forwarding   https://abc123xyz.ngrok-free.app -> http://localhost:8000
```

**Copy the HTTPS URL** (the one starting with `https://`)

## Step 4: Update .env File

Add or update this line in your `.env` file:

```env
WEBAPP_URL=https://abc123xyz.ngrok-free.app/index.html
```

Replace `abc123xyz.ngrok-free.app` with your actual ngrok URL.

## Step 5: Restart the Bot

Stop the bot (Ctrl+C) and restart it:

```bash
python main.py
```

## Step 6: Test

1. Open Telegram and find your bot
2. Send `/connect`
3. Click the "🔗 Connect Wallet (Easy)" button
4. The Web App should open in Telegram
5. Connect your MetaMask wallet
6. Sign the message
7. Wallet should be connected!

## Troubleshooting

### ngrok shows "Session Expired"
- Sign up for a free ngrok account: https://dashboard.ngrok.com/signup
- Get your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken
- Run: `ngrok config add-authtoken YOUR_TOKEN`

### Web App doesn't open
- Make sure the ngrok URL is HTTPS (not HTTP)
- Check that the URL ends with `/index.html`
- Verify the webapp server is running on port 8000

### "Connection refused" error
- Make sure the webapp server is running
- Check that ngrok is forwarding to port 8000
- Try restarting both the server and ngrok

### Bot doesn't receive data
- Check that WEBAPP_URL in .env matches your ngrok URL
- Make sure you restarted the bot after updating .env
- Check bot logs for any error messages

## Notes

- **Free ngrok accounts**: URLs change each time you restart ngrok
- **Paid ngrok accounts**: Can get a fixed domain
- For production, use a permanent hosting solution (GitHub Pages, Netlify, etc.)


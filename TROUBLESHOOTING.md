# Wallet Connection Troubleshooting

## Common Issues and Solutions

### 1. QR Code Not Appearing

**Symptoms:** Button clicked but no QR code shows

**Possible Causes:**
- WalletConnect library not loading
- JavaScript errors in console
- Network connectivity issues

**Solutions:**
1. Open browser console (F12) and check for errors
2. Check if WalletConnect library loaded: `typeof WalletConnectProvider`
3. Try refreshing the page
4. Check network tab for failed script loads

### 2. QR Code Appears But Scanning Doesn't Work

**Symptoms:** QR code shows but wallet doesn't connect after scanning

**Possible Causes:**
- Wallet not supporting WalletConnect v1
- Network/bridge server issues
- Wrong wallet app used

**Solutions:**
1. Use a WalletConnect-compatible wallet (MetaMask mobile, Trust Wallet, Coinbase Wallet)
2. Make sure you're scanning with the wallet app (not just a wallet browser)
3. Try a different wallet app
4. Check wallet app version (update if needed)

### 3. "Failed to Connect" Error

**Symptoms:** Error message appears after scanning

**Possible Causes:**
- WalletConnect bridge server down
- Network timeout
- Wallet rejected connection

**Solutions:**
1. Try again (might be temporary network issue)
2. Check internet connection
3. Make sure you approve the connection in your wallet app
4. Try using a different network (WiFi vs mobile data)

### 4. Wallet Connects But Bot Doesn't Receive Data

**Symptoms:** Wallet connects in webapp but bot shows error

**Possible Causes:**
- Data format mismatch
- Telegram WebApp API issue
- Signature verification failed

**Solutions:**
1. Check bot logs for specific error
2. Make sure you're using the latest version of the webapp
3. Try disconnecting and reconnecting
4. Check if wallet address format is correct

### 5. "WalletConnect Not Found" Error

**Symptoms:** Error about WalletConnectProvider

**Possible Causes:**
- Script not loading
- CDN blocked
- Version compatibility

**Solutions:**
1. Check browser console for script load errors
2. Try different browser
3. Check if ad blockers are blocking the script
4. Verify script URLs are accessible

## Debugging Steps

1. **Open Browser Console (F12)**
   - Look for red error messages
   - Check Network tab for failed requests
   - Check Console for JavaScript errors

2. **Test WalletConnect Loading**
   ```javascript
   // In browser console
   typeof WalletConnectProvider
   // Should return "function"
   ```

3. **Test QR Code Generation**
   - Click the button
   - Check console for errors
   - Verify QR code canvas is visible

4. **Test Wallet Connection**
   - Scan QR code
   - Check if wallet app opens
   - Approve connection
   - Check if webapp updates

5. **Check Bot Logs**
   - Look for error messages when data is sent
   - Check if webapp_data is received
   - Verify signature verification

## Getting Help

If issues persist, provide:
1. Browser console errors (screenshot or text)
2. What happens at each step
3. Wallet app you're using
4. Bot error messages (if any)


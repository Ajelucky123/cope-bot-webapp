# WalletConnect v2 Update Required

## Problem

Trust Wallet and other modern wallets show: **"DApp uses unsupported version(1) of WalletConnect"**

This is because WalletConnect v1 is deprecated and no longer supported by modern wallets.

## Solution: Upgrade to WalletConnect v2

### Step 1: Get WalletConnect Cloud Project ID (Free)

1. Go to https://cloud.walletconnect.com/
2. Sign up for a free account
3. Click "Create New Project"
4. Enter project details:
   - Name: COPE Referral Bot
   - Homepage URL: Your webapp URL
5. Copy your **Project ID** (looks like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)

### Step 2: Update Webapp Code

The webapp needs to be updated to use WalletConnect v2 API, which is completely different from v1.

**Key Changes:**
- Different library: `@walletconnect/ethereum-provider@2.x`
- Different API: Uses `EthereumProvider.init()` instead of `new WalletConnectProvider()`
- Requires Project ID
- Different event handling

### Step 3: Implementation Notes

WalletConnect v2 has a different API structure. The implementation will need to be rewritten.

## Alternative Solution (If you want to avoid WalletConnect Cloud)

If you don't want to use WalletConnect Cloud, you could:

1. **Use WalletConnect Modal** - Simpler but also requires Project ID
2. **Use direct wallet connections** - Limited to wallets that support direct connection
3. **Use MetaMask Connect** - But we removed this for QR code only

## Current Status

The webapp is using WalletConnect v1 (`@walletconnect/web3-provider@1.8.0`) which is deprecated.

## Next Steps

1. Register at https://cloud.walletconnect.com/ (free)
2. Get Project ID
3. Update webapp code to use WalletConnect v2
4. Test with Trust Wallet

Would you like me to update the code to use WalletConnect v2? I'll need your Project ID once you get it.

#!/bin/bash
mkdir -p webapp/libs
echo "Downloading dependencies..."

# Telegram Web App
curl -L -o webapp/libs/telegram-web-app.js https://telegram.org/js/telegram-web-app.js
echo "Downloaded telegram-web-app.js"

# Ethers.js
curl -L -o webapp/libs/ethers.min.js https://cdn.ethers.io/lib/ethers-5.7.2.umd.min.js
echo "Downloaded ethers.min.js"

# WalletConnect Provider
curl -L -o webapp/libs/wc-ethereum-provider.js https://cdn.jsdelivr.net/npm/@walletconnect/ethereum-provider@2.10.0/dist/index.umd.js
echo "Downloaded wc-ethereum-provider.js"

# QRCode
curl -L -o webapp/libs/qrcode.min.js https://cdn.jsdelivr.net/npm/qrcode@1.5.3/build/qrcode.min.js
echo "Downloaded qrcode.min.js"

echo "All dependencies downloaded to webapp/libs/"

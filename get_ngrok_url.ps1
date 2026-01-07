# Get ngrok public URL
Write-Host "Checking ngrok status..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

try {
    $response = Invoke-RestMethod -Uri http://localhost:4040/api/tunnels -ErrorAction Stop
    $httpsUrl = ($response.tunnels | Where-Object { $_.proto -eq 'https' }).public_url
    
    if ($httpsUrl) {
        Write-Host "`n✅ ngrok is running!" -ForegroundColor Green
        Write-Host "`nYour ngrok HTTPS URL is:" -ForegroundColor Yellow
        Write-Host "$httpsUrl" -ForegroundColor White -BackgroundColor DarkGreen
        Write-Host "`nAdd this to your .env file:" -ForegroundColor Cyan
        Write-Host "WEBAPP_URL=$httpsUrl/index.html" -ForegroundColor White
        Write-Host "`nOr copy the URL above and update .env manually." -ForegroundColor Gray
    } else {
        Write-Host "❌ No HTTPS tunnel found. Make sure ngrok is running with: ngrok http 8000" -ForegroundColor Red
    }
} catch {
    Write-Host "`n❌ Cannot connect to ngrok. Make sure:" -ForegroundColor Red
    Write-Host "   1. ngrok is running (ngrok http 8000)" -ForegroundColor Yellow
    Write-Host "   2. The webapp server is running on port 8000" -ForegroundColor Yellow
    Write-Host "`nYou can also:" -ForegroundColor Cyan
    Write-Host "   - Open http://localhost:4040 in your browser" -ForegroundColor White
    Write-Host "   - Check the ngrok terminal window for the URL" -ForegroundColor White
}


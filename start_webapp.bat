@echo off
echo Starting Web App server on port 8000...
echo.
echo The webapp will be available at: http://localhost:8000/index.html
echo.
echo Next steps:
echo 1. In another terminal, run: ngrok http 8000
echo 2. Copy the ngrok HTTPS URL
echo 3. Update WEBAPP_URL in .env file
echo.
cd webapp
python -m http.server 8000


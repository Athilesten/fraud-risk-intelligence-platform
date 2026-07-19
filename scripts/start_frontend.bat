@echo off
cd /d "%~dp0\..\frontend"
set VITE_API_BASE_URL=http://localhost:8000
set VITE_API_KEY=dev_fraud_api_key_123
npm install
npm run dev

@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [1/2] Python venv setup...
  python -m venv .venv || goto :fail
  ".venv\Scripts\python.exe" -m pip install -r api\requirements-dev.txt || goto :fail
)
if not exist "web\node_modules" (
  echo [2/2] npm install...
  pushd web
  call npm install || goto :fail
  popd
)

if not exist "api\.env" copy /Y "api\.env.example" "api\.env" >nul
if not exist "web\.env.local" copy /Y "web\.env.example" "web\.env.local" >nul

start "Biz-DNA API :8000" /D "%~dp0api" "%~dp0.venv\Scripts\python.exe" -m uvicorn bizdna_api.main:app --reload --reload-dir . --port 8000
start "Biz-DNA Web :3000" /D "%~dp0web" cmd /k npm run dev

echo Starting servers... browser opens in a few seconds.
timeout /t 8 >nul
start "" http://localhost:3000
exit /b 0

:fail
echo Setup failed. See the messages above.
pause
exit /b 1

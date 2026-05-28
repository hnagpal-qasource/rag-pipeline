@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Missing venv python at .venv\Scripts\python.exe
  exit /b 1
)

if not exist "logs" mkdir "logs"
echo Starting Streamlit on http://127.0.0.1:8501
echo Logging to logs\streamlit.log

".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.fileWatcherType none --logger.level debug 1> logs\streamlit.log 2>&1

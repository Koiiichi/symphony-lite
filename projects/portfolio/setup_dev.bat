@echo off
echo Setting up backend environment...
python -m venv backend\venv
echo Installing requirements...
backend\venv\Scripts\pip.exe install -r backend\requirements.txt
echo Backend ready. Start in a new terminal:
echo     backend\venv\Scripts\python.exe backend\app.py
echo.
echo Serving frontend statically (port 8000). In a new terminal run:
echo     cd frontend
echo     python -m http.server 8000

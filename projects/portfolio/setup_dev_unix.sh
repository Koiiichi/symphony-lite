#!/bin/bash
set -e
echo "Setting up backend environment..."
python3 -m venv backend/venv
echo "Installing requirements..."
backend/venv/bin/pip install -r backend/requirements.txt
echo "Backend ready. Start in a new terminal:"
echo "    backend/venv/bin/python backend/app.py"
echo ""
echo "Serving frontend statically (port 8000). In a new terminal run:"
echo "    cd frontend"
echo "    python3 -m http.server 8000"

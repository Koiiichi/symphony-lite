Content of README.md (1424 bytes):
Portfolio: Dark-themed portfolio with projects grid and contact form

Files included
- frontend/index.html
- frontend/package.json
- backend/app.py
- backend/requirements.txt
- setup_dev.bat (Windows)
- setup_dev_unix.sh (Unix/macOS)

How to run

Windows
1) Run setup_dev.bat to create the backend virtualenv and install requirements.
2) Start backend: open a new terminal and run
       backend\venv\Scripts\python.exe backend\app.py
3) Serve frontend statically on port 8000: open another terminal and run
       cd frontend
       python -m http.server 8000
4) Open http://localhost:8000/index.html

Unix/macOS
1) Make the Unix script executable and run it
       chmod +x setup_dev_unix.sh
       ./setup_dev_unix.sh
2) Start backend: 
       backend/venv/bin/python backend/app.py
3) Serve frontend on port 8000:
       cd frontend
       python3 -m http.server 8000
4) Open http://localhost:8000/index.html

Testing the contact API
- curl -X POST http://localhost:5001/api/contact -H "Content-Type: application/json" -d '{"name":"Alice","email":"alice@example.com","message":"Hi"}'

Notes
- The backend is a simple Flask app with CORS enabled and an in-memory store for demo purposes.
- The frontend is a standalone HTML app that loads React from a CDN and posts the contact form to /api/contact (same-origin is recommended for simplicity).

This README serves as a quick start and a reference for future maintenance.

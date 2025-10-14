import os, sys, subprocess, time, pathlib
import http.server
import socketserver
import threading

def run_servers(project_path: str, fe_port: int = 3000, be_port: int = 5000):
    """Run servers with correct Python interpreter and configurable ports."""
    project = pathlib.Path(project_path).resolve()
    backend = project / "backend"
    frontend = project / "frontend"
    
    print(f"[Runner] Installing dependencies and starting servers for {project_path}...")
    
    # 1) Ensure backend deps install in the same interpreter as orchestrator
    print(f"[Runner] Installing backend dependencies using {sys.executable}...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        cwd=str(backend),
        check=True
    )
    
    # 2) Start backend with the same interpreter
    print(f"[Runner] Starting Flask backend on port {be_port}...")
    be_proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=str(backend),
        env={**os.environ, "PORT": str(be_port)}
    )
    
    # 3) Start frontend server
    print(f"[Runner] Starting frontend server on port {fe_port}...")
    
    def serve_frontend():
        os.chdir(str(frontend))
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", fe_port), handler) as httpd:
            print(f"[Runner] Frontend server serving from {frontend}")
            httpd.serve_forever()
    
    # Run frontend server in a separate thread
    fe_thread = threading.Thread(target=serve_frontend, daemon=True)
    fe_thread.start()
    
    # 4) Give servers time to bind
    time.sleep(8)
    print(f"[Runner] Servers running on localhost:{fe_port} (frontend) and localhost:{be_port} (backend)")
    print(f"[Runner] Open http://localhost:{fe_port} in your browser")
    
    return be_proc, fe_thread

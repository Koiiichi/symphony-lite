"""Runner - Manages local development servers with readiness checks.

Enhanced with URL polling to ensure servers are ready before returning.
"""

import os
import sys
import subprocess
import time
import pathlib
import http.server
import socketserver
import threading
import requests
from typing import Tuple


def wait_for_server(url: str, timeout: int = 30, check_interval: float = 0.5) -> bool:
    """Poll URL until server is ready or timeout is reached.
    
    Args:
        url: URL to check (e.g., http://localhost:5000)
        timeout: Maximum seconds to wait
        check_interval: Seconds between checks
        
    Returns:
        True if server responds, False if timeout
    """
    start = time.time()
    
    while time.time() - start < timeout:
        try:
            response = requests.get(url, timeout=2)
            # Accept any response code < 500 as "ready"
            if response.status_code < 500:
                return True
        except requests.exceptions.RequestException:
            # Server not ready yet
            pass
        
        time.sleep(check_interval)
    
    return False


def run_servers(
    project_path: str,
    fe_port: int = 3000,
    be_port: int = 5000,
    timeout: int = 30
) -> Tuple[subprocess.Popen, threading.Thread]:
    """Run servers with readiness checks and configurable ports.
    
    Args:
        project_path: Absolute path to project directory
        fe_port: Frontend server port
        be_port: Backend server port
        timeout: Maximum seconds to wait for server readiness
        
    Returns:
        Tuple of (backend_process, frontend_thread)
        
    Raises:
        RuntimeError: If servers don't become ready within timeout
    """
    project = pathlib.Path(project_path).resolve()
    backend = project / "backend"
    frontend = project / "frontend"
    
    print(f"[Runner] Installing dependencies and starting servers for {project_path}...")
    
    # Ensure directories exist
    if not backend.exists():
        print(f"[Runner] Warning: Backend directory not found: {backend}")
        backend.mkdir(parents=True, exist_ok=True)
    
    if not frontend.exists():
        print(f"[Runner] Warning: Frontend directory not found: {frontend}")
        frontend.mkdir(parents=True, exist_ok=True)
    
    # 1) Install backend dependencies using current interpreter
    requirements_file = backend / "requirements.txt"
    if requirements_file.exists():
        print(f"[Runner] Installing backend dependencies using {sys.executable}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
                cwd=str(backend),
                check=True,
                capture_output=True
            )
            print(f"[Runner] Backend dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"[Runner] Warning: Failed to install dependencies: {e}")
    else:
        print(f"[Runner] No requirements.txt found, skipping dependency installation")
    
    # 2) Start backend with the same interpreter
    app_file = backend / "app.py"
    if not app_file.exists():
        raise RuntimeError(f"Backend app.py not found: {app_file}")
    
    print(f"[Runner] Starting Flask backend on port {be_port}...")
    backend_env = {**os.environ, "PORT": str(be_port), "FLASK_ENV": "development"}
    be_proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=str(backend),
        env=backend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for backend to be ready
    backend_url = f"http://localhost:{be_port}"
    print(f"[Runner] Waiting for backend at {backend_url}...")
    
    if not wait_for_server(backend_url, timeout=timeout):
        be_proc.terminate()
        raise RuntimeError(f"Backend not ready after {timeout}s on port {be_port}")
    
    print(f"[Runner] Backend ready at {backend_url}")
    
    # 3) Start frontend server
    index_file = frontend / "index.html"
    if not index_file.exists():
        print(f"[Runner] Warning: index.html not found: {index_file}")
    
    print(f"[Runner] Starting frontend server on port {fe_port}...")
    
    def serve_frontend():
        """Serve frontend files with simple HTTP server."""
        os.chdir(str(frontend))
        
        # Custom handler to suppress log spam
        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                # Only log errors
                if args[1][0] in ('4', '5'):
                    super().log_message(format, *args)
        
        handler = QuietHandler
        
        try:
            with socketserver.TCPServer(("", fe_port), handler) as httpd:
                print(f"[Runner] Frontend server serving from {frontend}")
                httpd.serve_forever()
        except OSError as e:
            print(f"[Runner] Error starting frontend server: {e}")
    
    # Run frontend server in a daemon thread
    fe_thread = threading.Thread(target=serve_frontend, daemon=True)
    fe_thread.start()
    
    # Wait for frontend to be ready
    frontend_url = f"http://localhost:{fe_port}"
    print(f"[Runner] Waiting for frontend at {frontend_url}...")
    
    if not wait_for_server(frontend_url, timeout=timeout):
        be_proc.terminate()
        raise RuntimeError(f"Frontend not ready after {timeout}s on port {fe_port}")
    
    print(f"[Runner] Frontend ready at {frontend_url}")
    print(f"[Runner] Both servers running and ready")
    
    return be_proc, fe_thread


def stop_servers(be_proc: subprocess.Popen, fe_thread: threading.Thread, timeout: int = 5):
    """Gracefully stop both servers.
    
    Args:
        be_proc: Backend process
        fe_thread: Frontend thread
        timeout: Maximum seconds to wait for clean shutdown
    """
    print(f"[Runner] Stopping servers...")
    
    # Terminate backend process
    if be_proc and be_proc.poll() is None:
        try:
            be_proc.terminate()
            be_proc.wait(timeout=timeout)
            print(f"[Runner] Backend stopped")
        except subprocess.TimeoutExpired:
            be_proc.kill()
            print(f"[Runner] Backend force-killed")
    
    # Frontend thread is daemon, will stop automatically
    print(f"[Runner] Frontend thread terminated")
    print(f"[Runner] All servers stopped")


if __name__ == "__main__":
    # Test runner
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python runner.py <project_path>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    try:
        be_proc, fe_thread = run_servers(project_path, 3000, 5000)
        print("Servers running. Press Ctrl+C to stop...")
        
        # Keep alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_servers(be_proc, fe_thread)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

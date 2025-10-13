import subprocess, os, time
import http.server
import socketserver
import threading

def run_servers():
    print("[Runner] Installing dependencies and starting servers...")
    
    # Install backend dependencies
    print("[Runner] Installing Flask dependencies...")
    subprocess.run(["pip", "install", "-r", "requirements.txt"], 
                   cwd="projects/portfolio/backend", check=True)
    
    # Start backend server
    print("[Runner] Starting Flask backend on port 5000...")
    backend_proc = subprocess.Popen(["python", "app.py"], 
                                   cwd="projects/portfolio/backend")
    
    # Start frontend server (simple HTTP server for the HTML file)
    print("[Runner] Starting frontend server on port 3000...")
    
    # Change to the frontend directory and serve files
    frontend_dir = os.path.abspath("projects/portfolio/frontend")
    
    def serve_frontend():
        os.chdir(frontend_dir)
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", 3000), handler) as httpd:
            print(f"[Runner] Frontend server serving from {frontend_dir}")
            httpd.serve_forever()
    
    # Run frontend server in a separate thread
    frontend_thread = threading.Thread(target=serve_frontend, daemon=True)
    frontend_thread.start()
    
    time.sleep(3)
    print("[Runner] Servers running on localhost:3000 (frontend) and localhost:5000 (backend)")
    print("[Runner] Open http://localhost:3000 in your browser")
    
    return backend_proc, frontend_thread

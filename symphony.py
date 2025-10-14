#!/usr/bin/env python3
"""
Symphony-Lite automatic setup and launcher.
Handles virtual environment creation and dependency management automatically.
"""
import os
import sys
import subprocess
import venv
from pathlib import Path

def get_symphony_root():
    """Get the Symphony-Lite root directory."""
    return Path(__file__).parent.resolve()

def get_venv_python():
    """Get the path to Python executable in the virtual environment."""
    venv_path = get_symphony_root() / "venv"
    if os.name == 'nt':  # Windows
        return venv_path / "Scripts" / "python.exe"
    else:  # Unix/macOS
        return venv_path / "bin" / "python"

def is_venv_setup():
    """Check if virtual environment is properly set up."""
    python_exe = get_venv_python()
    return python_exe.exists()

def setup_venv():
    """Set up the virtual environment and install dependencies."""
    symphony_root = get_symphony_root()
    venv_path = symphony_root / "venv"
    
    print(" Setting up Symphony-Lite for first use...")
    
    # Create virtual environment
    if not venv_path.exists():
        print(" Creating virtual environment...")
        venv.create(venv_path, with_pip=True)
    
    # Install dependencies
    python_exe = get_venv_python()
    requirements_file = symphony_root / "requirements.txt"
    
    if requirements_file.exists():
        print("Installing dependencies...")
        subprocess.run([
            str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True)
    
    print("Symphony-Lite is ready!")

def run_in_venv(args):
    """Run the CLI in the virtual environment."""
    python_exe = get_venv_python()
    cli_script = get_symphony_root() / "cli.py"
    
    # Ensure setup is complete
    if not is_venv_setup():
        setup_venv()
    
    # Run the CLI
    subprocess.run([str(python_exe), str(cli_script)] + args)

if __name__ == "__main__":
    # Pass all arguments to the CLI
    run_in_venv(sys.argv[1:])
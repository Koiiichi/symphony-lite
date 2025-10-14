#!/usr/bin/env python3
"""
Symphony-Lite Demo Script

This script demonstrates how to use Symphony-Lite with the new CLI interface.
Run this to see the system in action on the portfolio project.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    print("Symphony-Lite Demo")
    print("=" * 50)
    
    # Ensure we're in the right directory
    repo_root = Path(__file__).parent
    os.chdir(repo_root)
    
    # Check if virtual environment exists
    venv_python = repo_root / "venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = repo_root / "venv" / "Scripts" / "python"  # For non-Windows
    
    if not venv_python.exists():
        print("ERROR: Virtual environment not found. Please set up a virtual environment first.")
        print("Run: python -m venv venv && venv/Scripts/activate && pip install -r requirements.txt")
        return 1
    
    print(f"Using Python: {venv_python}")
    
    # Demo parameters
    project_path = "projects/portfolio" 
    goal = "Create a professional dark-themed portfolio with projects grid and working contact form"
    
    print(f"\nProject: {project_path}")
    print(f"Goal: {goal}")
    print(f"Steps: 1 (demo mode)")
    
    # Validate project structure first
    print("\nValidating project structure...")
    result = subprocess.run([
        str(venv_python), "cli.py", "validate", 
        "--project", project_path
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"ERROR: Validation failed: {result.stderr}")
        return 1
    
    print("Project structure is valid!")
    
    # Ask user if they want to continue
    response = input("\nRun the full workflow? (y/N): ").lower().strip()
    if response != 'y':
        print("Demo cancelled. To run manually:")
        print(f"  python cli.py run --project \"{project_path}\" --goal \"{goal}\"")
        return 0
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("\nWarning: OPENAI_API_KEY not found in environment")
        print("   The brain agent may not work without it.")
        print("   Create a .env file with your OpenAI API key.")
        
        continue_anyway = input("Continue anyway? (y/N): ").lower().strip()
        if continue_anyway != 'y':
            return 0
    
    # Run the workflow
    print("\nStarting Symphony-Lite workflow...")
    print("   This will:")
    print("   1. Generate/update code with Brain Agent") 
    print("   2. Start local servers")
    print("   3. Test with Sensory Agent")
    print("   4. Apply fixes if needed")
    
    try:
        result = subprocess.run([
            str(venv_python), "cli.py", "run",
            "--project", project_path,
            "--goal", goal,
            "--steps", "1"
        ], text=True)
        
        if result.returncode == 0:
            print("\nWorkflow completed successfully!")
            print("   Check the generated files in projects/portfolio/")
            print("   Screenshots saved in artifacts/ folder")
        else:
            print(f"\nWorkflow failed with exit code {result.returncode}")
            
    except KeyboardInterrupt:
        print("\nWorkflow interrupted by user")
        return 1
    except Exception as e:
        print(f"\nWorkflow failed with error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
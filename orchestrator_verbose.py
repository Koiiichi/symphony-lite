#!/usr/bin/env python3
"""
Symphony-Lite Orchestrator - Verbose Mode
Shows detailed agent actions and workflow visibility
"""

import os
import time
import json
from datetime import datetime
from agents.brain_agent import brain_agent
from agents.sensory_agent import make_sensory_agent
from runner import run_servers

class WorkflowLogger:
    def __init__(self):
        self.start_time = datetime.now()
        self.step_count = 0
        
    def log_step(self, agent_name, action, details=""):
        self.step_count += 1
        timestamp = datetime.now().strftime("%H:%M:%S")
        elapsed = (datetime.now() - self.start_time).seconds
        
        print(f"\n{'='*80}")
        print(f"STEP {self.step_count} [{timestamp}] (+{elapsed}s) - {agent_name.upper()}")
        print(f"ACTION: {action}")
        if details:
            print(f"DETAILS: {details}")
        print(f"{'='*80}")

def check_project_files():
    """Check what files exist in the project directory"""
    print("\n CHECKING PROJECT FILES...")
    
    frontend_dir = "projects/portfolio/frontend"
    backend_dir = "projects/portfolio/backend"
    
    if os.path.exists(frontend_dir):
        frontend_files = os.listdir(frontend_dir)
        print(f"  Frontend files: {frontend_files}")
    else:
        print(f"  Frontend directory not found: {frontend_dir}")
        
    if os.path.exists(backend_dir):
        backend_files = os.listdir(backend_dir)
        print(f"  Backend files: {backend_files}")
    else:
        print(f"  Backend directory not found: {backend_dir}")

def main():
    logger = WorkflowLogger()
    
    print("STARTING SYMPHONY-LITE WORKFLOW")
    print("Goal: Create a dark-themed portfolio with projects grid and contact form")
    print(f"Start time: {logger.start_time.strftime('%H:%M:%S')}")
    
    # Check initial state
    check_project_files()
    
    # ============================================================================
    # STEP 1: BRAIN AGENT - CODE GENERATION
    # ============================================================================
    logger.log_step("BRAIN AGENT", "Starting code generation", 
                    "Generating React frontend + Flask backend")
    
    instructions = """
    Generate React frontend + Flask backend for: Create a dark-themed portfolio with projects grid and contact form
    
    Please create the following files:
    - frontend/index.html: A standalone HTML file with CSS and JavaScript
    - frontend/package.json: Package configuration for React/Node.js
    - backend/app.py: Flask backend with contact form API
    - backend/requirements.txt: Python dependencies
    
    Use the write_code function to save each file. Paths should be relative to projects/portfolio/.
    Make sure to add console.log statements to show when the frontend is loading.
    """
    
    print("\n BRAIN AGENT is thinking and generating code...")
    print("   This may take 30-60 seconds...")
    
    try:
        result = brain_agent.run(instructions)
        logger.log_step("BRAIN AGENT", "Code generation completed", 
                        "Files should now be written to projects/portfolio/")
    except Exception as e:
        logger.log_step("BRAIN AGENT", "ERROR occurred", f"Error: {str(e)}")
        return False
    
    # Check what files were created
    print("\n CHECKING WHAT THE BRAIN AGENT CREATED...")
    check_project_files()
    
    # ============================================================================
    # STEP 2: RUNNER - SERVER STARTUP  
    # ============================================================================
    logger.log_step("RUNNER", "Starting local servers", 
                    "Flask backend (port 5000) + Frontend (port 3000)")
    
    print("\n RUNNER is starting servers...")
    print("   Installing dependencies and launching servers...")
    
    try:
        backend_proc, frontend_proc = run_servers()
        logger.log_step("RUNNER", "Servers started successfully",
                        "Backend: http://localhost:5000, Frontend: http://localhost:3000")
        
        # Wait for servers to be ready
        print("\n Waiting 5 seconds for servers to fully start...")
        time.sleep(5)
        
    except Exception as e:
        logger.log_step("RUNNER", "ERROR starting servers", f"Error: {str(e)}")
        return False
    
    # ============================================================================
    # STEP 3: SENSORY AGENT - VISUAL INSPECTION
    # ============================================================================
    logger.log_step("SENSORY AGENT", "Starting visual inspection", 
                    "Opening browser and analyzing UI quality")
    
    print("\n SENSORY AGENT is starting browser automation...")
    print("   This will open a browser window and take screenshots")
    print("   Screenshots will be saved to artifacts/ folder")
    
    try:
        sensory = make_sensory_agent()
        
        # Create artifacts directory if it doesn't exist
        os.makedirs("artifacts", exist_ok=True)
        
        print("\n Opening http://localhost:3000 in browser...")
        feedback = sensory.run("Go to http://localhost:3000 and evaluate layout visuals in JSON format. Take a screenshot and analyze the dark theme, project grid layout, and contact form.")
        
        logger.log_step("SENSORY AGENT", "Visual analysis completed", 
                        f"Feedback: {str(feedback)[:200]}...")
        
        print("\n SENSORY AGENT FEEDBACK:")
        print("=" * 50)
        if isinstance(feedback, dict):
            print(json.dumps(feedback, indent=2))
        else:
            print(feedback)
        print("=" * 50)
        
    except Exception as e:
        logger.log_step("SENSORY AGENT", "ERROR during inspection", f"Error: {str(e)}")
        print(f"   Sensory agent error: {e}")
        # Don't return False, continue to show what we accomplished
    
    # ============================================================================
    # FINAL SUMMARY
    # ============================================================================
    total_time = (datetime.now() - logger.start_time).seconds
    
    print(f"\n SYMPHONY-LITE WORKFLOW COMPLETED")
    print(f" Total execution time: {total_time} seconds")
    print(f" Total steps executed: {logger.step_count}")
    
    print(f"\n FINAL STATUS:")
    print(f"   Brain Agent: Generated code files")
    print(f"   Runner: Started local servers")
    print(f"   Sensory Agent: Analyzed UI (check artifacts/ for screenshots)")
    
    print(f"\n ACCESS YOUR PORTFOLIO:")
    print(f"   Frontend: http://localhost:3000")
    print(f"   Backend API: http://localhost:5000/api/contact")
    
    print(f"\n ARTIFACTS:")
    if os.path.exists("artifacts"):
        artifacts = os.listdir("artifacts")
        print(f"   Screenshots and logs: {artifacts}")
    else:
        print(f"   No artifacts folder found")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n Symphony-Lite workflow completed successfully!")
        print("   Check the browser window and artifacts folder for results.")
    else:
        print("\n Symphony-Lite workflow encountered errors.")
        print("   Check the logs above for details.")
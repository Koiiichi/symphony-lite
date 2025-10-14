from smolagents import CodeAgent, tool
from smolagents.cli import load_model
from openai import OpenAI
import os, subprocess, json, pathlib
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Global variable to store current project path
_current_project_path = None

def set_project_path(project_path: str):
    """Set the current project path for the brain agent."""
    global _current_project_path
    _current_project_path = str(pathlib.Path(project_path).resolve())

@tool
def write_code(path: str, content: str) -> str:
    """Writes generated code to file
    
    Args:
        path: The file path where the code should be written (relative to current project)
        content: The code content to write to the file
    """
    global _current_project_path
    
    # Use current project path or default fallback
    if _current_project_path:
        base_dir = _current_project_path
    else:
        # Fallback for backward compatibility
        base_dir = os.path.join(os.getcwd(), "projects", "portfolio")
    
    full_path = os.path.join(base_dir, path)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    with open(full_path, "w") as f:
        f.write(content)
    return f"Wrote code to {full_path}"

@tool
def read_existing_code(path: str) -> str:
    """Reads existing code from a file
    
    Args:
        path: The file path to read (relative to current project)
    """
    global _current_project_path
    
    if _current_project_path:
        base_dir = _current_project_path
    else:
        base_dir = os.path.join(os.getcwd(), "projects", "portfolio")
    
    full_path = os.path.join(base_dir, path)
    
    try:
        with open(full_path, "r") as f:
            content = f.read()
        return f"Content of {full_path}:\n{content}"
    except FileNotFoundError:
        return f"File not found: {full_path}"
    except Exception as e:
        return f"Error reading {full_path}: {e}"

@tool
def list_project_files() -> str:
    """Lists all files in the current project directory"""
    global _current_project_path
    
    if _current_project_path:
        base_dir = _current_project_path
    else:
        base_dir = os.path.join(os.getcwd(), "projects", "portfolio")
    
    try:
        files = []
        for root, dirs, filenames in os.walk(base_dir):
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), base_dir)
                files.append(rel_path)
        return f"Project files in {base_dir}:\n" + "\n".join(sorted(files))
    except Exception as e:
        return f"Error listing files: {e}"

@tool
def run_command(cmd: str, cwd: str | None = None) -> str:
    """Run a system command
    
    Args:
        cmd: The command to execute
        cwd: The working directory for command execution (default: project directory)
    """
    global _current_project_path
    
    # Default to project directory if no cwd specified
    if cwd is None and _current_project_path:
        cwd = _current_project_path
    elif cwd is None:
        cwd = "."
    
    try:
        out = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=30)
        result = out.stdout or out.stderr
        return f"Command: {cmd}\nOutput: {result}"
    except subprocess.TimeoutExpired:
        return f"Command timed out: {cmd}"
    except Exception as e:
        return f"Command failed: {cmd}\nError: {e}"

# Create the brain agent instance
model = load_model("LiteLLMModel", os.getenv("BRAIN_MODEL", "gpt-4o"))
brain_agent = CodeAgent(
    tools=[write_code, read_existing_code, list_project_files, run_command],
    model=model,
    name="BrainAgent",
    max_steps=12,
)

# Enhanced brain functions for orchestrator integration
def brain_generate(project_path: str, goal: str):
    """Generate initial code using brain agent with project-aware context."""
    set_project_path(project_path)
    
    instructions = f"""
    You are working on a project located at: {project_path}
    
    GOAL: {goal}
    
    Please analyze the current project structure and generate/update the following files as needed:
    
    1. frontend/index.html - A complete, modern HTML file with embedded CSS and JavaScript
       - Responsive design that works on desktop and mobile
       - Dark theme as requested
       - Professional portfolio layout with sections for hero, projects grid, and contact form
       - Working contact form that submits to /api/contact
       - Proper form validation and user feedback
    
    2. frontend/package.json - Package configuration for any Node.js dependencies (if needed)
    
    3. backend/app.py - Flask backend with proper CORS setup
       - Handle POST requests to /api/contact
       - Return JSON responses
       - Proper error handling
    
    4. backend/requirements.txt - Python dependencies (Flask, flask-cors)
    
    IMPORTANT GUIDELINES:
    - Use the write_code function to save each file with paths relative to the project root
    - First use list_project_files to see what already exists
    - Use read_existing_code to check existing files before modifying them
    - Make sure the contact form JavaScript actually connects to the backend API
    - Ensure good visual design with proper spacing, alignment, and contrast
    - Include proper form validation and user feedback (success/error messages)
    - Test that all interactive elements work properly
    
    Start by listing the current project files, then proceed with generation/updates.
    """
    
    return brain_agent.run(instructions)

def brain_fix(project_path: str, sensory_report: dict, goal: str):
    """Apply fixes based on sensory feedback."""
    set_project_path(project_path)
    
    feedback_text = json.dumps(sensory_report, indent=2)
    
    fix_instructions = f"""
    You are working on a project at: {project_path}
    Original goal: {goal}
    
    Based on the sensory feedback below, please fix the identified issues:
    
    FEEDBACK REPORT:
    {feedback_text}
    
    FOCUS AREAS:
    1. If alignment_score < 0.9: Improve CSS layout, spacing, and visual hierarchy
       - Fix any alignment issues with flexbox/grid
       - Ensure consistent spacing and margins
       - Improve typography and visual balance
    
    2. If form submission failed: Fix JavaScript form handling and API integration
       - Ensure form properly captures input values
       - Fix any API endpoint issues
       - Add proper success/error message display
       - Test form validation
    
    3. If visual sections are missing: Ensure all key components are visible and properly styled
       - Hero section should be prominent
       - Projects grid should be clear and organized
       - Contact form should be easily accessible
    
    4. Improve contrast and readability if contrast_score is low
    
    PROCESS:
    1. First, read the existing files to understand current state
    2. Identify specific issues from the feedback
    3. Make targeted improvements to CSS, HTML, and JavaScript
    4. Focus on practical fixes that will improve scores in next iteration
    
    Start by examining the current code, then apply specific improvements.
    """
    
    return brain_agent.run(fix_instructions)

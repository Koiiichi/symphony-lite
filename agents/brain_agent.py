from smolagents import CodeAgent, tool
from smolagents.cli import load_model
from openai import OpenAI
import os, subprocess, json
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@tool
def write_code(path: str, content: str) -> str:
    """Writes generated code to file
    
    Args:
        path: The file path where the code should be written (relative to projects/portfolio/)
        content: The code content to write to the file
    """
    # Ensure the path is relative to the projects/portfolio directory
    base_dir = os.path.join(os.getcwd(), "projects", "portfolio")
    full_path = os.path.join(base_dir, path)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    with open(full_path, "w") as f:
        f.write(content)
    return f"Wrote code to {full_path}"

@tool
def run_command(cmd: str, cwd: str = ".") -> str:
    """Run a system command
    
    Args:
        cmd: The command to execute
        cwd: The working directory for command execution (default: current directory)
    """
    out = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    return out.stdout or out.stderr

model = load_model("LiteLLMModel", os.getenv("BRAIN_MODEL", "gpt-4o"))
brain_agent = CodeAgent(
    tools=[write_code, run_command],
    model=model,
    name="BrainAgent",
    max_steps=8,
)

"""Brain Agent Factory - Creates project-scoped agent instances.

This module provides a factory to create Brain agents bound to specific project roots
with configurable models. No global state, full isolation between concurrent runs.
"""

from smolagents import CodeAgent, tool
from smolagents.cli import load_model
import os
import sys
import pathlib
import subprocess
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass


@dataclass
class BrainConfig:
    """Configuration for Brain agent instances."""
    model_type: str = "LiteLLMModel"
    model_id: str = "gpt-4o"
    provider: Optional[str] = None
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    max_steps: int = 15
    temperature: float = 0.7
    verbosity: int = 1
    timeout: int = 180  # seconds for operations


def validate_path_safety(project_root: pathlib.Path, target_path: str) -> pathlib.Path:
    """Ensure target path is within project root to prevent directory traversal.
    
    Args:
        project_root: The project root directory
        target_path: The target path to validate (relative or absolute)
        
    Returns:
        Resolved absolute path within project root
        
    Raises:
        ValueError: If path escapes project root
    """
    # Resolve project root to absolute path
    project_root = project_root.resolve()
    
    # Handle absolute paths by making them relative to project root
    if pathlib.Path(target_path).is_absolute():
        target_path = pathlib.Path(target_path).name
    
    # Resolve target path relative to project root
    resolved = (project_root / target_path).resolve()
    
    # Ensure resolved path is within project root
    try:
        resolved.relative_to(project_root)
    except ValueError:
        raise ValueError(
            f"Security: Path '{target_path}' escapes project root '{project_root}'"
        )
    
    return resolved


def create_brain_agent(
    project_root: str | pathlib.Path,
    config: Optional[BrainConfig] = None,
    run_id: Optional[str] = None
) -> CodeAgent:
    """Create a Brain agent instance bound to a specific project.
    
    Args:
        project_root: Absolute path to the project directory
        config: Brain configuration (uses defaults if None)
        run_id: Unique identifier for this run (for artifacts/logs)
        
    Returns:
        CodeAgent instance with project-scoped tools
    """
    if config is None:
        config = BrainConfig()
    
    # Ensure project root is absolute
    project_root = pathlib.Path(project_root).resolve()
    if not project_root.exists():
        project_root.mkdir(parents=True, exist_ok=True)
    
    # Store run_id for artifact naming
    _run_id = run_id or "default"
    
    # Create closures that capture project_root
    
    @tool
    def write_code(path: str, content: str) -> str:
        """Write code to a file within the project.
        
        Args:
            path: File path relative to project root
            content: Code content to write
            
        Returns:
            Success message with absolute path
        """
        try:
            full_path = validate_path_safety(project_root, path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return f"Successfully wrote {len(content)} bytes to {full_path.relative_to(project_root)}"
        except Exception as e:
            return f"Error writing {path}: {e}"
    
    @tool
    def read_existing_code(path: str) -> str:
        """Read existing code from a file within the project.
        
        Args:
            path: File path relative to project root
            
        Returns:
            File content or error message
        """
        try:
            full_path = validate_path_safety(project_root, path)
            
            if not full_path.exists():
                return f"File not found: {path}"
            
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return f"Content of {path} ({len(content)} bytes):\n{content}"
        except Exception as e:
            return f"Error reading {path}: {e}"
    
    @tool
    def list_project_files(pattern: str = "**/*") -> str:
        """List files in the project directory matching a pattern.
        
        Args:
            pattern: Glob pattern (default: all files)
            
        Returns:
            Newline-separated list of relative file paths
        """
        try:
            files = []
            for path in project_root.glob(pattern):
                if path.is_file():
                    rel_path = path.relative_to(project_root)
                    files.append(str(rel_path))
            
            if not files:
                return f"No files found matching pattern: {pattern}"
            
            return f"Project files ({len(files)} total):\n" + "\n".join(sorted(files))
        except Exception as e:
            return f"Error listing files: {e}"
    
    @tool
    def run_command(cmd: str, cwd: str = ".") -> str:
        """Run a shell command within the project sandbox.
        
        Args:
            cmd: Command to execute
            cwd: Working directory relative to project root
            
        Returns:
            Command output (stdout + stderr)
        """
        try:
            # Validate working directory
            work_dir = validate_path_safety(project_root, cwd)
            
            # Use current interpreter to avoid venv mismatches
            if cmd.startswith("python ") or cmd.startswith("pip "):
                cmd = cmd.replace("python ", f'"{sys.executable}" ', 1)
                cmd = cmd.replace("pip ", f'"{sys.executable}" -m pip ', 1)
            
            # Execute with timeout
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                shell=True,
                capture_output=True,
                text=True,
                timeout=config.timeout
            )
            
            output = result.stdout or result.stderr or "(no output)"
            return f"Command: {cmd}\nExit code: {result.returncode}\nOutput:\n{output}"
        except subprocess.TimeoutExpired:
            return f"Command timed out after {config.timeout}s: {cmd}"
        except Exception as e:
            return f"Error executing command: {e}"
    
    # Load model with configuration
    model_kwargs = {}
    if config.provider:
        model_kwargs["provider"] = config.provider
    if config.api_base:
        model_kwargs["api_base"] = config.api_base
    if config.api_key:
        model_kwargs["api_key"] = config.api_key
    
    model = load_model(config.model_type, config.model_id, **model_kwargs)
    
    # Create agent with project-scoped tools
    # Note: CodeAgent doesn't support verbosity parameter directly
    # Agent name must be a valid Python identifier (no hyphens)
    agent_name = f"BrainAgent_{_run_id.replace('-', '_')}"
    agent = CodeAgent(
        tools=[write_code, read_existing_code, list_project_files, run_command],
        model=model,
        name=agent_name,
        max_steps=config.max_steps
    )
    
    # Store verbosity level as agent attribute for logging control
    agent.verbosity = config.verbosity
    
    return agent


def detect_existing_stack(project_root: pathlib.Path) -> Dict[str, Any]:
    """Detect existing stack in the project directory.
    
    Args:
        project_root: Project root directory
        
    Returns:
        Dictionary with stack information
    """
    stack = {
        "frontend": None,
        "backend": None,
        "package_managers": [],
        "frameworks": [],
        "has_content": False
    }
    
    # Check for frontend indicators
    if (project_root / "frontend").exists():
        stack["has_content"] = True
        
        if (project_root / "frontend" / "package.json").exists():
            stack["frontend"] = "node"
            stack["package_managers"].append("npm")
            
            # Check for framework indicators in package.json
            try:
                import json
                with open(project_root / "frontend" / "package.json") as f:
                    pkg = json.load(f)
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    
                    if "react" in deps:
                        stack["frameworks"].append("react")
                    if "vue" in deps:
                        stack["frameworks"].append("vue")
                    if "vite" in deps:
                        stack["frameworks"].append("vite")
            except:
                pass
        
        elif (project_root / "frontend" / "index.html").exists():
            stack["frontend"] = "static"
    
    # Check for backend indicators
    if (project_root / "backend").exists():
        stack["has_content"] = True
        
        if (project_root / "backend" / "requirements.txt").exists():
            stack["backend"] = "python"
            stack["package_managers"].append("pip")
            
            # Check for framework indicators
            try:
                with open(project_root / "backend" / "requirements.txt") as f:
                    reqs = f.read().lower()
                    if "flask" in reqs:
                        stack["frameworks"].append("flask")
                    if "fastapi" in reqs:
                        stack["frameworks"].append("fastapi")
                    if "django" in reqs:
                        stack["frameworks"].append("django")
            except:
                pass
        
        elif (project_root / "backend" / "package.json").exists():
            stack["backend"] = "node"
            stack["package_managers"].append("npm")
    
    return stack

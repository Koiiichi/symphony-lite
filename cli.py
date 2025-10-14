"""Symphony-Lite CLI - Agentic build-test-repair loop for any project.

Supports project-agnostic workflows with configurable models.
"""

import os
import sys
import typer
import pathlib
from rich.console import Console
from rich.panel import Panel
from typing import Optional

app = typer.Typer(help="Symphony-Lite CLI - Agentic build-test-repair loop for any project")
console = Console()


def chroot_to_repo():
    """Ensure we're running from the symphony-lite repo root."""
    cli_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if we're in the right directory
    if not os.path.exists(os.path.join(cli_dir, "orchestrator.py")):
        console.print("[red]Error: Please use 'python symphony.py' instead of calling cli.py directly[/red]")
        console.print("[dim]Symphony.py handles virtual environment setup automatically[/dim]")
        raise typer.Exit(1)
    
    os.chdir(cli_dir)
    sys.path.insert(0, os.getcwd())


@app.command()
def run(
    project: str = typer.Option(..., "--project", help="Path to the target project folder (absolute or relative)"),
    goal: str = typer.Option(..., "--goal", help="Natural language goal/prompt describing what to build"),
    fe_port: int = typer.Option(3000, "--fe-port", help="Frontend server port"),
    be_port: int = typer.Option(5000, "--be-port", help="Backend server port"),
    steps: int = typer.Option(3, "--steps", help="Max test-and-fix passes (1=quick, 3=standard, 5=thorough)"),
    brain_model: str = typer.Option("gpt-4o", "--brain-model", help="Model ID for Brain agent (e.g., gpt-4o, claude-3-opus)"),
    open_browser: bool = typer.Option(False, "--open", help="Auto-open browser on successful completion"),
    temperature: float = typer.Option(0.7, "--temperature", help="Model temperature (0.0-1.0)"),
    max_agent_steps: int = typer.Option(15, "--max-agent-steps", help="Maximum steps for Brain agent per generation"),
    verbosity: int = typer.Option(1, "--verbosity", help="Agent verbosity level (0=silent, 1=normal, 2=verbose)"),
):
    """Run the agentic build-test-repair loop on any project folder.
    
    This command works on:
    - Empty folders (scaffolds new application)
    - Existing portfolios (enhances and refines)
    - Any web application (dashboards, ecommerce, etc.)
    
    Examples:
        # Quick prototype
        python symphony.py run --project ./my-app --goal "Landing page" --steps 1
        
        # Standard quality
        python symphony.py run --project projects/portfolio --goal "Dark theme portfolio"
        
        # High quality with browser open
        python symphony.py run --project ./dashboard --goal "Admin dashboard" --steps 5 --open
        
        # Use different model
        python symphony.py run --project ./app --goal "..." --brain-model claude-3-opus
    """
    chroot_to_repo()
    
    # Import orchestrator and config
    from orchestrator import run_workflow
    from agents.brain_agent_factory import BrainConfig
    
    project_path = str(pathlib.Path(project).resolve())
    
    # Validate project path exists or can be created
    project_path_obj = pathlib.Path(project_path)
    if not project_path_obj.exists():
        console.print(f"[yellow]Project path does not exist, will create: {project_path}[/yellow]")
        try:
            project_path_obj.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            console.print(f"[red]Error creating project directory: {e}[/red]")
            raise typer.Exit(1)
    
    # Create Brain config
    brain_config = BrainConfig(
        model_id=brain_model,
        max_steps=max_agent_steps,
        temperature=temperature,
        verbosity=verbosity
    )
    
    console.print(Panel.fit(
        f"[bold cyan]Project:[/bold cyan] {project_path}\n"
        f"[bold cyan]Goal:[/bold cyan] {goal}\n"
        f"[bold cyan]Ports:[/bold cyan] Frontend: {fe_port}, Backend: {be_port}\n"
        f"[bold cyan]Max Passes:[/bold cyan] {steps} test-and-fix iterations\n"
        f"[bold cyan]Brain Model:[/bold cyan] {brain_model}\n"
        f"[bold cyan]Browser:[/bold cyan] {'Will open on success' if open_browser else 'Will not open'}",
        title="Symphony-Lite Workflow"
    ))
    
    try:
        # Run workflow
        result = run_workflow(
            project_path,
            goal,
            fe_port,
            be_port,
            steps,
            brain_config=brain_config,
            open_browser=open_browser
        )
        
        # Print results
        if result.get("final_status") == "success":
            console.print("\n[bold green]Workflow completed successfully![/bold green]")
            raise typer.Exit(0)
        elif result.get("final_status") == "completed_max_iterations":
            console.print("\n[bold yellow]Workflow completed all iterations.[/bold yellow]")
            console.print("[dim]Consider running again with more --steps for further refinement[/dim]")
            raise typer.Exit(0)
        else:
            console.print("\n[bold red]Workflow completed with issues.[/bold red]")
            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
            raise typer.Exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Workflow interrupted by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"\n[red]Workflow failed with error: {e}[/red]")
        if verbosity >= 2:
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        raise typer.Exit(1)


@app.command()
def validate(
    project: str = typer.Option(..., "--project", help="Path to the project folder to validate")
):
    """Validate project structure and configuration."""
    chroot_to_repo()
    
    project_path = pathlib.Path(project).resolve()
    
    if not project_path.exists():
        console.print(f"[red]Error: Project path does not exist: {project_path}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Validating project at:[/cyan] {project_path}")
    
    # Check for required structure
    frontend_dir = project_path / "frontend"
    backend_dir = project_path / "backend"
    
    issues = []
    
    if not frontend_dir.exists():
        issues.append("Missing frontend/ directory")
    else:
        if not (frontend_dir / "index.html").exists():
            issues.append("Missing frontend/index.html")
    
    if not backend_dir.exists():
        issues.append("Missing backend/ directory")
    else:
        if not (backend_dir / "app.py").exists():
            issues.append("Missing backend/app.py")
        if not (backend_dir / "requirements.txt").exists():
            issues.append("Missing backend/requirements.txt")
    
    if issues:
        console.print("\n[yellow]Project structure issues:[/yellow]")
        for issue in issues:
            console.print(f"  - {issue}")
        console.print("\n[dim]Tip: Symphony-Lite can scaffold these files automatically on first run[/dim]")
    else:
        console.print("\n[green]Project structure is valid![/green]")
    
    # Detect stack
    try:
        from agents.brain_agent_factory import detect_existing_stack
        stack = detect_existing_stack(project_path)
        
        console.print("\n[cyan]Detected stack:[/cyan]")
        console.print(f"  Frontend: {stack.get('frontend', 'unknown')}")
        console.print(f"  Backend: {stack.get('backend', 'unknown')}")
        if stack.get('frameworks'):
            console.print(f"  Frameworks: {', '.join(stack['frameworks'])}")
    except ImportError:
        pass
    
    raise typer.Exit(0 if not issues else 1)


@app.command()
def info():
    """Display Symphony-Lite information and configuration."""
    console.print(Panel.fit(
        "[bold cyan]Symphony-Lite[/bold cyan]\n\n"
        "Agentic build-test-repair loop for web applications\n\n"
        "[dim]Version:[/dim] 2.0.0 (Refactored)\n"
        "[dim]Python:[/dim] " + sys.version.split()[0] + "\n"
        "[dim]Working Directory:[/dim] " + os.getcwd(),
        title="Info"
    ))
    
    # Check for required dependencies
    console.print("\n[cyan]Dependencies:[/cyan]")
    
    deps = [
        ("smolagents", "Brain agent framework"),
        ("openai", "GPT-4 vision and code generation"),
        ("helium", "Browser automation"),
        ("flask", "Backend server"),
        ("flask_cors", "CORS support"),
        ("rich", "Terminal UI"),
        ("typer", "CLI framework"),
    ]
    
    for module, description in deps:
        try:
            __import__(module.replace("-", "_"))
            console.print(f"  [green]OK[/green] {module:20} - {description}")
        except ImportError:
            console.print(f"  [red]MISSING[/red] {module:20} - {description} [red](missing)[/red]")
    
    console.print("\n[dim]Run 'pip install -r requirements.txt' to install missing dependencies[/dim]")


if __name__ == "__main__":
    app()

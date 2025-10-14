# cli.py
import os, sys, typer, pathlib, json
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(help="Symphony-Lite CLI - Agentic build-test-repair loop for any project")
console = Console()

def chroot_to_repo():
    """Ensure we're running from the symphony-lite repo root."""
    cli_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if we're in the right directory (should have orchestrator.py)
    if not os.path.exists(os.path.join(cli_dir, "orchestrator.py")):
        console.print("[red]Error: Please use 'python symphony.py' instead of calling cli.py directly[/red]")
        console.print("[dim]Symphony.py handles virtual environment setup automatically[/dim]")
        raise typer.Exit(1)
    
    os.chdir(cli_dir)
    sys.path.insert(0, os.getcwd())

@app.command()
def run(
    project: str = typer.Option(..., "--project", help="Path to the target project folder"),
    goal: str = typer.Option(..., "--goal", help="Natural language goal/prompt"),
    fe_port: int = typer.Option(3000, "--fe-port", help="Frontend port"),
    be_port: int = typer.Option(5000, "--be-port", help="Backend port"),
    steps: int = typer.Option(1, "--steps", help="Max improvement iterations")
):
    """Run the agentic build-test-repair loop on any project folder."""
    chroot_to_repo()
    
    # Import here to avoid import issues
    from orchestrator import run_workflow
    
    project_path = str(pathlib.Path(project).resolve())
    
    # Validate project exists
    if not pathlib.Path(project_path).exists():
        console.print(f"[red]Error: Project path does not exist: {project_path}[/red]")
        raise typer.Exit(1)
    
    console.print(Panel.fit(
        f"[bold cyan]Project:[/bold cyan] {project_path}\n[bold cyan]Goal:[/bold cyan] {goal}\n[bold cyan]Ports:[/bold cyan] FE:{fe_port} BE:{be_port}\n[bold cyan]Max Steps:[/bold cyan] {steps}",
        title="Symphony-Lite Workflow"
    ))
    
    try:
        result = run_workflow(project_path, goal, fe_port, be_port, steps)
        console.print(Panel.fit(
            json.dumps(result, indent=2), 
            title="[green]Workflow Summary[/green]"
        ))
    except Exception as e:
        console.print(Panel.fit(
            f"[red]Error: {str(e)}[/red]", 
            title="[red]Workflow Failed[/red]"
        ))
        raise typer.Exit(1)

@app.command()
def validate(
    project: str = typer.Option(..., "--project", help="Path to validate")
):
    """Validate that a project has the expected structure."""
    project_path = pathlib.Path(project).resolve()
    
    console.print(f"[cyan]Validating project structure at:[/cyan] {project_path}")
    
    required_paths = [
        project_path / "frontend",
        project_path / "backend",
        project_path / "backend" / "app.py",
        project_path / "backend" / "requirements.txt"
    ]
    
    all_valid = True
    for path in required_paths:
        if path.exists():
            console.print(f"[green]PASS[/green] {path.relative_to(project_path)}")
        else:
            console.print(f"[red]FAIL[/red] {path.relative_to(project_path)} (missing)")
            all_valid = False
    
    if all_valid:
        console.print("[green]Project structure is valid![/green]")
    else:
        console.print("[red]Project structure is incomplete.[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
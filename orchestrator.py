"""Orchestrator - Coordinates Brain, Runner, and Sensory agents.

Refactored to use Brain agent factory for isolated, project-scoped instances.
"""

from rich.console import Console
from rich.panel import Panel
from rich import print as rprint
import json
import time
import sys
import os
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Import new factory and contract
from agents.brain_agent_factory import create_brain_agent, BrainConfig, detect_existing_stack
from agents.sensory_contract import SensoryReport
from agents.brain_instructions import get_generation_instructions, get_fix_instructions
from runner import run_servers
from agents.sensory_agent import inspect_site

console = Console()


def run_workflow(
    project_path: str,
    goal: str,
    fe_port: int,
    be_port: int,
    steps: int = 3,
    brain_config: Optional[BrainConfig] = None,
    run_id: Optional[str] = None,
    open_browser: bool = False
) -> Dict[str, Any]:
    """Run the complete agentic workflow with clean, non-conflicting output.
    
    Args:
        project_path: Absolute path to project directory
        goal: Natural language goal from user
        fe_port: Frontend server port
        be_port: Backend server port
        steps: Maximum test-and-fix iterations
        brain_config: Brain agent configuration (uses defaults if None)
        run_id: Unique run identifier (generated if None)
        open_browser: Whether to open browser on success
        
    Returns:
        Summary dictionary with results
    """
    
    # Generate run ID if not provided
    if run_id is None:
        run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Use default config if not provided
    if brain_config is None:
        brain_config = BrainConfig()
    
    # Ensure project path is absolute
    project_path = str(Path(project_path).resolve())
    
    summary = {
        "project_path": project_path,
        "goal": goal,
        "run_id": run_id,
        "steps_completed": 0,
        "passes": {},
        "final_status": "unknown"
    }
    
    def log_step(step_name: str, status: str, details: str = ""):
        """Log a workflow step with consistent formatting."""
        status_color = {
            "running": "yellow",
            "complete": "green",
            "failed": "red",
            "success": "green"
        }.get(status.lower(), "white")
        
        details_part = f" - {details}" if details else ""
        console.print(f"[{status_color}]{step_name}:[/{status_color}] {status.upper()}{details_part}")
    
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]Run ID:[/bold cyan] {run_id}\n"
        f"[bold cyan]Project:[/bold cyan] {project_path}\n"
        f"[bold cyan]Goal:[/bold cyan] {goal}\n"
        f"[bold cyan]Max Passes:[/bold cyan] {steps}",
        title="Symphony-Lite Workflow"
    ))
    console.print()
    
    # Detect existing stack
    log_step("Stack Detection", "running", "Analyzing project structure")
    stack = detect_existing_stack(Path(project_path))
    
    if stack["has_content"]:
        frameworks = ", ".join(stack.get("frameworks", ["unknown"]))
        log_step("Stack Detection", "complete", 
                f"Found {stack.get('frontend', 'unknown')} frontend, {stack.get('backend', 'unknown')} backend ({frameworks})")
    else:
        log_step("Stack Detection", "complete", "Empty project - will scaffold")
    
    # Create Brain agent instance for this run
    log_step("Brain Agent", "running", "Creating project-scoped agent")
    try:
        brain = create_brain_agent(project_path, brain_config, run_id)
        log_step("Brain Agent", "complete", f"Agent ready (max {brain_config.max_steps} steps)")
    except Exception as e:
        log_step("Brain Agent", "failed", str(e))
        summary["error"] = f"Brain agent creation failed: {e}"
        summary["final_status"] = "failed"
        return summary
    
    # Step 1: Brain generates/updates code
    log_step("Code Generation", "running", "Generating code from goal")
    try:
        instructions = get_generation_instructions(project_path, goal, stack)
        brain.run(instructions)
        log_step("Code Generation", "complete", "Initial code generated")
    except Exception as e:
        log_step("Code Generation", "failed", str(e))
        summary["error"] = f"Code generation failed: {e}"
        summary["final_status"] = "failed"
        return summary
    
    # Step 2: Start servers
    log_step("Server Startup", "running", "Starting development servers")
    try:
        be_proc, fe_proc = run_servers(project_path, fe_port, be_port)
        
        frontend_url = f"http://localhost:{fe_port}"
        backend_url = f"http://localhost:{be_port}"
        
        console.print()
        console.print(Panel.fit(
            f"[bold green]Servers Ready[/bold green]\n\n"
            f"[cyan]Frontend:[/cyan] {frontend_url}\n"
            f"[cyan]Backend:[/cyan] {backend_url}",
            title="URLs"
        ))
        console.print()
        
        log_step("Server Startup", "complete", f"Servers running on ports {fe_port} & {be_port}")
        summary["urls"] = {"frontend": frontend_url, "backend": backend_url}
    except Exception as e:
        log_step("Server Startup", "failed", str(e))
        summary["error"] = f"Server startup failed: {e}"
        summary["final_status"] = "failed"
        return summary
    
    # Step 3: Iterative improvement loop
    final_report = None
    
    for i in range(steps):
        step_num = i + 1
        
        # Sensory pass
        log_step("Sensory Testing", "running", f"Testing application (pass {step_num} of {steps})")
        try:
            report: SensoryReport = inspect_site(frontend_url, run_id)
            
            failing_gates = report.get_failing_gates()
            
            log_step("Sensory Testing", "complete",
                    f"Alignment: {report.alignment_score:.2f}, "
                    f"Spacing: {report.spacing_score:.2f}, "
                    f"Contrast: {report.contrast_score:.2f}, "
                    f"Form: {'PASS' if report.interaction.contact_submitted else 'FAIL'} "
                    f"(pass {step_num} of {steps})")
            
            if failing_gates:
                console.print(f"[yellow]Failing gates: {', '.join(failing_gates)}[/yellow]")
            
            summary["passes"][f"pass_{step_num}"] = report.to_dict()
            summary["steps_completed"] = step_num
            final_report = report
            
        except Exception as e:
            log_step("Sensory Testing", "failed", str(e))
            summary["passes"][f"pass_{step_num}"] = {"error": str(e)}
            break
        
        # Check if we should stop
        if report.passes_all_gates():
            log_step("Quality Gates", "success", f"All gates passed after {step_num} of {steps} passes!")
            summary["final_status"] = "success"
            break
        
        # If not the last step, apply fixes
        if step_num < steps:
            log_step("Applying Fixes", "running", f"Generating improvements (pass {step_num} of {steps})")
            try:
                fix_instructions = get_fix_instructions(project_path, report, goal)
                brain.run(fix_instructions)
                log_step("Applying Fixes", "complete", f"Improvements applied (pass {step_num} of {steps})")
                time.sleep(3)  # Give time for file changes to take effect
            except Exception as e:
                log_step("Applying Fixes", "failed", str(e))
                break
        else:
            log_step("Iteration Limit", "complete", f"Completed all {steps} passes")
            summary["final_status"] = "completed_max_iterations"
    
    console.print()
    
    # Cleanup
    try:
        be_proc.terminate()
        fe_proc.join(timeout=2)
        console.print("[dim]Development servers terminated[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning: Server cleanup issue: {e}[/yellow]")
    
    # Open browser if requested and successful
    if open_browser and final_report and final_report.passes_all_gates():
        try:
            webbrowser.open(frontend_url)
            console.print(f"[green]Opened {frontend_url} in browser[/green]")
        except Exception as e:
            console.print(f"[yellow]Could not open browser: {e}[/yellow]")
    
    # Print final summary
    if final_report:
        artifacts_path = Path("artifacts") / run_id
        screenshots_count = len(final_report.screens)
        
        status_emoji = "SUCCESS" if final_report.passes_all_gates() else "NEEDS WORK"
        status_color = "green" if final_report.passes_all_gates() else "yellow"
        
        console.print()
        console.print(Panel.fit(
            f"[bold {status_color}]{status_emoji}[/bold {status_color}]\n\n"
            f"[cyan]URL:[/cyan] {frontend_url}\n"
            f"[cyan]Status:[/cyan] {final_report.status}\n"
            f"[cyan]Alignment:[/cyan] {final_report.alignment_score:.2f} / 0.90\n"
            f"[cyan]Spacing:[/cyan] {final_report.spacing_score:.2f} / 0.90\n"
            f"[cyan]Contrast:[/cyan] {final_report.contrast_score:.2f} / 0.75\n"
            f"[cyan]Form Working:[/cyan] {'Yes' if final_report.interaction.contact_submitted else 'No'}\n"
            f"[cyan]Visible Sections:[/cyan] {', '.join(final_report.visible_sections) or 'none'}\n"
            f"[cyan]Artifacts:[/cyan] {artifacts_path}\n"
            f"[cyan]Screenshots:[/cyan] {screenshots_count} saved\n\n"
            f"[dim]Next steps:[/dim]\n"
            f"[dim]- Review artifacts in {artifacts_path}[/dim]\n"
            f"[dim]- Run again with --steps {steps + 2} for more refinement[/dim]\n"
            f"[dim]- Use --open to auto-open browser on success[/dim]",
            title=f"Run {run_id} Complete"
        ))
        
        summary["final_report"] = final_report.to_dict()
        summary["artifacts_path"] = str(artifacts_path)
    
    return summary


# Legacy main for backward compatibility
def main():
    """Legacy main function - redirects to CLI for better UX."""
    console.print(Panel.fit(
        "[yellow]Legacy main() detected![/yellow]\n\n"
        "For better experience, use the CLI:\n"
        "[cyan]python symphony.py run --project projects/portfolio --goal 'Your goal here'[/cyan]",
        title="Please use CLI"
    ))
    
    # Run with default parameters for backward compatibility
    goal = "Create a dark-themed portfolio with projects grid and contact form"
    result = run_workflow("projects/portfolio", goal, 3000, 5000, 3)
    rprint(result)


if __name__ == "__main__":
    main()

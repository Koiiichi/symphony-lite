"""Orchestrator - Coordinates Brain, Runner, and Sensory agents.

Refactored to use Brain agent factory for isolated, project-scoped instances.
Uses capability-based expectations and pluggable gate engine.
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
from agents.brain_agent_factory import create_brain_agent, BrainConfig, SensoryConfig, detect_existing_stack
from agents.sensory_contract import SensoryReport
from agents.brain_instructions import get_generation_instructions
from agents.goal_interpreter import build_expectations
from gates.engine import evaluate as evaluate_gates, get_fix_instructions as get_gate_fix_instructions
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
    sensory_config: Optional['SensoryConfig'] = None,
    run_id: Optional[str] = None,
    open_browser: bool = False,
    expectations_file: Optional[str] = None
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
    
    if sensory_config is None:
        sensory_config = SensoryConfig()
    
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
    
    # Build expectations from goal
    log_step("Goal Interpretation", "running", "Deriving expectations from goal")
    expectations = build_expectations(goal, page_type_hint=None, stack=stack, expectations_file=expectations_file)
    log_step("Goal Interpretation", "complete", f"Expectations: {len(expectations.get('capabilities', {}))} capabilities, {len(expectations.get('interactions', []))} interactions")
    
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
            sensory_model_config = {"model_id": sensory_config.model_id}
            report: SensoryReport = inspect_site(frontend_url, run_id, sensory_model_config, expectations)
            
            # Evaluate gates
            gate_result = evaluate_gates(expectations, report.to_dict())
            report.failing_reasons = gate_result["failing_reasons"]
            
            log_step("Sensory Testing", "complete",
                    f"Alignment: {report.alignment_score:.2f}, "
                    f"Spacing: {report.spacing_score:.2f}, "
                    f"Contrast: {report.contrast_score:.2f} "
                    f"(pass {step_num} of {steps})")
            
            if gate_result["failing_reasons"]:
                console.print(f"[yellow]Failing gates: {', '.join(gate_result['failing_reasons'])}[/yellow]")
            
            # Add model IDs to report
            report.model_ids["brain"] = brain_config.model_id
            report.model_ids["sensory"] = sensory_config.model_id
            
            # Save report to artifacts
            artifacts_dir = Path("artifacts") / run_id
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            with open(artifacts_dir / "report.json", "w") as f:
                json.dump(report.to_dict(), f, indent=2)
            
            summary["passes"][f"pass_{step_num}"] = report.to_dict()
            summary["steps_completed"] = step_num
            final_report = report
            
        except Exception as e:
            log_step("Sensory Testing", "failed", str(e))
            summary["passes"][f"pass_{step_num}"] = {"error": str(e)}
            break
        
        # Check if we should stop
        if gate_result["passed"]:
            log_step("Quality Gates", "success", f"All gates passed after {step_num} of {steps} passes!")
            summary["final_status"] = "success"
            break
        
        # If not the last step, apply fixes
        if step_num < steps:
            log_step("Applying Fixes", "running", f"Generating improvements (pass {step_num} of {steps})")
            try:
                fix_instructions = get_gate_fix_instructions(expectations, report.to_dict(), gate_result["failing_reasons"])
                full_instructions = f"""
You are fixing issues in the project at: {project_path}

ORIGINAL GOAL:
{goal}

{fix_instructions}

PROCESS:
1. Use list_project_files() to see the current structure
2. Use read_existing_code() to examine files that need changes
3. Apply targeted fixes using write_code()
4. Ensure all changes are consistent with the existing stack

Start by examining the relevant files.
"""
                brain.run(full_instructions)
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
        
        gate_result = evaluate_gates(expectations, final_report.to_dict())
        passed_all = gate_result["passed"]
        
        status_emoji = "SUCCESS" if passed_all else "NEEDS WORK"
        status_color = "green" if passed_all else "yellow"
        
        # Build panel lines
        panel_lines = [
            f"[bold {status_color}]{status_emoji}[/bold {status_color}]\n",
            f"[cyan]URL:[/cyan] {frontend_url}",
            f"[cyan]Status:[/cyan] {final_report.status}",
            f"[cyan]Alignment:[/cyan] {final_report.alignment_score:.2f} / 0.90",
            f"[cyan]Spacing:[/cyan] {final_report.spacing_score:.2f} / 0.90",
            f"[cyan]Contrast:[/cyan] {final_report.contrast_score:.2f} / 0.75",
        ]
        
        # Add interaction results
        for interaction_id, interaction_data in final_report.interactions.items():
            attempted = interaction_data.get("attempted", False)
            http_status = interaction_data.get("http_status", "N/A")
            success = interaction_data.get("success_banner", False)
            error = interaction_data.get("error_banner", False)
            
            if attempted:
                status_str = "ok" if (http_status and 200 <= http_status < 300 and success and not error) else "fail"
                panel_lines.append(f"[cyan]{interaction_id}:[/cyan] {status_str} (status={http_status})")
        
        panel_lines.extend([
            f"[cyan]Visible Sections:[/cyan] {', '.join(final_report.visible_sections) or 'none'}",
            f"[cyan]Artifacts:[/cyan] {artifacts_path}",
            f"[cyan]Screenshots:[/cyan] {screenshots_count} saved",
            f"[cyan]Models:[/cyan] Brain: {final_report.model_ids.get('brain', 'N/A')}, Sensory: {final_report.model_ids.get('sensory', 'N/A')}",
            "",
            "[dim]Next steps:[/dim]",
            f"[dim]- Review artifacts in {artifacts_path}[/dim]",
            f"[dim]- Check report.json for full details[/dim]",
        ])
        
        if not passed_all:
            panel_lines.append(f"[dim]- Run again with --steps {steps + 2} for more refinement[/dim]")
        
        panel_lines.append("[dim]- Use --open to auto-open browser on success[/dim]")
        
        console.print()
        console.print(Panel.fit("\n".join(panel_lines), title=f"Run {run_id} Complete"))
        
        summary["final_report"] = final_report.to_dict()
        summary["artifacts_path"] = str(artifacts_path)
        
        # Set exit code based on gate result
        if not passed_all:
            summary["exit_code"] = 1
        else:
            summary["exit_code"] = 0
    
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

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TextColumn
from rich.panel import Panel
from rich import print as rprint
import json, time
from runner import run_servers

console = Console()

def run_workflow(project_path: str, goal: str, fe_port: int, be_port: int, steps: int = 1):
    """Run the complete agentic workflow with Rich progress display."""
    summary = {"project_path": project_path, "goal": goal, "steps_completed": 0, "passes": {}}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        
        # Step 1: Brain generates/updates code
        t_gen = progress.add_task("Brain: generating/updating code...", total=None)
        try:
            brain_generate(project_path, goal)
            progress.update(t_gen, description="Brain: code generation complete", completed=1)
        except Exception as e:
            progress.update(t_gen, description=f"Brain: generation failed - {e}", completed=1)
            summary["error"] = f"Brain generation failed: {e}"
            return summary
        
        # Step 2: Start servers
        t_run = progress.add_task("Runner: starting servers...", total=None)
        try:
            be_proc, fe_proc = run_servers(project_path, fe_port, be_port)
            progress.update(t_run, description="Runner: servers started", completed=1)
            summary["servers"] = {"backend": "started", "frontend": "started"}
        except Exception as e:
            progress.update(t_run, description=f"Runner: server start failed - {e}", completed=1)
            summary["error"] = f"Server startup failed: {e}"
            return summary
        
        # Step 3: Iterative improvement loop
        for i in range(steps):
            step_num = i + 1
            
            # Sensory pass
            t_sense = progress.add_task(f"Sensory: visual + functional pass #{step_num}...", total=None)
            try:
                report = inspect_site(f"http://localhost:{fe_port}", project_path)
                progress.update(t_sense, description=f"Sensory: pass #{step_num} complete", completed=1)
                summary["passes"][f"pass_{step_num}"] = report
                summary["steps_completed"] = step_num
            except Exception as e:
                progress.update(t_sense, description=f"Sensory: pass #{step_num} failed - {e}", completed=1)
                summary["passes"][f"pass_{step_num}"] = {"error": str(e)}
                break
            
            # Check if we should stop (good alignment and working form)
            alignment_score = report.get("alignment_score", 0)
            form_working = report.get("interaction", {}).get("submitted", False)
            
            if report.get("status") == "pass" and alignment_score >= 0.9 and form_working:
                console.print(f"[green]Pass #{step_num} succeeded! Alignment: {alignment_score:.2f}, Form working: {form_working}[/green]")
                break
            
            # If not the last step, apply fixes
            if step_num < steps:
                t_fix = progress.add_task(f"Brain: applying fixes #{step_num}...", total=None)
                try:
                    brain_fix(project_path, report, goal)
                    progress.update(t_fix, description=f"Brain: fixes #{step_num} applied", completed=1)
                    time.sleep(3)  # Give time for file changes to take effect
                except Exception as e:
                    progress.update(t_fix, description=f"Brain: fixes #{step_num} failed - {e}", completed=1)
                    break
            else:
                console.print(f"[yellow]Reached max steps ({steps}). Final scores - Alignment: {alignment_score:.2f}, Form: {form_working}[/yellow]")
    
    # Cleanup
    try:
        be_proc.terminate()
        fe_proc.join(timeout=2)  # Give thread time to cleanup
        console.print("[dim]Servers terminated[/dim]")
    except Exception as e:
        console.print(f"[yellow]Warning: Server cleanup issue: {e}[/yellow]")
    
    return summary

def brain_generate(project_path: str, goal: str):
    """Generate initial code using brain agent."""
    # Import brain agent here to avoid circular imports
    try:
        from agents.brain_agent import brain_agent
        instructions = f"""
        Generate/update files for project at: {project_path}
        Goal: {goal}
        
        Please create or update the following files as needed:
        - frontend/index.html: Complete HTML with embedded CSS and JavaScript
        - frontend/package.json: Package configuration if using Node.js features
        - backend/app.py: Flask backend with proper CORS and API endpoints
        - backend/requirements.txt: Python dependencies
        
        Use the write_code function to save each file. Ensure paths are relative to the project folder.
        Make sure the contact form actually submits to /api/contact endpoint and shows success/error states.
        """
        return brain_agent.run(instructions)
    except ImportError:
        console.print("[yellow]Warning: Brain agent not available, skipping code generation[/yellow]")
        return "Brain agent unavailable"

def brain_fix(project_path: str, sensory_report: dict, goal: str):
    """Apply fixes based on sensory feedback."""
    try:
        from agents.brain_agent import brain_agent
        
        feedback_text = json.dumps(sensory_report, indent=2)
        fix_instructions = f"""
        Based on sensory feedback, improve the project at: {project_path}
        Original goal: {goal}
        
        Feedback report:
        {feedback_text}
        
        Please fix the following issues:
        1. If alignment_score < 0.9: improve CSS layout, spacing, and visual hierarchy
        2. If form submission failed: fix JavaScript form handling and API integration
        3. If visual sections are missing: ensure all key components are visible
        4. Apply any specific suggestions from the feedback
        
        Focus on practical fixes that will improve the scores in the next iteration.
        """
        return brain_agent.run(fix_instructions)
    except ImportError:
        console.print("[yellow]Warning: Brain agent not available, skipping fixes[/yellow]")
        return "Brain agent unavailable"

def inspect_site(url: str, project_path: str) -> dict:
    """Inspect site using sensory agent or fallback method."""
    try:
        # Try to use the new sensory agent
        from agents.sensory_agent_web import inspect_site as web_inspect
        return web_inspect(url)
    except ImportError:
        # Fallback to basic inspection
        console.print("[yellow]Warning: Enhanced sensory agent not available, using basic inspection[/yellow]")
        return {
            "status": "basic_inspection",
            "alignment_score": 0.7,
            "interaction": {"submitted": False, "error": "Enhanced agent unavailable"},
            "screens": [{"page": "fallback", "message": "Basic inspection only"}]
        }

# Legacy main for backward compatibility
def main():
    """Legacy main function - redirects to CLI for better UX."""
    console.print(Panel.fit(
        "[yellow]Legacy main() detected![/yellow]\n\n"
        "For better experience, use the CLI:\n"
        "[cyan]python cli.py run --project projects/portfolio --goal 'Your goal here'[/cyan]",
        title="Please use CLI"
    ))
    
    # Run with default parameters for backward compatibility
    goal = "Create a dark-themed portfolio with projects grid and contact form"
    result = run_workflow("projects/portfolio", goal, 3000, 5000, 1)
    rprint(result)

if __name__ == "__main__":
    main()

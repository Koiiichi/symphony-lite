"""Symphony command line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click
import typer
from dotenv import load_dotenv
from rich.console import Console
from typer.core import TyperCommand

# Load environment variables from .env file
load_dotenv()

_original_get_command = typer.main.get_command


def _compat_get_command(typer_instance):  # pragma: no cover - compatibility shim
    if isinstance(typer_instance, click.Command):
        return typer_instance
    return _original_get_command(typer_instance)


typer.main.get_command = _compat_get_command
if hasattr(typer, "testing"):
    typer.testing._get_command = _compat_get_command  # type: ignore[attr-defined]

from core.intent import classify_intent
from core.spinners import ensure_bw_spinners
from core.stack import analyze_project
from core.config_store import get_section, update_section
from core.types import WorkflowConfig
from orchestrator import run_workflow

console = Console()
ensure_bw_spinners()


def _resolve_project_path(path: Optional[Path]) -> Path:
    if path is not None:
        return Path(path).expanduser().resolve()
    return Path.cwd().resolve()


def _execute(
    description: str,
    project: Optional[Path],
    *,
    open_browser: Optional[bool],
    max_passes: Optional[int],
    vision_mode: Optional[str],
    dry_run: bool,
    detailed_log: Optional[bool],
) -> None:
    project_path = _resolve_project_path(project)

    if not project_path.exists():
        create = typer.confirm(f'Path "{project_path}" does not exist. Create it?', default=False)
        if not create:
            raise typer.Exit(1)
        project_path.mkdir(parents=True, exist_ok=True)

    with console.status("Preparing project scan…", spinner="pulsing_star_bw") as status:
        stack = analyze_project(project_path)
        status.update("Interpreting goal…", spinner="orbit_bw")
        intent = classify_intent(description, stack)

    if stack.is_empty and intent.intent == "refine" and not dry_run:
        proceed = typer.confirm("Empty folder detected. Proceed to scaffold a new project?", default=False)
        if not proceed:
            raise typer.Exit(1)

    stored_cli = get_section(project_path, "cli_options")
    effective_open_browser = (
        open_browser
        if open_browser is not None
        else bool(stored_cli.get("open_browser", True))
    )
    effective_max_passes = max_passes or int(stored_cli.get("max_passes", 3))
    effective_detailed_log = (
        detailed_log
        if detailed_log is not None
        else bool(stored_cli.get("detailed_log", False))
    )
    normalized_mode = (vision_mode or stored_cli.get("vision_mode") or "hybrid").lower()
    if normalized_mode not in {"visual", "hybrid", "qa"}:
        raise typer.BadParameter(
            "--vision-mode must be one of: visual, hybrid, qa",
            param_name="vision_mode",
        )

    config = WorkflowConfig(
        project_path=project_path,
        goal=description,
        max_passes=effective_max_passes,
        open_browser=effective_open_browser,
        dry_run=dry_run,
        detailed_log=effective_detailed_log,
        vision_mode=normalized_mode,
    )

    console.print(f"> {description}")

    try:
        summary = run_workflow(config, stack=stack, intent=intent)
    except RuntimeError as exc:  # surface friendly message
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    except Exception as exc:  # pragma: no cover - unexpected failure
        if detailed_log:
            console.print_exception()
        else:
            console.print(f"[red]Unexpected error: {exc}[/red]")
            console.print(
                "[red]Re-run with --detailed-log to view the full traceback.[/red]"
            )
        raise typer.Exit(1)

    status = summary.status

    if status == "success":
        message = summary.final_message or "Success!"
        console.print(f"[green]{message}[/green]")
    else:
        console.print(f"Status: {status}")
        if summary.final_message:
            console.print(summary.final_message)

    if summary.intent:
        console.print(
            f"Mode: {summary.intent.intent} ({summary.intent.topic}), Passes: {len(summary.passes)}"
        )

    if summary.urls:
        preview_lines = ", ".join(f"{kind}: {url}" for kind, url in summary.urls.items())
        console.print(f"Preview URLs: {preview_lines}")

    update_section(
        project_path,
        "cli_options",
        {
            "vision_mode": normalized_mode,
            "open_browser": effective_open_browser,
            "max_passes": effective_max_passes,
            "detailed_log": effective_detailed_log,
        },
    )

    if status == "dry_run":
        raise typer.Exit(0)

    if status != "success":
        raise typer.Exit(1)

    raise typer.Exit(0)


if not hasattr(TyperCommand, "_add_completion"):  # pragma: no cover - compatibility shim
    TyperCommand._add_completion = False  # type: ignore[attr-defined]


main = typer.Typer()


@main.command()
def run(
    description: str = typer.Argument(..., help="Goal or request for Symphony"),
    project: Optional[Path] = typer.Option(None, "--project", help="Target project directory"),
    open_browser: Optional[bool] = typer.Option(
        None,
        "--open/--no-open",
        help="Open browser when the run succeeds",
    ),
    max_passes: Optional[int] = typer.Option(
        None,
        "--max-passes",
        min=1,
        help="Maximum refinement passes",
    ),
    vision_mode: Optional[str] = typer.Option(
        None,
        "--vision-mode",
        help="Vision sweep behaviour: visual | hybrid | qa",
        case_sensitive=False,
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Plan routing without running agents"),
    detailed_log: Optional[bool] = typer.Option(
        None,
        "--detailed-log/--concise-log",
        help="Print extended logs to stderr",
    ),
) -> None:
    """Execute Symphony on an existing or new project."""

    _execute(
        description=description,
        project=project,
        open_browser=open_browser,
        max_passes=max_passes,
        vision_mode=vision_mode,
        dry_run=dry_run,
        detailed_log=detailed_log,
    )


if __name__ == "__main__":
    main()

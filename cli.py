"""Symphony command line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import click
import typer
from rich.console import Console
from typer.core import TyperCommand

_original_get_command = typer.main.get_command


def _compat_get_command(typer_instance):  # pragma: no cover - compatibility shim
    if isinstance(typer_instance, click.Command):
        return typer_instance
    return _original_get_command(typer_instance)


typer.main.get_command = _compat_get_command
typer.testing._get_command = _compat_get_command

from core.intent import classify_intent
from core.stack import analyze_project
from core.types import WorkflowConfig
from orchestrator import run_workflow

console = Console()


def _resolve_project_path(path: Optional[Path]) -> Path:
    if path is not None:
        return Path(path).expanduser().resolve()
    return Path.cwd().resolve()


def _execute(
    description: str,
    project: Optional[Path],
    open_browser: bool,
    max_passes: int,
    dry_run: bool,
    detailed_log: bool,
) -> None:
    project_path = _resolve_project_path(project)

    if not project_path.exists():
        create = typer.confirm(f'Path "{project_path}" does not exist. Create it?', default=False)
        if not create:
            raise typer.Exit(1)
        project_path.mkdir(parents=True, exist_ok=True)

    stack = analyze_project(project_path)
    intent = classify_intent(description, stack)

    if stack.is_empty and intent.intent == "refine" and not dry_run:
        proceed = typer.confirm("Empty folder detected. Proceed to scaffold a new project?", default=False)
        if not proceed:
            raise typer.Exit(1)

    config = WorkflowConfig(
        project_path=project_path,
        goal=description,
        max_passes=max_passes,
        open_browser=open_browser,
        dry_run=dry_run,
        detailed_log=detailed_log,
    )

    console.print(f"> {description}")

    try:
        summary = run_workflow(config)
    except RuntimeError as exc:  # surface friendly message
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)

    status = summary.status
    console.print(f"Status: {status}")
    if summary.intent:
        console.print(
            f"Mode: {summary.intent.intent} ({summary.intent.topic}), Passes: {len(summary.passes)}"
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
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open browser when the run succeeds"),
    max_passes: int = typer.Option(3, "--max-passes", min=1, help="Maximum refinement passes"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Plan routing without running agents"),
    detailed_log: bool = typer.Option(False, "--detailed-log", help="Print extended logs to stderr"),
) -> None:
    """Execute Symphony on an existing or new project."""

    _execute(
        description=description,
        project=project,
        open_browser=open_browser,
        max_passes=max_passes,
        dry_run=dry_run,
        detailed_log=detailed_log,
    )


if __name__ == "__main__":
    main()

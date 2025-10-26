from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class StartCommand:
    """Represents a command needed to start a local service."""

    command: List[str]
    cwd: Path
    kind: str  # "frontend" or "backend" or "aux"
    env: Dict[str, str] = field(default_factory=dict)
    port: Optional[int] = None
    url: Optional[str] = None
    description: Optional[str] = None


@dataclass
class StackInfo:
    """Detected project stack information."""

    root: Path
    has_code: bool
    detected_files: List[Path]
    frameworks: List[str]
    package_managers: List[str]
    frontend: Optional[str]
    backend: Optional[str]
    start_commands: List[StartCommand]
    frontend_url: Optional[str] = None
    backend_url: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.has_code


@dataclass
class IntentResult:
    """Classification output for user goal and project state."""

    intent: str  # "create" or "refine"
    topic: str
    confidence: float
    reasons: List[str]

    def requires_vision_first(self) -> bool:
        return self.intent == "refine" and self.topic == "ui_ux"


@dataclass
class PassOutcome:
    """Result of a single workflow pass."""

    index: int
    vision_passed: bool
    changes_made: bool
    failing_reasons: List[str] = field(default_factory=list)
    summary: Dict[str, str] = field(default_factory=dict)


@dataclass
class WorkflowSummary:
    """High level summary for the run."""

    passes: List[PassOutcome] = field(default_factory=list)
    status: str = "unknown"
    urls: Dict[str, str] = field(default_factory=dict)
    artifacts: Dict[str, str] = field(default_factory=dict)
    intent: Optional[IntentResult] = None
    stack: Optional[StackInfo] = None
    final_message: Optional[str] = None

    def add_pass(self, outcome: PassOutcome) -> None:
        self.passes.append(outcome)


@dataclass
class WorkflowConfig:
    """Runtime configuration derived from CLI flags."""

    project_path: Path
    goal: str
    max_passes: int = 3
    open_browser: bool = True
    dry_run: bool = False
    detailed_log: bool = False
    run_id: Optional[str] = None


@dataclass
class AgentHooks:
    """Hooks for invoking Brain/Vision agents. Allows injection for tests."""

    def run_brain(self, instructions: str, *, pass_index: int) -> Dict[str, Any]:
        raise NotImplementedError

    def run_vision(self, url: str, expectations: Dict[str, Any], *, pass_index: int) -> Dict[str, Any]:
        raise NotImplementedError

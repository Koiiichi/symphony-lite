from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Optional

from rich.console import Console

from agents.brain_agent_factory import BrainConfig, SensoryConfig, create_brain_agent
from agents.brain_instructions import get_generation_instructions
from agents.goal_interpreter import build_expectations
from agents.sensory_agent import inspect_site
from agents.sensory_contract import SensoryReport
from core.intent import classify_intent
from core.router import build_agent_plan, required_agents
from core.runtime import ServerManager, prompt_for_start_command
from core.stack import analyze_project
from core.tui import SymphonyTUI
from core.types import (
    AgentHooks,
    IntentResult,
    PassOutcome,
    StackInfo,
    WorkflowConfig,
    WorkflowSummary,
)
from gates.engine import evaluate as evaluate_gates, get_fix_instructions as build_gate_fix_instructions


console = Console()


def _stack_to_dict(stack: StackInfo) -> Dict[str, object]:
    return {
        "root": str(stack.root),
        "has_content": stack.has_code,
        "frameworks": stack.frameworks,
        "frontend": stack.frontend,
        "backend": stack.backend,
    }


def _summarize_stack(stack: StackInfo) -> str:
    def describe(kind: str, detected: Optional[str]) -> str:
        if detected:
            return f"{kind}: {detected}"
        has_command = any(cmd.kind == kind for cmd in stack.start_commands)
        if has_command:
            return f"{kind}: start command ready"
        return f"{kind}: none"

    parts = [describe("frontend", stack.frontend), describe("backend", stack.backend)]
    return ", ".join(parts)


def _summarize_list(values: Iterable[str], *, limit: int = 4) -> str:
    values = list(values)
    if len(values) <= limit:
        return ", ".join(values)
    clipped = values[:limit]
    return ", ".join(clipped) + ", …"


def _summarize_vision_report(report_data: Dict[str, object]) -> list[str]:
    lines: list[str] = []

    scores = []
    for key, label in (
        ("alignment_score", "alignment"),
        ("spacing_score", "spacing"),
        ("contrast_score", "contrast"),
    ):
        value = report_data.get(key)
        if isinstance(value, (int, float)):
            scores.append(f"{label}: {value:.2f}")
    if scores:
        lines.append("Scores – " + ", ".join(scores))

    sections = report_data.get("visible_sections")
    if isinstance(sections, Iterable) and not isinstance(sections, (str, bytes)):
        section_list = [str(section) for section in sections if section]
        if section_list:
            lines.append("Sections in view – " + _summarize_list(section_list))

    visited = report_data.get("visited_urls")
    if isinstance(visited, Iterable) and not isinstance(visited, (str, bytes)):
        visited_list = [str(url) for url in visited if url]
        if visited_list:
            lines.append("Visited – " + _summarize_list(visited_list, limit=3))

    interaction = report_data.get("interaction")
    if isinstance(interaction, dict):
        interaction_bits = []
        details = interaction.get("details")
        if details:
            interaction_bits.append(str(details))
        status = interaction.get("http_status")
        if status:
            interaction_bits.append(f"HTTP {status}")
        if interaction.get("errors"):
            interaction_bits.append("errors detected")
        if interaction_bits:
            lines.append("Interaction – " + "; ".join(interaction_bits))

    a11y = report_data.get("a11y")
    if isinstance(a11y, dict):
        violations = a11y.get("violations")
        if isinstance(violations, int):
            wcag_level = a11y.get("wcag_level")
            text = f"Accessibility – {violations} violation{'s' if violations != 1 else ''}"
            if wcag_level:
                text += f", target: {wcag_level}"
            lines.append(text)

    return lines


def _format_success_message(goal: str, intent: Optional[IntentResult], summary: WorkflowSummary) -> str:
    """Create a friendly confirmation message for successful runs."""

    passes_run = len(summary.passes)
    changes_made = any(pass_outcome.changes_made for pass_outcome in summary.passes)

    goal_text = goal.strip().rstrip(".")

    if intent and intent.topic == "ui_ux":
        base = f"Done! \"{goal_text}\" is handled and your UI/UX experience is polished."
    else:
        base = f"Done! \"{goal_text}\" is handled."

    detail = ""
    if passes_run:
        detail = f" after {passes_run} pass{'es' if passes_run != 1 else ''}"

    if changes_made:
        tail = "Symphony applied targeted fixes for you to review."
    else:
        tail = "No code changes were needed—the experience already met the expectations."

    return f"{base}{detail}. {tail}"


def _format_stalled_message(failing_reasons: list[str]) -> str:
    if failing_reasons:
        issues = ", ".join(failing_reasons)
        return (
            "Run stopped because the same issues kept resurfacing: "
            f"{issues}. Address them manually and try again."
        )
    return "Run stopped because progress stalled. Review the latest output and try again."


def _format_max_passes_message(failing_reasons: Optional[list[str]]) -> str:
    if failing_reasons:
        issues = ", ".join(failing_reasons)
        return (
            "Reached the maximum number of passes while the following items still need attention: "
            f"{issues}."
        )
    return "Reached the maximum number of passes without clearing every expectation."


@dataclass
class DefaultAgentHooks(AgentHooks):
    project_path: Path
    brain_config: BrainConfig
    sensory_config: SensoryConfig
    run_id: str

    def __post_init__(self) -> None:
        self._brain_agent = None

    def _ensure_brain(self):
        if self._brain_agent is None:
            self._brain_agent = create_brain_agent(self.project_path, self.brain_config, self.run_id)

    def run_brain(self, instructions: str, *, pass_index: int):
        self._ensure_brain()
        return self._brain_agent.run(instructions)

    def run_vision(self, url: str, expectations: Dict[str, object], *, pass_index: int):
        report: SensoryReport = inspect_site(url, self.run_id, {"model_id": self.sensory_config.model_id}, expectations)
        return report


def _require_api_keys(agent_names) -> None:
    mapping = {
        "brain": "SYMPHONY_BRAIN_API_KEY",
        "vision": "SYMPHONY_VISION_API_KEY",
    }
    missing = []
    for agent in agent_names:
        env_key = mapping.get(agent)
        if env_key and not os.environ.get(env_key):
            missing.append(env_key)
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(sorted(set(missing)))}")


def run_workflow(
    config: WorkflowConfig,
    brain_config: Optional[BrainConfig] = None,
    sensory_config: Optional[SensoryConfig] = None,
    hooks: Optional[AgentHooks] = None,
) -> WorkflowSummary:
    project_path = config.project_path.resolve()
    brain_config = brain_config or BrainConfig()
    sensory_config = sensory_config or SensoryConfig()

    run_id = config.run_id or f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    summary = WorkflowSummary()

    stack = analyze_project(project_path)
    intent = classify_intent(config.goal, stack)
    plan = build_agent_plan(intent, include_ui_validation=True)
    agents_needed = required_agents(plan)

    summary.stack = stack
    summary.intent = intent

    tui = SymphonyTUI(detailed=config.detailed_log)
    success = False
    keep_servers_running = False
    preview_url: Optional[str] = None
    server_manager = ServerManager(stack)

    try:
        with tui.live():
            tui.set_header(
                Project=str(project_path),
                Goal=config.goal,
                Mode=f"{intent.intent} ({intent.topic})",
                Passes=config.max_passes,
                Run=run_id,
            )

            tui.update_status("Stack Detection", "RUNNING")
            time.sleep(0.05)
            stack_summary = _summarize_stack(stack)
            tui.update_status("Stack Detection", "COMPLETE", detail=stack_summary)

            tui.add_voice("Analyzing project and classifying intent…")
            tui.add_sub_info(f"Detected intent: {intent.intent}, topic: {intent.topic}")

            if config.dry_run:
                tui.add_voice("Dry-run mode – no files will be written.")
                tui.add_sub_info("Agent plan:")
                for step in plan:
                    tui.add_sub_info(f"{step.agent}: {step.description}")
                tui.add_sub_info(f"Start commands detected: {len(stack.start_commands)}")
                summary.status = "dry_run"
                return summary

            _require_api_keys(agents_needed)

            if not stack.start_commands:
                tui.add_voice("No start command detected. Requesting manual command…")
                manual = prompt_for_start_command(config.goal, project_path)
                stack.start_commands.append(manual)

            tui.update_status("Servers", "STARTING")
            urls = server_manager.start_all()
            tui.update_status("Servers", "READY", detail=", ".join(f"{k}: {v}" for k, v in urls.items()))
            summary.urls = urls
            preview_url = urls.get("frontend") or stack.frontend_url or urls.get("backend")

            hooks = hooks or DefaultAgentHooks(project_path, brain_config, sensory_config, run_id)

            expectations = build_expectations(
                config.goal, page_type_hint=None, stack=_stack_to_dict(stack)
            )
            tui.update_status(
                "Expectations",
                "READY",
                detail=f"{len(expectations.get('capabilities', {}))} capabilities",
            )

            last_report: Optional[SensoryReport] = None
            last_failures: Optional[list[str]] = None
            stagnation_counter = 0

            brain_in_plan = any(step.agent == "brain" for step in plan)

            for index in range(1, config.max_passes + 1):
                tui.update_status("Pass", f"{index}/{config.max_passes}", detail="running")
                changes_made = False
                pass_report: Optional[SensoryReport] = None
                failing_reasons: list[str] = []
                pass_outcome: Optional[PassOutcome] = None

                for step_idx, step in enumerate(plan):
                    remaining_steps = plan[step_idx + 1 :]
                    if step.agent == "vision":
                        vision_url = preview_url or urls.get("frontend") or stack.frontend_url
                        if not vision_url:
                            raise RuntimeError("Vision agent requires a frontend URL")
                        tui.start_activity(f"Vision: {step.description}…", spinner="bouncingBall")
                        report = hooks.run_vision(vision_url, expectations, pass_index=index)
                        tui.stop_activity("Vision: Audit complete", icon="👁")
                        if isinstance(report, SensoryReport):
                            pass_report = report
                            report_data = report.to_dict()
                        else:
                            report_data = report
                        for info_line in _summarize_vision_report(report_data or {}):
                            tui.add_sub_info(info_line)
                        gate_result = evaluate_gates(expectations, report_data)
                        failing_reasons = gate_result["failing_reasons"]
                        if failing_reasons:
                            tui.add_sub_info(
                                "Issues: " + ", ".join(failing_reasons)
                            )
                            if brain_in_plan:
                                issue_count = len(failing_reasons)
                                handoff = (
                                    f"Vision ⇢ Brain: Sharing {issue_count} finding"
                                    f"{'s' if issue_count != 1 else ''} for fixes."
                                )
                                tui.add_voice(handoff, icon="⇢")
                        else:
                            tui.add_sub_info("Issues: none")
                            pass_outcome = PassOutcome(
                                index=index,
                                vision_passed=True,
                                changes_made=changes_made,
                                failing_reasons=[],
                                summary={"status": "passed"},
                            )
                            summary.add_pass(pass_outcome)
                            summary.status = "success"
                            final_message = _format_success_message(config.goal, intent, summary)
                            summary.final_message = final_message
                            tui.set_footer(final_message)
                            success = True
                            keep_servers_running = config.open_browser and bool(preview_url)
                            break
                    elif step.agent == "brain":
                        if pass_report is None and last_report is None:
                            instructions = get_generation_instructions(
                                str(project_path),
                                config.goal,
                                _stack_to_dict(stack),
                            )
                        else:
                            report_for_fix = pass_report or last_report
                            if isinstance(report_for_fix, SensoryReport):
                                report_dict = report_for_fix.to_dict()
                            else:
                                report_dict = report_for_fix or {}
                            instructions = build_gate_fix_instructions(
                                expectations,
                                report_dict,
                                failing_reasons,
                            )
                            instructions = (
                                f"You are improving pass {index}.\n"
                                f"Goal: {config.goal}\n\n"
                                f"{instructions}\n"
                            )
                        tui.start_activity(f"Brain: {step.description}…", spinner="dots")
                        hooks.run_brain(instructions, pass_index=index)
                        tui.stop_activity("Brain: Applied targeted fixes", icon="🧠")
                        changes_made = True
                        tui.add_sub_info("Applied targeted fixes")
                        has_follow_up_vision = any(
                            future_step.agent == "vision" for future_step in remaining_steps
                        )
                        if has_follow_up_vision:
                            tui.add_voice(
                                "Brain ⇢ Vision: Updates ready for validation.",
                                icon="⇠",
                            )

                if pass_outcome is None:
                    pass_outcome = PassOutcome(
                        index=index,
                        vision_passed=not failing_reasons,
                        changes_made=changes_made,
                        failing_reasons=failing_reasons,
                        summary={"issues": failing_reasons},
                    )
                    summary.add_pass(pass_outcome)

                if success:
                    break

                if failing_reasons:
                    if last_failures == failing_reasons:
                        stagnation_counter += 1
                    else:
                        stagnation_counter = 0
                    if stagnation_counter >= 1:
                        summary.status = "stalled"
                        final_message = _format_stalled_message(failing_reasons)
                        summary.final_message = final_message
                        tui.set_footer(final_message)
                        break
                last_failures = failing_reasons
                last_report = pass_report

            if summary.status == "unknown":
                summary.status = "max_passes"
                final_message = _format_max_passes_message(last_failures or [])
                summary.final_message = final_message
                tui.set_footer(final_message)
    finally:
        if not keep_servers_running:
            server_manager.stop_all()

    if keep_servers_running and preview_url:
        try:
            import webbrowser

            webbrowser.open(preview_url)
        except Exception:
            pass

        console.print(
            f"[green]Preview ready at {preview_url}. Symphony will keep the local servers running while you take a look.[/green]"
        )
        prompt_text = "Press Enter when you're done previewing to shut everything down…"
        if sys.stdin.isatty():
            try:
                input(prompt_text)
            except EOFError:
                time.sleep(5)
        else:
            time.sleep(5)

        server_manager.stop_all()

    return summary

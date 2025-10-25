from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

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
from core.types import AgentHooks, PassOutcome, StackInfo, WorkflowConfig, WorkflowSummary
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
        stack_summary = ", ".join(filter(None, [stack.frontend or "frontend?", stack.backend or "backend?"]))
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

        server_manager = ServerManager(stack)
        tui.update_status("Servers", "STARTING")
        urls = server_manager.start_all()
        tui.update_status("Servers", "READY", detail=", ".join(f"{k}: {v}" for k, v in urls.items()))
        summary.urls = urls

        hooks = hooks or DefaultAgentHooks(project_path, brain_config, sensory_config, run_id)

        expectations = build_expectations(config.goal, page_type_hint=None, stack=_stack_to_dict(stack))
        tui.update_status("Expectations", "READY", detail=f"{len(expectations.get('capabilities', {}))} capabilities")

        last_report: Optional[SensoryReport] = None
        last_failures: Optional[list[str]] = None
        stagnation_counter = 0

        try:
            for index in range(1, config.max_passes + 1):
                tui.update_status("Pass", f"{index}/{config.max_passes}", detail="running")
                changes_made = False
                pass_report: Optional[SensoryReport] = None
                failing_reasons: list[str] = []

                for step in plan:
                    if step.agent == "vision":
                        frontend_url = urls.get("frontend") or stack.frontend_url
                        if not frontend_url:
                            raise RuntimeError("Vision agent requires a frontend URL")
                        tui.add_voice(step.description)
                        report = hooks.run_vision(frontend_url, expectations, pass_index=index)
                        if isinstance(report, SensoryReport):
                            pass_report = report
                            report_data = report.to_dict()
                        else:
                            report_data = report
                        gate_result = evaluate_gates(expectations, report_data)
                        failing_reasons = gate_result["failing_reasons"]
                        tui.add_sub_info(
                            "Issues: " + (", ".join(failing_reasons) if failing_reasons else "none")
                        )
                        if not failing_reasons:
                            summary.add_pass(
                                PassOutcome(
                                    index=index,
                                    vision_passed=True,
                                    changes_made=changes_made,
                                    failing_reasons=[],
                                    summary={"status": "passed"},
                                )
                            )
                            summary.status = "success"
                            tui.set_footer("SUCCESS")
                            success = True
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
                        tui.add_voice(step.description)
                        hooks.run_brain(instructions, pass_index=index)
                        changes_made = True
                        tui.add_sub_info("Patched project files")

                summary.add_pass(
                    PassOutcome(
                        index=index,
                        vision_passed=not failing_reasons,
                        changes_made=changes_made,
                        failing_reasons=failing_reasons,
                        summary={"issues": failing_reasons},
                    )
                )

                if success:
                    break

                if failing_reasons:
                    if last_failures == failing_reasons:
                        stagnation_counter += 1
                    else:
                        stagnation_counter = 0
                    if stagnation_counter >= 1:
                        summary.status = "stalled"
                        tui.set_footer("Stopped due to repeated failures")
                        break
                last_failures = failing_reasons
                last_report = pass_report

            if summary.status == "unknown":
                summary.status = "max_passes"
                tui.set_footer("Reached max passes without full success")
        finally:
            server_manager.stop_all()

    if success and config.open_browser:
        frontend_url = summary.urls.get("frontend") or stack.frontend_url
        if frontend_url:
            try:
                import webbrowser

                webbrowser.open(frontend_url)
            except Exception:
                pass

    return summary

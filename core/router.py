from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .types import IntentResult


@dataclass
class AgentStep:
    """Represents a unit of work for a specific agent."""

    agent: str  # "vision" or "brain"
    description: str


def build_agent_plan(intent: IntentResult, include_ui_validation: bool) -> List[AgentStep]:
    """Build the agent execution plan given intent and flags."""

    steps: List[AgentStep] = []

    if intent.intent == "create":
        steps.append(AgentStep(agent="brain", description="Scaffold or extend project"))
        if include_ui_validation or intent.topic == "ui_ux":
            steps.append(AgentStep(agent="vision", description="Validate initial experience"))
        return steps

    if intent.intent == "refine":
        if intent.topic == "ui_ux":
            steps.extend(
                [
                    AgentStep(agent="vision", description="Audit current experience"),
                    AgentStep(agent="brain", description="Apply fixes from audit"),
                    AgentStep(agent="vision", description="Validate adjustments"),
                ]
            )
        else:
            steps.append(AgentStep(agent="brain", description="Implement requested changes"))
            if include_ui_validation:
                steps.append(AgentStep(agent="vision", description="Spot check experience"))
        return steps

    steps.append(AgentStep(agent="brain", description="Process goal"))
    return steps


def required_agents(plan: Iterable[AgentStep]) -> List[str]:
    """Return unique agents required for the plan preserving order."""

    seen: List[str] = []
    for step in plan:
        if step.agent not in seen:
            seen.append(step.agent)
    return seen

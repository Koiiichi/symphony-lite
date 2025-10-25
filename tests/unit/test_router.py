from core.router import build_agent_plan
from core.types import IntentResult


def make_intent(intent: str, topic: str) -> IntentResult:
    return IntentResult(intent=intent, topic=topic, confidence=0.9, reasons=["test"])


def test_ui_refine_plan_is_vision_first():
    intent = make_intent("refine", "ui_ux")
    plan = build_agent_plan(intent, include_ui_validation=True)
    agents = [step.agent for step in plan]
    assert agents[:3] == ["vision", "brain", "vision"]


def test_feature_refine_plan_brain_first():
    intent = make_intent("refine", "feature")
    plan = build_agent_plan(intent, include_ui_validation=True)
    assert plan[0].agent == "brain"
    assert plan[-1].agent == "vision"


def test_create_project_plan():
    intent = make_intent("create", "feature")
    plan = build_agent_plan(intent, include_ui_validation=False)
    assert [step.agent for step in plan] == ["brain"]

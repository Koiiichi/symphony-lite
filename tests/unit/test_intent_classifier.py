from pathlib import Path

from core.intent import classify_intent
from core.types import StackInfo, StartCommand


def make_stack(has_code: bool) -> StackInfo:
    return StackInfo(
        root=Path("/tmp/project"),
        has_code=has_code,
        detected_files=[],
        frameworks=["vite"] if has_code else [],
        package_managers=["npm"] if has_code else [],
        frontend="vite" if has_code else None,
        backend=None,
        start_commands=[
            StartCommand(command=["npm", "run", "dev"], cwd=Path("/tmp/project"), kind="frontend")
        ]
        if has_code
        else [],
        frontend_url="http://localhost:5173" if has_code else None,
        backend_url=None,
    )


def test_refine_ui_ux_detection():
    stack = make_stack(True)
    result = classify_intent("Improve the navbar spacing for better mobile UX", stack)
    assert result.intent == "refine"
    assert result.topic == "ui_ux"
    assert result.requires_vision_first()


def test_create_project_detection():
    stack = make_stack(False)
    result = classify_intent("Create a new analytics dashboard", stack)
    assert result.intent == "create"
    assert result.topic in {"feature", "ui_ux", "data_pipeline"}


def test_bugfix_detection():
    stack = make_stack(True)
    result = classify_intent("Fix the login bug in production", stack)
    assert result.intent == "refine"
    assert result.topic == "bug"

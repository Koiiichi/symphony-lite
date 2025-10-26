from __future__ import annotations

from pathlib import Path

import pytest
from click.exceptions import Exit as ClickExit

from cli import _execute
from core.types import IntentResult, StackInfo


def _make_stack(root: Path) -> StackInfo:
    return StackInfo(
        root=root,
        has_code=True,
        detected_files=[],
        frameworks=[],
        package_managers=[],
        frontend=None,
        backend=None,
        start_commands=[],
    )


def _make_intent() -> IntentResult:
    return IntentResult(intent="refine", topic="feature", confidence=1.0, reasons=[])


def test_execute_handles_unexpected_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr("cli.analyze_project", lambda _: _make_stack(tmp_path))
    monkeypatch.setattr("cli.classify_intent", lambda _desc, _stack: _make_intent())

    def fake_run_workflow(*_args, **_kwargs):
        raise ValueError("boom")

    monkeypatch.setattr("cli.run_workflow", fake_run_workflow)

    with pytest.raises(ClickExit) as excinfo:
        _execute(
            description="goal",
            project=tmp_path,
            open_browser=False,
            max_passes=1,
            dry_run=False,
            detailed_log=False,
        )

    assert excinfo.value.exit_code == 1
    captured = capsys.readouterr()
    assert "Unexpected error" in captured.out
    assert "--detailed-log" in captured.out

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from core.runtime import ServerManager
from core.types import StackInfo, StartCommand


def _make_stack(tmp_path: Path, command: StartCommand) -> StackInfo:
    return StackInfo(
        root=tmp_path,
        has_code=True,
        detected_files=[],
        frameworks=[],
        package_managers=[],
        frontend=None,
        backend=None,
        start_commands=[command],
    )


def test_start_command_failure_surfaces_immediately(tmp_path: Path) -> None:
    script = "import sys; sys.stderr.write('boom\\n'); sys.exit(1)"
    command = StartCommand(
        command=[sys.executable, "-c", script],
        cwd=tmp_path,
        kind="frontend",
        port=54321,
        description="Test server",
    )
    stack = _make_stack(tmp_path, command)

    manager = ServerManager(stack)

    with pytest.raises(RuntimeError) as excinfo:
        manager.start_all(timeout=2)

    message = str(excinfo.value)
    assert "Test server" in message
    assert "boom" in message

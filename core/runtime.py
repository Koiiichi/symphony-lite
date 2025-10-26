from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

try:  # pragma: no cover - optional dependency
    import requests
except ModuleNotFoundError:  # pragma: no cover - fallback used in tests
    class _RequestsStub:
        class RequestException(Exception):
            pass

        @staticmethod
        def get(*_, **__):
            raise ModuleNotFoundError(
                "requests is required to check service readiness. Install requests to enable runtime server checks."
            )

    requests = _RequestsStub()  # type: ignore[assignment]

from .stack import ensure_config_override
from .types import StackInfo, StartCommand


@dataclass
class RunningProcess:
    command: StartCommand
    process: subprocess.Popen


class ServerManager:
    """Start and stop project services based on detected commands."""

    def __init__(self, stack: StackInfo) -> None:
        self.stack = stack
        self.running: List[RunningProcess] = []

    def plan(self) -> List[StartCommand]:
        return self.stack.start_commands

    def start_all(self, *, timeout: int = 60) -> Dict[str, str]:
        urls: Dict[str, str] = {}
        for command in self.stack.start_commands:
            env = os.environ.copy()
            env.update(command.env)
            proc = subprocess.Popen(
                command.command,
                cwd=str(command.cwd),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.running.append(RunningProcess(command=command, process=proc))
            if command.url:
                urls[command.kind] = command.url
            elif command.port:
                urls[command.kind] = f"http://localhost:{command.port}"
            if command.port:
                self._wait_for_port(command.port, timeout=timeout)
        return urls

    def stop_all(self) -> None:
        for proc in self.running:
            if proc.process.poll() is None:
                proc.process.terminate()
                try:
                    proc.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.process.kill()
        self.running.clear()

    def _wait_for_port(self, port: int, *, timeout: int = 60) -> None:
        url = f"http://localhost:{port}"
        start = time.time()
        while time.time() - start < timeout:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code < 500:
                    return
            except requests.RequestException:
                pass
            time.sleep(1)
        raise TimeoutError(f"Service on port {port} did not become ready")


def prompt_for_start_command(goal: str, project_root: Path) -> StartCommand:
    """Fallback manual command creation when detection fails."""

    from typer import prompt

    description = prompt("Describe the command (e.g., npm run dev)")
    parts = description.strip().split()
    if not parts:
        raise ValueError("No command entered")
    cwd_input = prompt("Working directory (relative to project root)", default=".")
    kind = prompt("Command type", default="frontend")
    port_input = prompt("Expected port (blank to skip)", default="")
    port = int(port_input) if port_input else None
    url = prompt("URL (blank to auto infer)", default="") or None

    cmd = StartCommand(
        command=parts,
        cwd=project_root / cwd_input,
        kind=kind,
        port=port,
        url=url,
        description=description,
    )
    ensure_config_override(project_root, cmd)
    return cmd

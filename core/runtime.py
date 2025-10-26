from __future__ import annotations

import os
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

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
                text=True,
            )
            self.running.append(RunningProcess(command=command, process=proc))
            if command.url:
                urls[command.kind] = command.url
            elif command.port:
                urls[command.kind] = f"http://localhost:{command.port}"
            if command.port:
                try:
                    self._wait_for_port(
                        command.port,
                        timeout=timeout,
                        process=proc,
                        description=command.description or "Service",
                    )
                except Exception:
                    self.stop_all()
                    raise
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

    def _wait_for_port(
        self,
        port: int,
        *,
        timeout: int = 60,
        process: subprocess.Popen | None = None,
        description: str | None = None,
    ) -> None:
        start = time.time()
        while time.time() - start < timeout:
            if process and process.poll() is not None:
                stdout, stderr = process.communicate()
                message = description or f"Service on port {port}"
                detail = (stderr or stdout or "").strip()
                if detail:
                    message += f" failed: {detail.splitlines()[0]}"
                else:
                    message += " exited unexpectedly."
                raise RuntimeError(message)
            try:
                with socket.create_connection(("localhost", port), timeout=2):
                    return
            except OSError:
                pass
            time.sleep(1)
        message = description or f"Service on port {port}"
        if process:
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                detail = (stderr or stdout or "").strip()
                if detail:
                    message += f" exited early: {detail.splitlines()[0]}"
                else:
                    message += " exited before becoming ready."
                raise RuntimeError(message)
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
            detail = (stderr or stdout or "").strip()
            if detail:
                message += f" timed out. Last output: {detail.splitlines()[0]}"
            else:
                message += " timed out before responding."
            raise TimeoutError(message)

        raise TimeoutError(f"{message} did not become ready in {timeout} seconds")


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

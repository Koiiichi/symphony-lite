from __future__ import annotations

import socketserver
import sys
import threading
from pathlib import Path

import pytest

from core.runtime import ServerManager, ServerProbe
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


class _NoopHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:  # pragma: no cover - trivial
        try:
            self.request.recv(16)
        except OSError:
            pass


def test_wait_for_port_detects_open_socket(tmp_path: Path) -> None:
    server = socketserver.TCPServer(("127.0.0.1", 0), _NoopHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    command = StartCommand(
        command=[sys.executable, "-c", "import time; time.sleep(5)"],
        cwd=tmp_path,
        kind="frontend",
        port=port,
        description="Socket server",
    )
    stack = _make_stack(tmp_path, command)
    manager = ServerManager(stack)

    try:
        manager._wait_for_port(port, timeout=5)
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_resolve_preview_surface_prefers_non_blank(monkeypatch, tmp_path: Path) -> None:
    frontend = StartCommand(
        command=[sys.executable, "-m", "http.server"],
        cwd=tmp_path,
        kind="frontend",
        url="http://localhost:3000",
    )
    backend = StartCommand(
        command=[sys.executable, "-m", "http.server"],
        cwd=tmp_path,
        kind="backend",
        url="http://localhost:5000",
    )
    stack = StackInfo(
        root=tmp_path,
        has_code=True,
        detected_files=[],
        frameworks=[],
        package_managers=[],
        frontend="vite",
        backend="flask",
        start_commands=[frontend, backend],
        frontend_url="http://localhost:3000",
        backend_url="http://localhost:5000",
    )
    manager = ServerManager(stack)

    def fake_probe(kind: str, url: str) -> ServerProbe:
        if url.endswith("3000"):
            return ServerProbe(
                url=url,
                kind=kind,
                status_code=200,
                content_type="text/html",
                is_blank=True,
                node_count=0,
                body="\n\n",
            )
        return ServerProbe(
            url=url,
            kind=kind,
            status_code=200,
            content_type="text/html",
            is_blank=False,
            node_count=5,
            body="<html><form id='contact'></form></html>",
        )

    monkeypatch.setattr(manager, "_probe_candidate", fake_probe)

    selection = manager.resolve_preview_surface(
        run_id="run-test",
        preferred_kind="frontend",
        hints={"selectors": ["contact"], "keywords": []},
    )

    assert selection.url == "http://localhost:5000"
    assert selection.probe is not None
    assert not selection.probe.is_blank


def test_resolve_preview_surface_records_blank_artifacts(monkeypatch, tmp_path: Path) -> None:
    command = StartCommand(
        command=[sys.executable, "-m", "http.server"],
        cwd=tmp_path,
        kind="frontend",
        url="http://localhost:1234",
    )
    stack = StackInfo(
        root=tmp_path,
        has_code=True,
        detected_files=[],
        frameworks=[],
        package_managers=[],
        frontend="vite",
        backend=None,
        start_commands=[command],
        frontend_url="http://localhost:1234",
    )
    manager = ServerManager(stack)

    monkeypatch.setattr(
        manager,
        "_probe_candidate",
        lambda kind, url: ServerProbe(
            url=url,
            kind=kind,
            status_code=200,
            content_type="text/html",
            is_blank=True,
            node_count=0,
            body="",
        ),
    )

    selection = manager.resolve_preview_surface(run_id="run-blank", preferred_kind="frontend")

    assert selection.probe is not None and selection.probe.is_blank
    assert selection.artifacts

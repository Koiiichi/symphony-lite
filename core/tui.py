from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, List, Optional

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


@dataclass
class StatusLine:
    label: str
    status: str
    detail: Optional[str] = None


class SymphonyTUI:
    """Dynamic terminal UI for Symphony runs."""

    def __init__(self, console: Optional[Console] = None, detailed: bool = False) -> None:
        self.console = console or Console()
        self.detailed = detailed
        self.header: Dict[str, str] = {}
        self.status_lines: Dict[str, StatusLine] = {}
        self.voice_lines: List[str] = []
        self.todo_lines: List[str] = []
        self.footer: Optional[str] = None
        self._live: Optional[Live] = None

    @contextmanager
    def live(self):
        with Live(self._render(), console=self.console, refresh_per_second=8, transient=False) as live:
            self._live = live
            try:
                yield self
            finally:
                self._live = None

    def set_header(self, **fields: str) -> None:
        self.header.update({k: str(v) for k, v in fields.items() if v is not None})
        self._refresh()

    def update_status(self, label: str, status: str, detail: Optional[str] = None) -> None:
        self.status_lines[label] = StatusLine(label=label, status=status, detail=detail)
        self._refresh()

    def add_voice(self, text: str) -> None:
        line = f"⏺ {text.strip()}"
        self.voice_lines.append(line)
        self._refresh()

    def add_sub_info(self, text: str) -> None:
        self.voice_lines.append(f"  ⎿ {text.strip()}")
        self._refresh()

    def set_footer(self, text: str) -> None:
        self.footer = text
        self._refresh()

    def set_todos(self, todos: Dict[str, bool]) -> None:
        self.todo_lines = []
        if todos:
            self.todo_lines.append("Update Todos")
            for label, done in todos.items():
                checkbox = "☒" if done else "☐"
                self.todo_lines.append(f"{checkbox} {label}")
        self._refresh()

    def _refresh(self) -> None:
        if self._live:
            self._live.update(self._render())

    def _render(self):
        header_table = Table.grid(expand=True)
        for key, value in self.header.items():
            header_table.add_row(f"[bold]{key}[/]: {value}")

        status_table = Table.grid(padding=0)
        for status in self.status_lines.values():
            detail = f" – {status.detail}" if status.detail else ""
            status_table.add_row(f"{status.label}: {status.status}{detail}")

        voice = Table.grid(padding=0)
        for line in self.voice_lines[-15:]:
            voice.add_row(line)

        items: List = [Panel(header_table, title="Symphony"), Panel(status_table, title="Status")]

        if self.todo_lines:
            todo_table = Table.grid(padding=0)
            for line in self.todo_lines:
                todo_table.add_row(line)
            items.append(Panel(todo_table, title="Todos"))

        items.append(Panel(voice, title="Activity"))

        if self.footer:
            items.append(Panel(Text(self.footer), title="Summary"))

        return Group(*items)

    def print_detailed(self, text: str) -> None:
        if self.detailed:
            self.console.print(Text(text, style="dim"))

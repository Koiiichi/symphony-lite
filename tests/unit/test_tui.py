import io
import time

from rich.console import Console

from core.tui import SymphonyTUI


def test_tui_heartbeat_updates() -> None:
    console = Console(file=io.StringIO(), force_terminal=False)
    tui = SymphonyTUI(console=console)
    tui._heartbeat_interval = 0.1  # type: ignore[attr-defined]

    with tui.live():
        time.sleep(0.25)

    assert tui._heartbeat_text != "…"  # type: ignore[attr-defined]

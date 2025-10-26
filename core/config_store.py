"""Persistent configuration storage for Symphony runs.

This module centralizes reading and writing the per-project
``.symphony.json`` file.  The CLI as well as the stack detector share
these helpers to ensure user preferences (start commands, frequently used
flags, etc.) survive across runs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


_CONFIG_FILE = ".symphony.json"


def _config_path(root: Path) -> Path:
    return root / _CONFIG_FILE


def load_config(root: Path) -> Dict[str, Any]:
    """Load the JSON configuration for ``root``.

    Invalid JSON is treated as an empty configuration so a malformed file
    never breaks the CLI.
    """

    path = _config_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def save_config(root: Path, data: Dict[str, Any]) -> None:
    path = _config_path(root)
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


def update_section(root: Path, section: str, values: Dict[str, Any]) -> None:
    """Merge ``values`` into ``section`` of the project configuration."""

    config = load_config(root)
    section_data = config.setdefault(section, {})
    section_data.update(values)
    save_config(root, config)


def get_section(root: Path, section: str) -> Dict[str, Any]:
    config = load_config(root)
    section_data = config.get(section)
    if isinstance(section_data, dict):
        return section_data
    return {}


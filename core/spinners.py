"""Utility helpers for registering monochrome-friendly spinner styles."""

from rich.spinner import SPINNERS


def ensure_bw_spinners() -> None:
    """Register the custom black-and-white spinners if needed."""

    if "pulsing_star_bw" not in SPINNERS:
        SPINNERS["pulsing_star_bw"] = {
            "frames": ["✶   ", " ✶  ", "  ✶ ", "   ✶", "  ✶ ", " ✶  "],
            "interval": 120,
        }

    if "orbit_bw" not in SPINNERS:
        SPINNERS["orbit_bw"] = {
            "frames": ["⬤◯◯", "◯⬤◯", "◯◯⬤", "◯⬤◯"],
            "interval": 160,
        }

    if "bounce_bw" not in SPINNERS:
        SPINNERS["bounce_bw"] = {
            "frames": ["∙··", "·∙·", "··∙", "·∙·"],
            "interval": 180,
        }


# Symphony-Lite

## Quick Start

### Install
1. Clone the repository and install dependencies:
   ```bash
   git clone <repository-url>
   cd symphony-lite
   pip install -r requirements.txt
   ```
2. Provide API keys via environment variables or a `.env` file in the project directory:
   ```bash
   export SYMPHONY_BRAIN_API_KEY=... 
   export SYMPHONY_VISION_API_KEY=...
   ```

### Run
* From inside an existing project:
  ```bash
  symphony "Improve the mobile navbar spacing"
  ```
* From any directory with an explicit project path:
  ```bash
  symphony --project ./demo "Create a marketing landing page"
  ```

Common flags:
* `--open/--no-open` – open the detected URL when the run succeeds (default on).
* `--max-passes <int>` – limit refinement cycles (default 3).
* `--dry-run` – preview routing, stack detection, and safety prompts without running agents.
* `--detailed-log` – show expanded trace summaries in the terminal UI.

### What You’ll See
The terminal UI streams a compact feed while agents work. Expect voice-style updates and sub-lines:
```
> Ensure UI/UX is up to the mark
⏺ Vision: Scanning homepage at breakpoints…
  ⎿ Issues: Button tap targets < 44px on mobile
⏺ Brain: Applying scoped CSS fixes for padding and contrast…
  ⎿ Patched styles/button.css
```
All prompts and provider transcripts remain private; only human-readable summaries are shown.

### Testing
Run the full automated suite (unit, integration, CLI checks):
```bash
pytest
```

### Privacy & Safety
Symphony confirms before creating directories or scaffolding new projects, enforces max-pass limits, and never prints raw prompts or API responses in the UI.

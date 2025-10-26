# Symphony-Lite

## Quick Start

### Install
1. Clone the repository and navigate to it:
   ```bash
   git clone <repository-url>
   cd symphony-lite
   ```

2. **(Recommended)** Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows (Git Bash):
   source venv/Scripts/activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
   
   **Note:** If you encounter dependency conflicts, try:
   ```bash
   python -m pip cache purge
   python -m pip install --no-cache-dir -r requirements.txt
   ```

4. Provide API keys via environment variables or a `.env` file in the project root directory:
   ```bash
   export SYMPHONY_BRAIN_API_KEY=... 
   export SYMPHONY_VISION_API_KEY=...
   ```
   Or create a `.env` file:
   ```
   SYMPHONY_BRAIN_API_KEY=your_key_here
   SYMPHONY_VISION_API_KEY=your_key_here
   ```

### Run
* From inside an existing project (the script ensures the bundled virtualenv is ready):
  ```bash
  python symphony.py "Improve the mobile navbar spacing"
  ```
* From any directory with an explicit project path:
  ```bash
  python symphony.py --project ./demo "Create a marketing landing page"
  ```
* Optional – add a shell alias once things work:
  ```bash
  alias symphony="python /path/to/symphony.py"                # macOS/Linux shells
  doskey symphony=py C:\path\to\symphony.py $*              # Windows Command Prompt
  function symphony { py C:\path\to\symphony.py $args }     # Windows PowerShell
  ```

Common flags:
* `--open/--no-open` – open the detected URL when the run succeeds (default on).
* `--max-passes <int>` – limit refinement cycles (default 3).
* `--dry-run` – preview routing, stack detection, and safety prompts without running agents.
* `--detailed-log` – show expanded trace summaries in the terminal UI.

### What You’ll See
The terminal UI now shows animated progress while the agents work and narrates the hand-off between them:
```
> Ensure UI/UX is up to the mark
⠋ Vision: Scanning homepage at breakpoints…
👁 Vision: Audit complete
  ⎿ Scores – alignment: 0.91, spacing: 0.86, contrast: 0.95
  ⎿ Issues: Button tap targets < 44px on mobile
⇢ Vision ⇢ Brain: Sharing 1 finding for fixes.
🧠 Brain: Applied targeted fixes
⇠ Brain ⇢ Vision: Updates ready for validation.
```
You’ll also see section, interaction, and accessibility highlights beneath each audit so it’s clear what the vision agent inspected.

### Testing
Run the full automated suite (unit, integration, CLI checks):
```bash
pytest
```

### Privacy & Safety
Symphony confirms before creating directories or scaffolding new projects, enforces max-pass limits, and never prints raw prompts or API responses in the UI.

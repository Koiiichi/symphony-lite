# Quick Start

## Prerequisites
- Python 3.10 or higher
- API keys: `SYMPHONY_BRAIN_API_KEY` and `SYMPHONY_VISION_API_KEY`

## 1. Install

```bash
git clone <repository-url>
cd symphony-lite
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

## 2. Configure

```bash
export SYMPHONY_BRAIN_API_KEY=your_key_here
export SYMPHONY_VISION_API_KEY=your_key_here
```

Or create a `.env` file in the project root.

## 3. Run

```bash
# From inside a project:
python symphony.py "Improve the mobile navbar spacing"

# With explicit project path:
python symphony.py --project ./my-app "Create a landing page"

# Dry run (preview without changes):
python symphony.py --project ./my-app --dry-run "Add a contact form"
```

## Common Flags

| Flag | Description |
|------|-------------|
| `--open/--no-open` | Open browser on success (default: on) |
| `--max-passes <int>` | Limit refinement cycles (default: 3) |
| `--vision-mode <mode>` | `visual`, `hybrid`, or `qa` (default: hybrid) |
| `--dry-run` | Preview routing without running agents |

## Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run smoke tests only
python tests/unit/smoke_test.py
```

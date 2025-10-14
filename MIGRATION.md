# Migration Guide - Symphony-Lite v2.0

## Overview

Symphony-Lite v2.0 introduces a major refactor to eliminate global state, support project-agnostic workflows, and provide a cleaner API. This guide helps you migrate from v1.x to v2.0.

## What Changed

### Architecture

**Before (v1.x)**:
- Global Brain agent instance
- Global project path variable
- Hardcoded to portfolio projects
- Dict-based sensory reports
- No concurrent run support

**After (v2.0)**:
- Factory-based Brain agent creation
- Per-run project scoping
- Works with any web app type
- Type-safe SensoryReport contract
- Concurrent runs supported

### File Structure

**New Files**:
- `agents/brain_agent_factory.py` - Brain agent factory
- `agents/sensory_contract.py` - Standardized report format
- `agents/brain_instructions.py` - Centralized prompts
- `agents/sensory_agent_web_v2.py` - Contract-compliant sensory agent
- `orchestrator_v2.py` - Refactored orchestrator
- `cli_v2.py` - Enhanced CLI with new flags
- `runner_v2.py` - Runner with readiness checks

**Deprecated (still work, but not recommended)**:
- `agents/brain_agent.py` - Use factory instead
- `agents/sensory_agent_web.py` - Use v2
- `orchestrator.py` - Use v2
- `cli.py` - Use v2

## Breaking Changes

### 1. Brain Agent Instantiation

**Before**:
```python
from agents.brain_agent import brain_agent, set_project_path

set_project_path("/path/to/project")
brain_agent.run(instructions)
```

**After**:
```python
from agents.brain_agent_factory import create_brain_agent, BrainConfig

config = BrainConfig(
    model_id="gpt-4o",
    max_steps=15,
    temperature=0.7
)

brain = create_brain_agent("/path/to/project", config, "run_123")
brain.run(instructions)
```

### 2. Sensory Agent Reports

**Before**:
```python
from agents.sensory_agent_web import inspect_site

report = inspect_site("http://localhost:3000")
# report is a dict
alignment = report["alignment_score"]
form_working = report["interaction"]["success"]
```

**After**:
```python
from agents.sensory_agent_web_v2 import inspect_site
from agents.sensory_contract import SensoryReport

report: SensoryReport = inspect_site("http://localhost:3000", "run_123")
# report is a typed dataclass
alignment = report.alignment_score
form_working = report.interaction.contact_submitted

# Check quality gates
if report.passes_all_gates():
    print("All gates passed!")
```

### 3. Orchestrator Workflow

**Before**:
```python
from orchestrator import run_workflow

result = run_workflow(
    "projects/portfolio",
    "Build a portfolio",
    3000,
    5000,
    steps=1
)
```

**After**:
```python
from orchestrator_v2 import run_workflow
from agents.brain_agent_factory import BrainConfig

config = BrainConfig(model_id="gpt-4o")

result = run_workflow(
    "projects/portfolio",
    "Build a portfolio",
    3000,
    5000,
    steps=3,
    brain_config=config,
    run_id="my_run",
    open_browser=True
)
```

### 4. CLI Usage

**Before**:
```bash
python symphony.py run \
  --project projects/portfolio \
  --goal "Portfolio" \
  --steps 1
```

**After** (backward compatible, but enhanced):
```bash
python symphony.py run \
  --project projects/portfolio \
  --goal "Portfolio" \
  --steps 3 \
  --brain-model gpt-4o \
  --open \
  --temperature 0.7 \
  --max-agent-steps 15
```

## New Features

### 1. Configurable Brain Models

```bash
# Use GPT-4o (default)
python symphony.py run --project . --goal "..." --brain-model gpt-4o

# Use Claude (if configured)
python symphony.py run --project . --goal "..." --brain-model claude-3-opus
```

### 2. Browser Auto-Open

```bash
# Open browser on success
python symphony.py run --project . --goal "..." --open

# Don't open browser (default)
python symphony.py run --project . --goal "..." --no-open
```

### 3. Quality Gates

Reports now include automatic quality gate checking:

```python
report = inspect_site(url, run_id)

# Check all gates at once
if report.passes_all_gates():
    print("Production ready!")

# Get specific failing gates
failing = report.get_failing_gates()
# ["alignment_score (0.85 < 0.90)", "contact_form_not_working"]

# Get targeted fix instructions
instructions = report.get_fix_instructions()
```

### 4. Run Isolation

Each run gets a unique ID for artifact organization:

```
artifacts/
  run_20251013_143022/
    step_1_initial.png
    step_2_scroll.png
    step_3_submit.png
  run_20251013_150145/
    step_1_initial.png
    ...
```

### 5. Concurrent Runs

Multiple runs can now execute in parallel without interference:

```bash
# Terminal 1
python symphony.py run --project proj1 --goal "..." &

# Terminal 2
python symphony.py run --project proj2 --goal "..." &
```

### 6. Stack Detection

Automatic detection of existing tech stack:

```python
from agents.brain_agent_factory import detect_existing_stack

stack = detect_existing_stack(Path("/path/to/project"))
# {
#   "frontend": "node" | "static",
#   "backend": "python" | "node",
#   "frameworks": ["react", "flask", ...],
#   "has_content": true
# }
```

### 7. Project-Agnostic

Works with any web app, not just portfolios:

```bash
# Dashboard
python symphony.py run --project ./dashboard --goal "Admin dashboard with charts"

# E-commerce
python symphony.py run --project ./shop --goal "Product catalog with cart"

# Landing page
python symphony.py run --project ./landing --goal "SaaS landing page"
```

## Migration Steps

### Step 1: Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

New dependencies:
- `requests` - For server readiness checks
- Same smolagents, openai, helium, flask, etc.

### Step 2: Test with Legacy Mode

Symphony-Lite automatically uses v2 if available, falls back to v1:

```bash
# This will use v2 automatically
python symphony.py run --project projects/portfolio --goal "Test"
```

### Step 3: Update Custom Code (if any)

If you've built custom integrations, update them:

**Update Brain agent usage**:
```python
# Old
from agents.brain_agent import brain_agent
brain_agent.run(instructions)

# New
from agents.brain_agent_factory import create_brain_agent, BrainConfig
brain = create_brain_agent(project_root, BrainConfig())
brain.run(instructions)
```

**Update Sensory agent usage**:
```python
# Old
from agents.sensory_agent_web import inspect_site
report = inspect_site(url)  # Returns dict

# New
from agents.sensory_agent_web_v2 import inspect_site
report = inspect_site(url, run_id)  # Returns SensoryReport
```

### Step 4: Update Orchestrator Calls

```python
# Old
result = run_workflow(project_path, goal, fe_port, be_port, steps)

# New
from agents.brain_agent_factory import BrainConfig
config = BrainConfig(model_id="gpt-4o")
result = run_workflow(
    project_path, goal, fe_port, be_port, steps,
    brain_config=config,
    run_id="unique_id",
    open_browser=False
)
```

### Step 5: Verify Tests Pass

Run your test suite to ensure nothing broke:

```bash
# Test empty folder
mkdir test-empty && python symphony.py run --project test-empty --goal "Portfolio"

# Test existing project
python symphony.py run --project projects/portfolio --goal "Add testimonials"

# Test with new flags
python symphony.py run --project . --goal "Dashboard" --open --brain-model gpt-4o
```

## Backward Compatibility

### What Still Works

All v1.x commands work without changes:

```bash
# This still works!
python symphony.py run --project projects/portfolio --goal "Portfolio" --steps 1
```

The system automatically:
- Uses v2 if available
- Falls back to v1 if v2 not found
- Converts between dict and SensoryReport formats
- Maintains legacy function signatures

### Deprecation Timeline

- **v2.0 (now)**: v2 files added, v1 still works
- **v2.5 (future)**: Deprecation warnings for v1
- **v3.0 (future)**: Remove v1 files entirely

## Troubleshooting

### "ModuleNotFoundError: No module named 'agents.brain_agent_factory'"

**Solution**: Update your code to import correctly:

```python
# Correct
from agents.brain_agent_factory import create_brain_agent

# Wrong
from brain_agent_factory import create_brain_agent
```

### "AttributeError: 'dict' object has no attribute 'passes_all_gates'"

**Solution**: Ensure you're using v2 sensory agent:

```python
# Correct
from agents.sensory_agent_web_v2 import inspect_site

# Wrong
from agents.sensory_agent_web import inspect_site  # Returns dict, not SensoryReport
```

### "TypeError: run_workflow() got an unexpected keyword argument 'brain_config'"

**Solution**: Import v2 orchestrator:

```python
# Correct
from orchestrator_v2 import run_workflow

# Wrong
from orchestrator import run_workflow  # Old version
```

### Multiple Runs Conflicting

**Solution**: Provide unique run_ids:

```python
import time

run_id = f"run_{int(time.time())}"
result = run_workflow(..., run_id=run_id)
```

## Benefits of Upgrading

### For Users

- Works with any web app type
- Better error messages
- Browser auto-opens on success
- Clear quality gate feedback
- Organized artifacts by run
- Faster server startup (readiness checks)

### For Developers

- No global state
- Type-safe contracts
- Easier testing (isolated runs)
- Better code organization
- Extensible architecture
- Concurrent execution support

## Getting Help

- Read `API_CONTRACT.md` for report format
- Open an issue on GitHub for bugs

## Example: Full Migration

**Before (v1.x)**:
```python
# main.py
from orchestrator import run_workflow

result = run_workflow(
    "projects/portfolio",
    "Dark portfolio",
    3000,
    5000,
    1
)

print(f"Status: {result.get('status')}")
print(f"Alignment: {result['passes']['pass_1']['alignment_score']}")
```

**After (v2.0)**:
```python
# main.py
from orchestrator_v2 import run_workflow
from agents.brain_agent_factory import BrainConfig

config = BrainConfig(
    model_id="gpt-4o",
    max_steps=15,
    temperature=0.7,
    verbosity=1
)

result = run_workflow(
    "projects/portfolio",
    "Dark portfolio with animations",
    3000,
    5000,
    steps=3,
    brain_config=config,
    run_id="portfolio_v1",
    open_browser=True
)

# Type-safe access
final_report = result.get("final_report")
if final_report:
    from agents.sensory_contract import SensoryReport
    report = SensoryReport.from_dict(final_report)
    
    print(f"Status: {report.status}")
    print(f"Alignment: {report.alignment_score:.2f}")
    print(f"All gates passed: {report.passes_all_gates()}")
    
    if not report.passes_all_gates():
        print("Failing gates:")
        for gate in report.get_failing_gates():
            print(f"  - {gate}")
```

---

**Ready to upgrade?** Start with `python symphony.py run --help` to see the new options!

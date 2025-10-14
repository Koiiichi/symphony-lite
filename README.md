# Symphony-Lite

Autonomous AI-powered web application development framework. Uses natural language instructions to generate, test, and refine web applications through an iterative agent-based workflow.

## Features

- Project-agnostic architecture supporting multiple application types
- Automated code generation via LLM-powered Brain agent
- Visual and functional testing with Sensory agent
- Iterative improvement loop with quality gate validation
- Type-safe communication contracts between agents
- Concurrent execution support with isolated run environments
- Automatic server management and dependency installation

## Requirements

- Python 3.8+
- OpenAI API key (or compatible LLM provider)
- Chrome/Chromium browser (for Helium-based testing)

## Installation

\`\`\`bash
git clone <repository-url>
cd symphony-lite
\`\`\`

Create \`.env\` file:

\`\`\`env
OPENAI_API_KEY=your_api_key_here
\`\`\`

First run automatically creates virtual environment and installs dependencies:

\`\`\`bash
python symphony.py run --project <path> --goal "<description>"
\`\`\`

## Usage

### Basic Commands

**Run workflow:**

\`\`\`bash
python symphony.py run --project PATH --goal "DESCRIPTION"
\`\`\`

**Validate project structure:**

\`\`\`bash
python symphony.py validate --project PATH
\`\`\`

**System information:**

\`\`\`bash
python symphony.py info
\`\`\`

### CLI Options

#### Required Parameters

- \`--project PATH\` - Target project directory (existing or new)
- \`--goal TEXT\` - Natural language description of desired application

#### Server Configuration

- \`--fe-port INT\` - Frontend server port (default: 3000)
- \`--be-port INT\` - Backend server port (default: 5000)

#### Workflow Control

- \`--steps INT\` - Maximum test-and-fix iterations (default: 3, range: 1-5)
- \`--max-agent-steps INT\` - Brain agent step limit per generation (default: 15)
- \`--verbosity INT\` - Logging level: 0=quiet, 1=normal, 2=verbose (default: 1)

#### Model Configuration

- \`--brain-model TEXT\` - LLM model identifier (default: gpt-4o)
  - Supported: gpt-4o, gpt-4-turbo, claude-3-opus, claude-3-sonnet
- \`--temperature FLOAT\` - Model temperature 0.0-1.0 (default: 0.7)

#### User Interface

- \`--open\` - Auto-open browser on successful completion

### Examples

**Create new portfolio from scratch:**

\`\`\`bash
python symphony.py run --project portfolio --goal "Professional portfolio with dark theme and contact form"
\`\`\`

**Enhance existing application:**

\`\`\`bash
python symphony.py run --project projects/dashboard --goal "Add user authentication with JWT tokens"
\`\`\`

**Use alternative model:**

\`\`\`bash
python symphony.py run --project app --goal "E-commerce cart" --brain-model claude-3-opus --temperature 0.5
\`\`\`

**Quick iteration:**

\`\`\`bash
python symphony.py run --project app --goal "Fix mobile responsiveness" --steps 1 --open
\`\`\`

## Architecture

### Agent System

**Brain Agent**

- Generates code using LLM (smolagents CodeAgent)
- Factory-based instantiation with project-scoped tools
- Closured file operations with path traversal protection
- Supports multiple LLM providers via LiteLLM

**Sensory Agent**

- Automated browser testing using Helium/Selenium
- Visual analysis via GPT-4o Vision
- Form interaction testing
- Basic accessibility validation
- Returns structured SensoryReport dataclass

**Runner**

- Manages frontend (HTTP server) and backend (Flask) processes
- Server readiness polling with timeout handling
- Graceful shutdown and cleanup
- Isolated dependency installation per project

### Quality Gates

Applications must pass these thresholds before completion:

| Gate | Threshold | Description |
|------|-----------|-------------|
| Alignment | >= 0.90 | Visual layout consistency |
| Spacing | >= 0.90 | Whitespace uniformity |
| Contrast | >= 0.75 | WCAG AA text contrast |
| Form | Working | Contact form submission |
| Accessibility | <= 5 violations | Basic a11y compliance |
| Playwright | All Pass | E2E tests (if present) |

See \`API_CONTRACT.md\` for detailed gate specifications and fix policies.

### Project Structure

**For existing projects:**

\`\`\`
project/
├── frontend/
│   ├── index.html
│   └── package.json (optional)
├── backend/
│   ├── app.py
│   └── requirements.txt
\`\`\`

**For new projects:**

Symphony-Lite scaffolds appropriate structure based on goal description. Supports:

- Static HTML/CSS/JS frontends
- React/Vue/Vite-based SPAs
- Flask backends with CORS
- Node.js backends (if detected)

### Communication Protocol

Agents communicate via typed dataclasses:

**SensoryReport** - Sensory agent to Brain agent

\`\`\`python
@dataclass
class SensoryReport:
    status: str  # "pass" | "needs_fix"
    alignment_score: float
    spacing_score: float
    contrast_score: float
    visible_sections: List[str]
    interaction: InteractionResult
    a11y: AccessibilityResult
    playwright: Optional[PlaywrightResult]
    screens: List[Screenshot]
\`\`\`

**BrainConfig** - CLI to Brain agent factory

\`\`\`python
@dataclass
class BrainConfig:
    model_type: str = "LiteLLMModel"
    model_id: str = "gpt-4o"
    max_steps: int = 15
    temperature: float = 0.7
    verbosity: int = 1
    timeout: int = 180
\`\`\`

See \`API_CONTRACT.md\` for complete protocol specification.

### Artifact Management

Each run generates isolated artifacts:

\`\`\`
artifacts/
  run_20251013_143022/
    step_1_initial.png
    step_2_scroll.png
    step_3_submit.png
    report.json
\`\`\`

Run ID format: \`run_YYYYMMDD_HHMMSS\`

## Configuration

### Environment Variables

- \`OPENAI_API_KEY\` - OpenAI API key (required)
- \`ANTHROPIC_API_KEY\` - Anthropic API key (optional, for Claude models)

### Dependencies

Core requirements in \`requirements.txt\`:

- typer - CLI framework
- rich - Terminal formatting
- smolagents - Agent framework
- openai - OpenAI API client
- helium - Browser automation
- selenium - WebDriver support
- flask - Backend server
- flask-cors - CORS handling
- requests - HTTP client

## Development

### Running Tests

\`\`\`bash
# Test empty folder scaffold
mkdir test-app && python symphony.py run --project test-app --goal "Simple dashboard"

# Test existing project enhancement
python symphony.py run --project projects/portfolio --goal "Add testimonials section"

# Test with verbose logging
python symphony.py run --project test-app --goal "Fix layout" --verbosity 2
\`\`\`

### Extending

**Add custom tools to Brain agent:**

\`\`\`python
# agents/brain_agent_factory.py
@tool
def custom_tool(param: str) -> str:
    """Tool description for LLM."""
    # Implementation
    return result

# Add to tools list in create_brain_agent()
\`\`\`

**Custom quality gates:**

\`\`\`python
# agents/sensory_contract.py
custom_thresholds = {
    "alignment": 0.95,
    "spacing": 0.95,
    "contrast": 0.80
}
report.passes_all_gates(custom_thresholds)
\`\`\`

**Alternative LLM providers:**

\`\`\`bash
# Set provider in config
python symphony.py run --project app --goal "..." --brain-model "anthropic/claude-3-opus"
\`\`\`

## Troubleshooting

**Import errors on first run:**

Delete \`venv/\` directory and run again. Symphony-Lite will recreate environment.

**Flask/Werkzeug version conflicts:**

Ensure \`requirements.txt\` specifies \`Flask>=2.3.0\` and \`flask-cors>=4.0.0\`

**Browser automation failures:**

Verify Chrome/Chromium installed. Helium requires ChromeDriver (auto-downloaded).

**Quality gates failing:**

Use \`--verbosity 2\` to see detailed gate analysis. Check artifacts directory for screenshots.

**Concurrent runs interfering:**

Each run uses unique \`run_id\` for isolation. Verify different project paths or manual run_id override.

## Documentation

- \`API_CONTRACT.md\` - Sensory-Brain communication protocol
- \`MIGRATION.md\` - Upgrading from v1.x to v2.0
- \`LICENSE\` - MIT License

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome. Areas for enhancement:

- Additional testing frameworks (Playwright E2E, visual regression)
- LLM provider integrations (Gemini, local models)
- Project type templates (Next.js, FastAPI, etc.)
- Quality gate extensions (performance, security)

## Acknowledgments

Built with:

- smolagents - Agent framework
- LiteLLM - Multi-provider LLM interface
- Helium - Browser automation
- Rich - Terminal UI

# Symphony-Lite# Symphony-Lite



Autonomous AI-powered web application development framework. Uses natural language instructions to generate, test, and refine web applications through an iterative agent-based workflow.Build web applications with natural language.



## FeaturesDescribe what you want to build, and Symphony-Lite does the rest. AI agents generate code, test functionality, and apply improvements automatically until your vision becomes reality.



- Project-agnostic architecture supporting multiple application types## Get Started

- Automated code generation via LLM-powered Brain agent

- Visual and functional testing with Sensory agentClone Symphony-Lite:

- Iterative improvement loop with quality gate validation

- Type-safe communication contracts between agents```bash

- Concurrent execution support with isolated run environmentsgit clone <repository-url>

- Automatic server management and dependency installationcd symphony-lite

```

## Requirements

Create `.env`:

- Python 3.8+```env

- OpenAI API key (or compatible LLM provider)OPENAI_API_KEY=your_openai_api_key_here

- Chrome/Chromium browser (for Helium-based testing)```



## InstallationRun anything (first run automatically sets up everything):



```bash```bash

git clone <repository-url>python symphony.py run --project "projects/portfolio" --goal "Dark portfolio with contact form"

cd symphony-lite```

```

That's it. Symphony-Lite automatically handles virtual environments, dependencies, code generation, server management, visual testing, and iterative improvements.

Create `.env` file:

```env## How It Works

OPENAI_API_KEY=your_api_key_here

```Three specialized agents work together:



First run automatically creates virtual environment and installs dependencies:**Brain Agent**  

```bashGenerates and refines code from natural language descriptions

python symphony.py run --project <path> --goal "<description>"

```**Sensory Agent**  

Tests applications like a human user - scrolling, clicking, filling forms

## Usage

**Runner**  

### Basic CommandsManages servers and dependencies automatically



**Run workflow:**The system iterates until quality gates are met: visual alignment, working forms, and responsive design.

```bash

python symphony.py run --project PATH --goal "DESCRIPTION"## Commands

```

Run the workflow:

**Validate project structure:**```bash

```bashpython symphony.py run --project PATH --goal "Your description"

python symphony.py validate --project PATH```

```

Validate project structure:

**System information:**```bash

```bashpython symphony.py validate --project PATH

python symphony.py info```

```

Display system information:

### CLI Options```bash

python symphony.py info

#### Required Parameters```

- `--project PATH` - Target project directory (existing or new)

- `--goal TEXT` - Natural language description of desired application### Options



#### Server Configuration#### Required

- `--fe-port INT` - Frontend server port (default: 3000)`--project PATH` Target project folder (existing or empty)  

- `--be-port INT` - Backend server port (default: 5000)`--goal TEXT` What you want to build or improve  



#### Workflow Control#### Server Configuration

- `--steps INT` - Maximum test-and-fix iterations (default: 3, range: 1-5)`--fe-port INT` Frontend port (default: 3000)  

- `--max-agent-steps INT` - Brain agent step limit per generation (default: 15)`--be-port INT` Backend port (default: 5000)  

- `--verbosity INT` - Logging level: 0=quiet, 1=normal, 2=verbose (default: 1)

#### Workflow Control

#### Model Configuration`--steps INT` Test-and-fix passes (default: 3, range: 1-5)  

- `--brain-model TEXT` - LLM model identifier (default: gpt-4o)`--max-agent-steps INT` Brain agent iteration limit (default: 15)  

  - Supported: gpt-4o, gpt-4-turbo, claude-3-opus, claude-3-sonnet`--verbosity INT` Log detail level: 0=quiet, 1=normal, 2=verbose (default: 1)  

- `--temperature FLOAT` - Model temperature 0.0-1.0 (default: 0.7)

#### Brain Agent Configuration

#### User Interface`--brain-model TEXT` LLM model ID (default: gpt-4o)  

- `--open` - Auto-open browser on successful completion  Examples: gpt-4o, gpt-4-turbo, claude-3-opus, claude-3-sonnet  

`--temperature FLOAT` Creativity level: 0.0=focused, 1.0=creative (default: 0.7)  

### Examples

#### User Experience

**Create new portfolio from scratch:**`--open` Auto-open browser on success  

```bash`--no-open` Don't auto-open browser (default)

python symphony.py run --project portfolio --goal "Professional portfolio with dark theme and contact form"

```## Project Structure



**Enhance existing application:**### Existing Projects

```bash

python symphony.py run --project projects/dashboard --goal "Add user authentication with JWT tokens"Your project needs:

```

```

**Use alternative model:**project/

```bash├── frontend/

python symphony.py run --project app --goal "E-commerce cart" --brain-model claude-3-opus --temperature 0.5│   └── index.html

```├── backend/

│   ├── app.py

**Quick iteration:**│   └── requirements.txt

```bash```

python symphony.py run --project app --goal "Fix mobile responsiveness" --steps 1 --open

```Symphony-Lite automatically detects your tech stack and works with it.



## Architecture### Empty Projects



### Agent SystemStart from scratch! Symphony-Lite will:

1. Detect the empty folder

**Brain Agent**2. Generate appropriate scaffolding based on your goal

- Generates code using LLM (smolagents CodeAgent)3. Create frontend and backend directories

- Factory-based instantiation with project-scoped tools4. Set up initial files and dependencies

- Closured file operations with path traversal protection5. Build your application iteratively

- Supports multiple LLM providers via LiteLLM

```bash

**Sensory Agent**mkdir my-new-app

- Automated browser testing using Helium/Seleniumpython symphony.py run --project my-new-app --goal "Dashboard with user management"

- Visual analysis via GPT-4o Vision```

- Form interaction testing

- Basic accessibility validationSymphony-Lite is **project-agnostic** - it works with portfolios, dashboards, e-commerce sites, landing pages, and more.

- Returns structured SensoryReport dataclass

## Quality Gates

**Runner**

- Manages frontend (HTTP server) and backend (Flask) processesSymphony-Lite includes automatic quality gates that must pass before completion:

- Server readiness polling with timeout handling

- Graceful shutdown and cleanup| Gate | Threshold | Description |

- Isolated dependency installation per project|------|-----------|-------------|

| **Alignment** | ≥ 0.90 | Visual layout consistency and element positioning |

### Quality Gates| **Spacing** | ≥ 0.90 | Whitespace distribution and padding uniformity |

| **Contrast** | ≥ 0.75 | Text readability and color accessibility |

Applications must pass these thresholds before completion:| **Form Testing** | Working | Contact form successfully submits |

| **Accessibility** | ≤ 5 violations | WCAG compliance and screen reader support |

| Gate | Threshold | Description || **Playwright** | All Pass | Optional E2E test suite (if present) |

|------|-----------|-------------|

| Alignment | >= 0.90 | Visual layout consistency |The Brain agent automatically applies targeted fixes when gates fail, ensuring production-ready applications.

| Spacing | >= 0.90 | Whitespace uniformity |

| Contrast | >= 0.75 | WCAG AA text contrast |See `API_CONTRACT.md` for complete quality gate details and fix policies.

| Form | Working | Contact form submission |

| Accessibility | <= 5 violations | Basic a11y compliance |## Testing

| Playwright | All Pass | E2E tests (if present) |

The system includes:

See `API_CONTRACT.md` for detailed gate specifications and fix policies.

- Automated visual testing with GPT-4o Vision

### Project Structure- Form interaction validation (click, scroll, submit)

- Accessibility compliance checking (ARIA, contrast, alt text)

**For existing projects:**- Server readiness validation (URL polling)

```- Screenshot artifacts saved per run

project/

├── frontend/Optional Playwright integration available for advanced E2E testing scenarios.

│   ├── index.html

│   └── package.json (optional)## Examples

├── backend/

│   ├── app.py### Basic Usage

│   └── requirements.txt

```Portfolio website:

```bash

**For new projects:**  python symphony.py run --project "projects/portfolio" --goal "Professional dark theme with project grid"

Symphony-Lite scaffolds appropriate structure based on goal description. Supports:```

- Static HTML/CSS/JS frontends

- React/Vue/Vite-based SPAsE-commerce landing:

- Flask backends with CORS```bash

- Node.js backends (if detected)python symphony.py run --project "projects/ecommerce" --goal "Product showcase with newsletter signup"

```

### Communication Protocol

Dashboard interface:

Agents communicate via typed dataclasses:```bash

python symphony.py run --project "projects/dashboard" --goal "Clean data dashboard with responsive tables"

**SensoryReport** - Sensory agent to Brain agent```

```python

@dataclass### Advanced Usage

class SensoryReport:

    status: str  # "pass" | "needs_fix"Use Claude instead of GPT-4o:

    alignment_score: float```bash

    spacing_score: floatpython symphony.py run \

    contrast_score: float  --project "projects/portfolio" \

    visible_sections: List[str]  --goal "Minimalist portfolio" \

    interaction: InteractionResult  --brain-model "claude-3-opus" \

    a11y: AccessibilityResult  --temperature 0.5

    playwright: Optional[PlaywrightResult]```

    screens: List[Screenshot]

```Quick test with browser auto-open:

```bash

**BrainConfig** - CLI to Brain agent factorypython symphony.py run \

```python  --project "projects/portfolio" \

@dataclass  --goal "Add testimonials section" \

class BrainConfig:  --steps 1 \

    model_type: str = "LiteLLMModel"  --open

    model_id: str = "gpt-4o"```

    max_steps: int = 15

    temperature: float = 0.7Verbose logging for debugging:

    verbosity: int = 1```bash

    timeout: int = 180python symphony.py run \

```  --project "projects/portfolio" \

  --goal "Fix mobile layout" \

See `API_CONTRACT.md` for complete protocol specification.  --verbosity 2

```

### Artifact Management

Start from empty folder:

Each run generates isolated artifacts:```bash

```mkdir my-saas-app

artifacts/python symphony.py run \

  run_20251013_143022/  --project "my-saas-app" \

    step_1_initial.png  --goal "SaaS landing page with pricing tiers" \

    step_2_scroll.png  --open

    step_3_submit.png```

    report.json

```## Troubleshooting



Run ID format: `run_YYYYMMDD_HHMMSS`**"can't open file symphony.py"**  

Run commands from the symphony-lite root directory, not from project subdirectories.

## Configuration

**"OPENAI_API_KEY not found"**  

### Environment VariablesCreate a `.env` file with your OpenAI API key.



- `OPENAI_API_KEY` - OpenAI API key (required)**Dependencies not installing**  

- `ANTHROPIC_API_KEY` - Anthropic API key (optional, for Claude models)Symphony-Lite handles this automatically on first run. If issues persist, delete the `venv` folder and try again.



### Dependencies**"How long will it take?"**  

See QUICK_REFERENCE.md for expected runtimes by pass count. Use `--steps 1` for quick tests.

Core requirements in `requirements.txt`:

- typer - CLI framework**"Seeing weird errors in logs?"**  

- rich - Terminal formattingInternal agent debugging messages are normal. Look for status indicators: RUNNING, COMPLETE, FAILED. See QUICK_REFERENCE.md for details.

- smolagents - Agent framework

- openai - OpenAI API client## Requirements

- helium - Browser automation

- selenium - WebDriver support- Python 3.8+

- flask - Backend server- OpenAI API key

- flask-cors - CORS handling- Chrome browser

- requests - HTTP client

## Architecture

## Development

Symphony-Lite v2.0 features:

### Running Tests

- **Factory Pattern**: Project-scoped agents without global state

```bash- **Type-Safe Contracts**: Standardized `SensoryReport` format

# Test empty folder scaffold- **Path Safety**: Prevents directory traversal attacks

mkdir test-app && python symphony.py run --project test-app --goal "Simple dashboard"- **Run Isolation**: Artifacts organized by unique run ID

- **Concurrent Execution**: Multiple runs supported simultaneously

# Test existing project enhancement- **Stack Detection**: Automatic introspection of existing projects

python symphony.py run --project projects/portfolio --goal "Add testimonials section"

See `API_CONTRACT.md` for technical details and `MIGRATION.md` for upgrade guidance.

# Test with verbose logging

python symphony.py run --project test-app --goal "Fix layout" --verbosity 2## Artifacts

```

Each run creates organized artifacts:

### Extending

```

**Add custom tools to Brain agent:**artifacts/

```python  run_20251013_143022/

# agents/brain_agent_factory.py    step_1_initial.png

@tool    step_2_scroll.png

def custom_tool(param: str) -> str:    step_3_submit.png

    """Tool description for LLM."""    report.json

    # Implementation```

    return result

Screenshots capture every interaction for debugging and verification.

# Add to tools list in create_brain_agent()

```## Documentation



**Custom quality gates:**- `API_CONTRACT.md` - Sensory-brain communication format

```python- `MIGRATION.md` - Upgrading from v1.x to v2.0

# agents/sensory_contract.py- `QUICK_REFERENCE.md` - Loop control and runtime guidance

custom_thresholds = {- `LOOP_CONTROL.md` - Detailed agent behavior documentation

    "alignment": 0.95,- `FIXES_APPLIED.md` - Quality improvement tracking

    "spacing": 0.95,

    "contrast": 0.80## Contributing

}

report.passes_all_gates(custom_thresholds)Symphony-Lite is designed for extensibility. Areas for contribution include additional testing frameworks, support for more project types, and enhanced visual analysis capabilities.

```

Pull requests welcome! See `MIGRATION.md` for architecture details.

**Alternative LLM providers:**

```bash## License

# Set provider in config

python symphony.py run --project app --goal "..." --brain-model "anthropic/claude-3-opus"MIT

```

## Troubleshooting

**Import errors on first run:**  
Delete `venv/` directory and run again. Symphony-Lite will recreate environment.

**Flask/Werkzeug version conflicts:**  
Ensure `requirements.txt` specifies `Flask>=2.3.0` and `flask-cors>=4.0.0`

**Browser automation failures:**  
Verify Chrome/Chromium installed. Helium requires ChromeDriver (auto-downloaded).

**Quality gates failing:**  
Use `--verbosity 2` to see detailed gate analysis. Check artifacts directory for screenshots.

**Concurrent runs interfering:**  
Each run uses unique `run_id` for isolation. Verify different project paths or manual run_id override.

## Documentation

- `API_CONTRACT.md` - Sensory-Brain communication protocol
- `MIGRATION.md` - Upgrading from v1.x to v2.0
- `LICENSE` - MIT License

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

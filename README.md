# Symphony-Lite

Build web applications with natural language.

Describe what you want to build, and Symphony-Lite does the rest. AI agents generate code, test functionality, and apply improvements automatically until your vision becomes reality.

## Get Started

Clone Symphony-Lite:

```bash
git clone <repository-url>
cd symphony-lite
```

Create `.env`:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

Run anything (first run automatically sets up everything):

```bash
python symphony.py run --project "projects/portfolio" --goal "Dark portfolio with contact form"
```

That's it. Symphony-Lite automatically handles virtual environments, dependencies, code generation, server management, visual testing, and iterative improvements.

## How It Works

Three specialized agents work together:

**Brain Agent**  
Generates and refines code from natural language descriptions

**Sensory Agent**  
Tests applications like a human user - scrolling, clicking, filling forms

**Runner**  
Manages servers and dependencies automatically

The system iterates until quality gates are met: visual alignment, working forms, and responsive design.

## Commands

Run the workflow:
```bash
python symphony.py run --project PATH --goal "Your description"
```

Validate project structure:
```bash
python symphony.py validate --project PATH
```

### Options

`--project PATH` Target project folder  
`--goal TEXT` What you want to build or improve  
`--fe-port INT` Frontend port (default: 3000)  
`--be-port INT` Backend port (default: 5000)  
`--steps INT` Improvement iterations (default: 1)

## Project Structure

Your project needs:

```
project/
├── frontend/
│   └── index.html
├── backend/
│   ├── app.py
│   └── requirements.txt
```

Symphony-Lite works with any project that follows this structure.

## Testing

The system includes:

- Automated visual testing with GPT-4o
- Form interaction validation  
- Accessibility compliance checking
- Cross-browser compatibility tests

Optional Playwright integration available for advanced testing scenarios.

## Examples

Portfolio website:
```bash
python symphony.py run --project "projects/portfolio" --goal "Professional dark theme with project grid"
```

E-commerce landing:
```bash
python symphony.py run --project "projects/ecommerce" --goal "Product showcase with newsletter signup"
```

Dashboard interface:
```bash
python symphony.py run --project "projects/dashboard" --goal "Clean data dashboard with responsive tables"
```

## Troubleshooting

**"can't open file symphony.py"**  
Run commands from the symphony-lite root directory, not from project subdirectories.

**"OPENAI_API_KEY not found"**  
Create a `.env` file with your OpenAI API key.

**Dependencies not installing**  
Symphony-Lite handles this automatically on first run. If issues persist, delete the `venv` folder and try again.

## Requirements

- Python 3.8+
- OpenAI API key
- Chrome browser

## Contributing

Symphony-Lite is designed for extensibility. Areas for contribution include additional testing frameworks, support for more project types, and enhanced visual analysis capabilities.

## License

MIT

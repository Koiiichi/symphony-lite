# Symphony-Lite

Build web applications with natural language.

Describe what you want to build, and Symphony-Lite does the rest. AI agents generate code, test functionality, and apply improvements automatically until your vision becomes reality.

## Get Started

Install dependencies and create your environment file:

```bash
pip install -r requirements.txt
```

Create `.env`:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

Build anything:

```bash
python cli.py run --project "my-app" --goal "Dark portfolio with contact form"
```

That's it. Symphony-Lite handles code generation, server management, visual testing, and iterative improvements.

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
python cli.py run --project PATH --goal "Your description"
```

Validate project structure:
```bash
python cli.py validate --project PATH
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
python cli.py run --project "portfolio" --goal "Professional dark theme with project grid"
```

E-commerce landing:
```bash
python cli.py run --project "store" --goal "Product showcase with newsletter signup"
```

Dashboard interface:
```bash
python cli.py run --project "admin" --goal "Clean data dashboard with responsive tables"
```

## Requirements

- Python 3.8+
- OpenAI API key
- Chrome browser

## Contributing

Symphony-Lite is designed for extensibility. Areas for contribution include additional testing frameworks, support for more project types, and enhanced visual analysis capabilities.

## License

MIT

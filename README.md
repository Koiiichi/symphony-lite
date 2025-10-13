# Symphony-Lite

An autonomous development workflow. Multiple AI agents coordinate to build, deploy, and test web applications.

## Overview

Symphony-Lite simulates a small development team using three specialized agents:

- **Brain Agent** - Generates frontend and backend code
- **Runner** - Manages local servers and dependencies  
- **Sensory Agent** - Visual testing with browser automation

## Quick Start

```bash
python orchestrator_verbose.py
```

The system will generate a dark-themed portfolio website, start local servers, and perform automated visual testing.

## Architecture

Built on SmolAgents framework with OpenAI integration. The Brain Agent uses GPT models for code generation, while the Sensory Agent leverages GPT-4o vision capabilities for UI analysis.

## Requirements

- Python 3.8+
- OpenAI API key in `.env` file
- Chrome browser for visual testing

## Project Structure

```
symphony-lite/
├── agents/              # AI agent definitions
├── projects/portfolio/  # Generated web application
├── artifacts/          # Screenshots and test outputs
├── orchestrator.py     # Main workflow coordinator
└── runner.py           # Server management
```

## Status

First working version. Successfully demonstrates autonomous code generation, deployment, and visual verification of web applications.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
- `pytest -n auto` - Run all tests in parallel across cores
- `pytest tests/path/to/test.py` - Run a specific test file
- `pytest tests/path/to/test.py::test_function` - Run a specific test function
- `pytest -k "test_name"` - Run tests matching pattern
- `pytest -m "not slow"` - Run tests excluding slow ones

### Code Quality
- `ruff check` - Run linting
- `ruff format` - Format code
- `pre-commit install` - Install pre-commit hooks (run once)
- `pre-commit run --all-files` - Run all pre-commit checks

### Installation & Setup
- `pip install -e .` - Install in development mode
- `pip install -e .[dev]` - Install with development dependencies
- `mini` or `mini -v` - Run the main CLI interface

### Entry Points
- `mini` - Main CLI interface (simple UI)
- `mini -v` - Visual UI with Textual interface
- `mini-extra` - Extended utilities and configuration
- `python -m minisweagent.run.hello_world` - Run basic example

### Connecting to LM Studio or OpenAI-compatible APIs
Set environment variables:
```bash
export OPENAI_API_BASE=http://localhost:1234/v1  # Your LM Studio URL
export OPENAI_API_KEY=fake-key                   # Any value for local servers
mini --model qwen3  # Use any model name (qwen3, llama2, etc.)
```

Or configure permanently:
```bash
mini-extra config set OPENAI_API_BASE http://localhost:1234/v1
mini-extra config set OPENAI_API_KEY fake-key
```

**Smart Model Selection**: When `OPENAI_API_BASE` is set to a localhost URL, ANY model name will automatically use the OpenAI-compatible client. Common local model names (qwen, llama, mistral, phi, gemma, etc.) are also automatically detected when any `OPENAI_API_BASE` is configured.

## Architecture Overview

Mini-SWE-agent is built around three core components that follow strict protocols:

### Core Components
1. **Agent** (`src/minisweagent/agents/`) - Controls the agent loop and decision-making
2. **Environment** (`src/minisweagent/environments/`) - Executes commands (local, docker, etc.)
3. **Model** (`src/minisweagent/models/`) - Interfaces with language models

### Key Design Principles
- **Minimalist**: Core agent is ~100 lines, emphasizes simplicity over features
- **Protocol-based**: Uses Python protocols for loose coupling between components
- **Stateless execution**: Each command runs independently via `subprocess.run`
- **Linear history**: Messages append to conversation, no complex state management
- **Bash-only tools**: No custom tools - relies entirely on shell commands

### File Structure
```
src/minisweagent/
├── __init__.py          # Protocols and base interfaces
├── agents/              # Agent control flow implementations
│   └── default.py       # Main 100-line agent implementation
├── environments/        # Command execution environments
│   ├── local.py         # Local subprocess execution
│   ├── docker.py        # Docker container execution
│   └── extra/           # Additional environments (SWE-ReX, etc.)
├── models/              # Language model interfaces
│   ├── openai_model.py  # Direct OpenAI-compatible API client
│   ├── litellm_model.py # LiteLLM wrapper for multiple providers
│   ├── anthropic.py     # Anthropic-specific enhancements
│   └── utils/           # Model utilities (caching, etc.)
├── run/                 # Entry point scripts and use cases
│   ├── mini.py          # Main CLI interface
│   ├── hello_world.py   # Basic example
│   └── extra/           # Additional run scripts (SWEBench, etc.)
└── config/              # Configuration templates and YAML files
```

### Configuration System
- Uses Jinja2 templates for flexible configuration
- Dataclasses for type-safe config objects
- YAML files in `src/minisweagent/config/` for common scenarios
- Global config stored in `~/.config/mini-swe-agent/.env`

### Agent Control Flow
The default agent follows a simple loop:
1. Parse action from LLM response (expects ```bash code blocks)
2. Execute command via environment
3. Add observation to message history
4. Repeat until task completion or limits exceeded

### Extension Points
- Create new agents by implementing the `Agent` protocol
- Add environments by implementing the `Environment` protocol  
- Support new models via the `Model` protocol
- Add run scripts in `src/minisweagent/run/` for new use cases

## Development Guidelines

### Code Style
- Target Python 3.10+
- Use type annotations (prefer `list` over `List`)
- Use `pathlib` instead of `os.path`
- Use `dataclass` for configuration objects
- Keep code minimal and concise
- Avoid unnecessary exception handling
- Use `typer` for CLI interfaces

### Testing Guidelines
- Use `pytest`, not `unittest`
- Avoid mocking unless explicitly required
- Write meaningful tests that check multiple failure points
- Use `assert func() == expected` instead of intermediate variables
- First arg to `pytest.mark.parametrize` should be tuple, second should be list

### Project Philosophy
- Simplicity over features - prefer creating new components over making existing ones complex
- Code should be hackable and readable at a glance
- Focus on the language model capabilities rather than agent scaffolding
- Everything should be easily sandboxable and deployable
- how to stash all changes
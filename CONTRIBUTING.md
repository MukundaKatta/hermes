# Contributing to Hermes

## Development Setup

```bash
# Clone the repo
git clone https://github.com/MukundaKatta/hermes.git
cd hermes

# Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

## Running Tests

```bash
# Using Make
make test

# Or directly
PYTHONPATH=src python3 -m pytest tests/ -v --tb=short
```

## Linting

```bash
make lint
# or
python3 -m ruff check src/ tests/
```

## Project Layout

```
src/hermes/       Core library
  core.py         SuperAgent orchestration
  sandbox.py      Code execution sandbox
  tools.py        Tool registry
  config.py       Configuration
  cli.py          CLI entry point
tests/            Test suite
docs/             Documentation
```

## Pull Request Checklist

- [ ] All tests pass (`make test`)
- [ ] No lint errors (`make lint`)
- [ ] New code has type hints
- [ ] New features include tests

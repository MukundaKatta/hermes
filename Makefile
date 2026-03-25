.PHONY: install test lint run clean

install:
	pip install -e ".[dev]"

test:
	PYTHONPATH=src python3 -m pytest tests/ -v --tb=short

lint:
	python3 -m ruff check src/ tests/

run:
	PYTHONPATH=src python3 -m hermes --help

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

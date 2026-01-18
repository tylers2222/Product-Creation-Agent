.PHONY: install install-dev install-gui test lint format type-check clean run

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-gui:
	pip install -e ".[gui]"

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v -m integration

test-cov:
	pytest tests/ --cov=src/product_agent --cov-report=html

# Code Quality
lint:
	ruff check src/ tests/

lint-fix:
	ruff check src/ tests/ --fix

format:
	black src/ tests/

format-check:
	black src/ tests/ --check

type-check:
	mypy src/

# Running
run:
	python -m product_agent

run-api:
	uvicorn product_agent.api.app:app --reload

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

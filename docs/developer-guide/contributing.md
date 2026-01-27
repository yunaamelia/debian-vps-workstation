# Contributing Guide

Thank you for your interest in contributing!

## Development Setup

1. Clone the repo.
2. Install dev dependencies: `pip install -r requirements-dev.txt`.
3. Install pre-commit hooks: `pre-commit install`.

## Code Style

We use `ruff` for linting and formatting. Please ensure your code passes:

```bash
ruff check .
ruff format .
```

## Testing

Run tests before submitting a PR:

```bash
pytest tests/
```

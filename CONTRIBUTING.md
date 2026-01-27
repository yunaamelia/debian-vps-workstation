# Contributing to Debian VPS Workstation Configurator

First off, thanks for taking the time to contribute! 🎉

The following is a set of guidelines for contributing to this project. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report.

- **Check existing issues** to see if the bug has already been reported.
- **Use a clear and descriptive title** for the issue to identify the problem.
- **Describe the reproduction steps** in detail.
- **Include system details**: Run `vps-configurator --version` and include the output.

### Suggesting Enhancements

- **Use a clear and descriptive title**.
- **Provide a step-by-step description of the suggested enhancement**.
- **Explain why this enhancement would be useful**.

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/ahmadrizal7/debian-vps-workstation.git
   cd debian-vps-workstation
   ```

2. **Create a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install -e .
   ```

4. **Run tests**

   ```bash
   pytest tests/
   ```

## Style Guide

- We use **Blue** or **Black** for code formatting.
- We use **Ruff** for linting.
- We use **MyPy** for type checking.

Run linting before committing:

```bash
ruff check configurator/
mypy configurator/
```

## Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

## New Modules

See the [Module Development Guide](docs/developer-guide/module-development.md) for details on creating new configuration modules.

## Documentation

Documentation is built with MkDocs.

To build and serve locally:

```bash
mkdocs serve
```

## Community

- Join the discussion on [GitHub Discussions](https://github.com/ahmadrizal7/debian-vps-workstation/discussions).

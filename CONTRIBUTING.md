# Contributing to Debian VPS Workstation Configurator

Thank you for your interest in contributing! This document explains how to contribute to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Submitting Changes](#submitting-changes)
7. [Adding New Modules](#adding-new-modules)
8. [Code Style](#code-style)

---

## Code of Conduct

Be respectful and inclusive. We welcome contributors of all experience levels.

---

## Getting Started

### Types of Contributions

- **Bug fixes**: Found a bug? Fix it and submit a PR
- **Documentation**: Improve docs, add examples, fix typos
- **New modules**: Add support for new languages/tools
- **Features**: Add new functionality
- **Tests**: Improve test coverage

### Issues First

Before starting major work:

1. Check [existing issues](https://github.com/yunaamelia/debian-vps-workstation/issues)
2. Open an issue to discuss your idea
3. Wait for feedback before coding

---

## Development Setup

### Prerequisites

- Python 3.11+
- Git
- A Debian 13 VM/VPS for testing

### Clone and Setup

```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/debian-vps-configurator.git
cd debian-vps-configurator

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .

# Verify installation
python -m configurator --version
```

### IDE Setup

For VS Code:
1. Install Python extension
2. Select `.venv` as Python interpreter
3. Install recommended extensions

---

## Making Changes

### Create a Branch

```bash
# Update main
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/my-new-feature
```

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring
- `test/` - Test additions

### Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Examples:
```
feat(docker): add support for custom registries
fix(security): correct fail2ban jail configuration
docs(readme): add troubleshooting section
test(config): add validation tests
```

---

## Testing

### Running Tests

```bash
# All unit tests
pytest tests/unit/ -v

# Specific test file
pytest tests/unit/test_config.py -v

# With coverage
pytest tests/unit/ --cov=configurator --cov-report=html

# Integration tests (requires Debian 13)
pytest tests/integration/ -v --slow
```

### Writing Tests

- Add tests for all new functionality
- Place tests in appropriate directory:
  - `tests/unit/` - Unit tests (no external dependencies)
  - `tests/integration/` - Integration tests (may need real system)

Example test:

```python
import pytest
from configurator.config import ConfigManager

class TestMyFeature:
    def test_feature_works(self):
        config = ConfigManager()
        result = config.my_method()
        assert result == expected_value
```

### Test Markers

```python
@pytest.mark.slow          # Takes a long time
@pytest.mark.integration   # Needs real system
@pytest.mark.destructive   # Makes system changes
```

---

## Submitting Changes

### Before Submitting

1. Run all tests:
   ```bash
   pytest tests/unit/ -v
   ```

2. Check code style:
   ```bash
   black configurator/ tests/
   isort configurator/ tests/
   pylint configurator/
   mypy configurator/
   ```

3. Update documentation if needed

### Create Pull Request

1. Push your branch:
   ```bash
   git push origin feature/my-new-feature
   ```

2. Open PR on GitHub

3. Fill in the PR template:
   - Description of changes
   - Related issues
   - Testing done
   - Screenshots (if UI changes)

### PR Review

- Address review feedback
- Keep PRs focused and small
- Rebase if needed

---

## Adding New Modules

### Module Structure

Create a new file in `configurator/modules/`:

```python
"""
NewTool module description.

Handles:
- Feature 1
- Feature 2
"""

from configurator.modules.base import ConfigurationModule


class NewToolModule(ConfigurationModule):
    """NewTool installation module."""

    name = "NewTool"
    description = "Install and configure NewTool"
    priority = 55  # Execution order
    mandatory = False

    def validate(self) -> bool:
        """Check prerequisites."""
        # Check requirements
        return True

    def configure(self) -> bool:
        """Install and configure."""
        self.logger.info("Installing NewTool...")

        # Install packages
        self.install_packages(["newtool"])

        # Configure
        # ...

        return True

    def verify(self) -> bool:
        """Verify installation."""
        return self.command_exists("newtool")
```

### Register the Module

1. Add to `configurator/modules/__init__.py`:
   ```python
   from configurator.modules.newtool import NewToolModule
   ```

2. Add to `configurator/core/installer.py`:
   ```python
   MODULE_PRIORITY = {
       # ...
       "newtool": 55,
   }

   def _register_modules(self):
       from configurator.modules.newtool import NewToolModule
       self._module_registry["newtool"] = NewToolModule
   ```

3. Add configuration in `config/default.yaml`:
   ```yaml
   tools:
     newtool:
       enabled: false
   ```

4. Add tests in `tests/unit/test_newtool.py`

5. Document in `docs/configuration/overview.md`

---

## Code Style

### Python Style

- Follow PEP 8
- Use Black for formatting
- Use isort for imports
- Maximum line length: 88 characters

### Type Hints

Use type hints for all public functions:

```python
def my_function(name: str, count: int = 0) -> bool:
    """Do something.

    Args:
        name: The name to process
        count: Optional count

    Returns:
        True if successful
    """
    return True
```

### Docstrings

Use Google-style docstrings:

```python
def run_command(cmd: str, timeout: int = 30) -> CommandResult:
    """Run a shell command.

    Args:
        cmd: Command to execute
        timeout: Timeout in seconds

    Returns:
        CommandResult with return code and output

    Raises:
        ModuleExecutionError: If command fails
    """
```

### Error Messages

Follow the beginner-friendly pattern:

```python
raise ModuleExecutionError(
    what="Failed to install Docker",
    why="Package repository is not available",
    how="Check your internet connection and try again",
    docs_link="https://docs.docker.com/install/",
)
```

---

## Questions?

- Open a [discussion](https://github.com/yunaamelia/debian-vps-workstation/discussions)
- Join the community chat
- Ask in your pull request

Thank you for contributing! 🎉

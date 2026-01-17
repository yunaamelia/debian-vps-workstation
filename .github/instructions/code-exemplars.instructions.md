---
description: "Code exemplar-based instructions for maintaining consistency with established best practices in the Debian VPS Configurator project"
applyTo: "**/*.py"
---

# Code Exemplars Instructions

## Overview

This instruction file is based on the code exemplars documented in `/docs/exemplars.md`. These exemplars represent the highest quality code in our codebase and serve as templates for all new development. You MUST follow the patterns, principles, and conventions demonstrated in these exemplars.

## Core Principles

When generating or reviewing code for this project, you MUST adhere to these fundamental principles:

### 1. Module Design Principles

**Template Method Pattern**

- You WILL use `ConfigurationModule` as the base class for all feature modules
- You MUST implement the three core lifecycle methods: `validate()`, `configure()`, `verify()`
- You WILL use the abstract base class pattern to define required interfaces
- You MUST accept optional dependencies via constructor with sensible defaults

**Example Structure:**

```python
from configurator.modules.base import ConfigurationModule

class MyModule(ConfigurationModule):
    """Brief description of what this module configures."""

    def __init__(self, config_manager=None, logger=None, dry_run=False):
        """Initialize with optional dependencies."""
        super().__init__(config_manager, logger, dry_run)
        # Additional initialization

    def validate(self) -> bool:
        """Validate prerequisites before configuration."""
        # Validation logic
        return True

    def configure(self) -> None:
        """Execute the configuration steps."""
        # Configuration logic

    def verify(self) -> bool:
        """Verify the configuration was successful."""
        # Verification logic
        return True
```

### 2. Dependency Injection

**Container-Based DI**

- You WILL use the `Container` class from `configurator.core.container` for service management
- You MUST register services as singletons, factories, or mocks as appropriate
- You WILL accept dependencies via constructor parameters, not global imports
- You MUST provide default implementations for optional dependencies

**Anti-Pattern to AVOID:**

```python
# BAD: Direct import of other modules
from configurator.modules.network import NetworkModule
network = NetworkModule()
```

**Correct Pattern:**

```python
# GOOD: Dependency injection via constructor
def __init__(self, network_module=None):
    self.network = network_module or get_dependency('network')
```

### 3. Exception Handling

**User-Centric Error Messages**

- You MUST use custom exceptions from `configurator.exceptions`
- You WILL follow the WHAT/WHY/HOW format for all error messages:
  - **WHAT**: Describe what went wrong
  - **WHY**: Explain why it's a problem
  - **HOW**: Provide actionable steps to fix it
- You MUST include ASCII art formatting for visibility
- You WILL provide optional documentation links when available

**Example:**

```python
from configurator.exceptions import ConfiguratorError

class MyModuleError(ConfiguratorError):
    """Raised when MyModule encounters a specific error."""

    def __init__(self, detail: str):
        message = f"""
╔═══════════════════════════════════════════════════════════════╗
║                    MY MODULE ERROR                             ║
╚═══════════════════════════════════════════════════════════════╝

WHAT: {detail}
WHY:  This prevents the module from completing configuration
HOW:  Check the configuration file and ensure all required fields are set

Docs: https://docs.example.com/mymodule
"""
        super().__init__(message)
```

### 4. Resilience Patterns

**Circuit Breaker Pattern**

- You WILL use `CircuitBreaker` from `configurator.utils.circuit_breaker` for external service calls
- You MUST implement proper state transitions (CLOSED → OPEN → HALF_OPEN)
- You WILL configure appropriate failure thresholds and timeout periods
- You MUST provide meaningful error messages when circuits are open

**Retry Pattern**

- You WILL use the `@retry` decorator from `configurator.utils.retry` for transient failures
- You MUST configure exponential backoff with jitter to prevent thundering herd
- You WILL catch specific exceptions, not bare `except:` clauses
- You MUST log retry attempts with context

**Example:**

```python
from configurator.utils.retry import retry
from configurator.utils.circuit_breaker import CircuitBreaker

class MyService:
    def __init__(self):
        self.circuit = CircuitBreaker(
            failure_threshold=3,
            timeout=60,
            name="my_service"
        )

    @retry(max_retries=3, backoff_base=2.0, exceptions=(NetworkError,))
    def call_external_api(self):
        """Call external API with retry and circuit breaker."""
        with self.circuit:
            # API call logic
            pass
```

### 5. Rollback Management

**Command Pattern for Rollback**

- You MUST use `RollbackManager` from `configurator.core.rollback` for all state changes
- You WILL register rollback actions BEFORE executing changes
- You MUST support all action types: commands, files, packages, services
- You WILL execute rollbacks in reverse order (LIFO)

**Example:**

```python
from configurator.core.rollback import RollbackManager, RollbackAction

class MyModule(ConfigurationModule):
    def configure(self):
        rollback = RollbackManager()

        # Register rollback before making change
        rollback.add_action(RollbackAction(
            type="file",
            description="Restore original config",
            command=f"cp /backup/config /etc/config"
        ))

        # Make the actual change
        self.run("cp /etc/config /backup/config")
        self.run("echo 'new config' > /etc/config")
```

### 6. Configuration Management

**Layered Configuration**

- You WILL use `ConfigManager` from `configurator.config` for all configuration access
- You MUST support configuration layering: Defaults → Profile → User → CLI
- You WILL use dot notation for nested access: `config.get("system.hostname")`
- You MUST validate configuration using Pydantic schemas

**Example:**

```python
from configurator.config import ConfigManager

class MyModule(ConfigurationModule):
    def validate(self):
        # Access configuration with defaults
        timeout = self.config.get("mymodule.timeout", default=30)
        enabled = self.config.get("mymodule.enabled", default=True)

        if not enabled:
            self.logger.info("MyModule is disabled in configuration")
            return False

        return True
```

### 7. Input Validation and Security

**Defense in Depth**

- You MUST use `InputValidator` from `configurator.security.input_validator` for all user input
- You WILL validate usernames, paths, commands, emails, IPs, and domains
- You MUST sanitize input before using in shell commands or file operations
- You WILL use strict mode to raise exceptions on invalid input

**Example:**

```python
from configurator.security.input_validator import InputValidator

validator = InputValidator(strict=True)

# Validate before use
username = validator.validate_username(user_input)
path = validator.validate_path(file_path, must_exist=False)
email = validator.validate_email(email_input)

# Sanitize for shell commands
safe_command = validator.sanitize_command(command_input)
```

### 8. Logging and User Feedback

**User-Visible Progress**

- You WILL use structured logging with appropriate levels (DEBUG, INFO, WARNING, ERROR)
- You MUST provide clear progress messages with visual indicators (✓, ✗, →)
- You WILL log security events and validation failures
- You MUST use consistent formatting across all modules

**Example:**

```python
class MyModule(ConfigurationModule):
    def configure(self):
        self.logger.info("→ Starting MyModule configuration...")

        try:
            self._step_one()
            self.logger.info("✓ Step 1 completed successfully")

            self._step_two()
            self.logger.info("✓ Step 2 completed successfully")

        except Exception as e:
            self.logger.error(f"✗ Configuration failed: {e}")
            raise
```

### 9. Testing Standards

**Test Structure**

- You MUST write unit tests for all new functionality
- You WILL use pytest fixtures from `tests/conftest.py` for common setup
- You MUST follow Arrange-Act-Assert pattern in all tests
- You WILL use descriptive test names that explain expected behavior

**Test Isolation**

- You MUST use `tmp_path` fixture for file operations in tests
- You WILL mock external dependencies using `monkeypatch` or `mock_run_command`
- You MUST restore state after each test (use `autouse` fixtures when needed)
- You WILL mark integration tests with `@pytest.mark.integration`

**Example:**

```python
import pytest
from configurator.modules.mymodule import MyModule

class TestMyModule:
    """Tests for MyModule."""

    def test_validate_returns_true_when_prerequisites_met(self, mock_run_command):
        """Validation should succeed when all prerequisites are met."""
        # Arrange
        mock_run_command.return_value = (0, "success", "")
        module = MyModule(dry_run=True)

        # Act
        result = module.validate()

        # Assert
        assert result is True

    def test_configure_raises_error_when_command_fails(self, mock_run_command):
        """Configuration should raise error when command fails."""
        # Arrange
        mock_run_command.return_value = (1, "", "error")
        module = MyModule(dry_run=False)

        # Act & Assert
        with pytest.raises(ConfiguratorError):
            module.configure()
```

## Implementation Checklist

When implementing a new module or feature, you MUST verify:

- [ ] Inherits from `ConfigurationModule` base class
- [ ] Implements `validate()`, `configure()`, `verify()` methods
- [ ] Accepts dependencies via constructor with defaults
- [ ] Uses custom exceptions with WHAT/WHY/HOW format
- [ ] Registers rollback actions before state changes
- [ ] Uses `InputValidator` for all user input
- [ ] Uses `@retry` decorator for transient failures
- [ ] Uses `CircuitBreaker` for external service calls
- [ ] Provides clear user-visible progress messages
- [ ] Includes comprehensive unit tests
- [ ] Follows Arrange-Act-Assert pattern in tests
- [ ] Uses appropriate pytest fixtures for isolation
- [ ] Documents public methods with docstrings
- [ ] Validates configuration using schemas
- [ ] Logs security events appropriately

## Anti-Patterns to AVOID

You MUST NOT:

- ❌ Import other modules directly (use dependency injection)
- ❌ Use bare `except:` clauses (catch specific exceptions)
- ❌ Hardcode values (use configuration system)
- ❌ Execute system calls without rollback registration
- ❌ Use global mutable state (use DI container)
- ❌ Create generic error messages (follow WHAT/WHY/HOW format)
- ❌ Skip input validation for user-provided data
- ❌ Use synchronous retries without backoff
- ❌ Ignore test isolation (each test must be independent)
- ❌ Write tests that depend on execution order

## Code Quality Standards

### Documentation

- You WILL write module-level docstrings explaining purpose
- You MUST document all public methods with docstrings
- You WILL include parameter types and return types in docstrings
- You MUST provide usage examples for complex functionality

### Type Hints

- You WILL use type hints for all function parameters
- You MUST specify return types for all functions
- You WILL use `Optional[T]` for nullable parameters
- You MUST use `Union[T1, T2]` for multiple possible types

### Code Organization

- You WILL keep methods focused on a single responsibility
- You MUST use private methods (prefix with `_`) for internal logic
- You WILL organize imports: stdlib → third-party → local
- You MUST keep line length under 100 characters

### Error Handling

- You WILL catch specific exceptions, not `Exception`
- You MUST provide context in exception messages
- You WILL log errors before raising them
- You MUST clean up resources in `finally` blocks or context managers

## Security Considerations

When implementing security-sensitive features, you MUST:

- Validate ALL user input using `InputValidator`
- Use parameterized commands to prevent injection attacks
- Verify GPG signatures for package installations
- Log security events with appropriate severity
- Follow principle of least privilege
- Sanitize data before logging (no passwords or secrets)
- Use secure defaults in configuration
- Implement rate limiting for authentication attempts

## Performance Guidelines

- You WILL use lazy loading for expensive resources
- You MUST implement caching for frequently accessed data
- You WILL use generators for large datasets
- You MUST clean up resources promptly (use context managers)
- You WILL parallelize independent operations when possible
- You MUST implement timeouts for network operations

## Maintenance Guidelines

### Adding New Exemplars

When you identify code that should be an exemplar:

1. Verify it demonstrates clear best practices
2. Ensure it's well-documented and tested
3. Add it to `/docs/exemplars.md` with explanation
4. Update this instruction file if new patterns are introduced

### Refactoring Existing Code

When refactoring to match exemplars:

1. Start with comprehensive tests
2. Refactor incrementally, not all at once
3. Verify tests pass after each change
4. Update documentation to reflect changes
5. Add rollback capability if missing

## Conclusion

These instructions are derived from proven, production-quality code in our codebase. Following these patterns ensures consistency, maintainability, and reliability. When in doubt, refer to the exemplars in `/docs/exemplars.md` for concrete examples.

**Remember:** Code quality is not negotiable. Every commit should maintain or improve the quality standard set by our exemplars.

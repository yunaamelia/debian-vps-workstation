---
trigger: always_on
glob: "**/*.py"
description: "Guidelines for using the project's technology stack (CLI, Config, Validation)."
---

You are a technology specialist for this project. You implement features using the established framework patterns, avoiding raw or deprecated approaches.

# Technology Stack Usage

1. **CLI Framework (Click)**
    - Use decorators: `@cli.command()`, `@option()`
    - Provide help text for EVERYTHING.
    - Handle exceptions at the command boundary: `try...except ConfiguratorError`.

2. **Configuration**
    - Access config ONLY via `ConfigManager` dot notation (`system.hostname`).
    - Always provide defaults: `config.get("key", default=None)`.
    - Never read YAML files directly in feature code.

3. **Validation (Pydantic)**
    - Use Pydantic models for data schemas.
    - Return structured `ValidationResult` objects, not bare booleans/exceptions for logic checks.
    - Validate early (at boundaries).

4. **Console Output (Rich)**
    - Use `Console` for all output.
    - Use semantic tags: `[green]Success[/green]`, `[red]Error[/red]`.
    - Example: `console.print("[green]✓ Installed[/green]")`

5. **Cryptography**
    - Use `cryptography` library high-level APIs.
    - Never store plaintext secrets.
    - Use `secrets` module for token generation.

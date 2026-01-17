---
trigger: always_on
glob: "**/*.py"
description: "Python coding standards, typing, and documentation requirements."
---

You are a code quality enforcer. You ensure all Python code meets the project's strict style and documentation standards.

# Code Style Rules

1.  **Modern Python**:
    - Use Python 3.11+ features (typing, dataclasses, match/case).
    - Follow PEP 8 (max line length 79/88).

2.  **Type Hinting**:
    - **Mandatory**: All function signatures (args and return).
    - Use `Optional[T]` or `T | None`.
    - Use generic aliases (`list[str]`, `dict[str, Any]`).

3.  **Documentation**:
    - **Public APIs**: Require docstrings (Module, Class, Method).
    - **Structure**:
      - Description
      - Args/Returns (PEP 257)
      - Raises (if applicable)

4.  **Import Sorting**:
    - Block 1: Standard Lib (`os`, `sys`)
    - Block 2: Third Party (`click`, `rich`)
    - Block 3: Local (`configurator.core`)

5.  **Composition Pattern**:
    - Prefer Dependency Injection over Inheritance.
    - Keep inheritance hierarchies flat (max 1-2 levels).

6.  **Explicit Failure**:
    - Don't return `False`/`None` for errors. Raise specific exceptions.
    - Validate inputs at the start of functions.

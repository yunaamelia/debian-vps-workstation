---
trigger: always_on
glob: "**/*"
description: "Strict naming conventions for files, classes, functions, and variables."
---

You are a code consistency expert. You enforce strict naming conventions to ensure readability and predictability across the codebase.

# Naming Rules

1.  **Files**: Use `snake_case.py` for Python and `kebab-case.md` for documentation.
    - Correct: `circuit_breaker.py`, `user-guide.md`
    - Incorrect: `CircuitBreaker.py`, `User_Guide.md`

2.  **Classes**: Use `PascalCase`.
    - **Modules**: Must end in `Module` (e.g., `DockerModule`)
    - **Managers**: Must end in `Manager` (e.g., `RollbackManager`)
    - **Validators**: Must end in `Validator` (e.g., `SystemValidator`)
    - **Exceptions**: Must end in `Error` (e.g., `ConfiguratorError`)

3.  **Functions & Methods**: Use `snake_case`.
    - Public: `install_packages()`
    - Private: `_internal_logic()`
    - Tests: `test_<scenario>_<expected>()`

4.  **Variables**: Use `snake_case`.
    - Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`)

5.  **Directories**: Use `snake_case`.
    - Correct: `tier1_critical`
    - Incorrect: `Tier1Critical`

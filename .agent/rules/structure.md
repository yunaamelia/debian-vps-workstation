---
trigger: always_on
glob: "**/*"
description: "Permanent architectural rules for folder structure, file placement, and naming conventions."
---

You are the guardian of the project's structural integrity. Your goal is to ensure all files are placed correctly and the directory structure remains clean and predictable.

# Core Structural Rules

1.  **Maintain Root Structure**: Do not create new top-level directories.
    - `configurator/`: Main package
    - `tests/`: Test suite (must mirror source)
    - `config/`: YAML configuration only
    - `docs/`: Documentation

2.  **Package Layering**: Organize `configurator/` by layer:
    - `cli.py`, `wizard.py`: Presentation
    - `core/`: Orchestration
    - `modules/`: Features
    - `security/`, `validators/`, `utils/`: Foundation

3.  **Test Mirroring**: Tests must strictly mirror the source tree.
    - Source: `configurator/modules/docker.py`
    - Test: `tests/unit/test_docker.py`

4.  **File Placement**:
    - **Models**: `configurator/config_schema.py`
    - **Exceptions**: `configurator/exceptions.py`
    - **Constants**: Near usage or `configurator/utils/constants.py`

5.  **Configuration**:
    - NEVER hardcode config. Use `config/default.yaml`.

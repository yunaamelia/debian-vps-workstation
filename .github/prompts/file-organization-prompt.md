# Repository File Organization Prompt

**Purpose:** Organize and structure files in the debian-vps-workstation repository to maintain consistency, clarity, and adherence to established architectural patterns.

**Target:** Python 3.12+ CLI Application with Modular Plugin Architecture
**Project:** Debian VPS Configurator v2.0

---

## Core Directives

You WILL organize files in this repository following the established modular plugin architecture and layered structure.
You MUST maintain strict layer boundaries and dependency rules during reorganization.
You WILL ALWAYS validate that file moves preserve import statements and module relationships.
You WILL NEVER introduce circular dependencies when reorganizing code.
CRITICAL: You MUST ensure all file paths in documentation are updated after file movements.

---

## Requirements

<!-- <requirements> -->

### Repository Structure Requirements

#### Layer-Based Organization (Vertical)

You MUST organize files according to these architectural layers:

1. **Presentation Layer** - User interaction components

   - Location: `configurator/cli.py`, `configurator/wizard.py`, `configurator/cli_monitoring.py`
   - Purpose: Command-line interface, TUI wizards, CLI commands
   - Files: CLI entry points, command definitions, user prompts

2. **Orchestration Layer** - Core coordination logic

   - Location: `configurator/core/`
   - Purpose: Module execution, dependency resolution, service coordination
   - Files: installer.py, container.py, parallel.py, rollback.py, hooks.py
   - CRITICAL: This layer CANNOT import from `configurator/modules/`

3. **Module Layer** - Feature implementations

   - Location: `configurator/modules/`
   - Purpose: Independent, self-contained feature modules
   - Files: docker.py, git.py, python.py, nodejs.py, etc. (24 modules)
   - CRITICAL: Modules CANNOT import other modules directly

4. **Foundation Layer** - Shared utilities and services
   - Location: `configurator/utils/`, `configurator/security/`, `configurator/rbac/`
   - Purpose: Reusable components, security, validation, utilities
   - Files: Helpers, validators, security services, access control

#### Domain-Based Organization (Horizontal)

You MUST organize files according to these domain boundaries:

- **Security Domain**: `configurator/security/` (20 files)

  - File categories: Input validation, supply chain, secrets management, encryption
  - Naming pattern: `<function>_<domain>.py` (e.g., `input_validator.py`, `supply_chain.py`)

- **RBAC Domain**: `configurator/rbac/` (5 files)

  - File categories: Role definitions, permission checks, policy enforcement
  - Naming pattern: `<component>.py` (e.g., `roles.py`, `permissions.py`)

- **User Management**: `configurator/users/` (5 files)

  - File categories: User creation, team management, registries
  - Naming pattern: `<entity>_<action>.py` (e.g., `user_manager.py`, `team_registry.py`)

- **Observability**: `configurator/observability/`
  - File categories: Metrics, alerting, monitoring, logging
  - Naming pattern: `<function>.py` (e.g., `metrics.py`, `alerting.py`)

#### Feature-Based Modules (Plugins)

You MUST ensure each module follows this self-contained pattern:

- **Location**: `configurator/modules/<module_name>.py`
- **Pattern**: Single file per module (exceptions: multi-file modules like `xrdp_xfce_zsh/`)
- **Naming**: `<feature_name>.py` (e.g., `docker.py`, `python.py`, `nodejs.py`)
- **Structure**: Inherits from `ConfigurationModule` base class
- **Dependencies**: Uses dependency injection, no direct imports of other modules

### File Naming Conventions Requirements

#### Python Files

You WILL follow these naming patterns:

- **Module files**: `snake_case.py` (e.g., `docker.py`, `parallel.py`)
- **Class names**: `PascalCase` (e.g., `ConfigurationModule`, `DockerModule`)
- **Function/method names**: `snake_case` (e.g., `install_packages_resilient`, `validate_username`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `_APT_LOCK`, `ROLLBACK_STATE_FILE`)
- **Private functions/methods**: Leading underscore `_function_name`
- **Protected attributes**: Leading underscore `_attribute_name`
- **Dunder methods**: Double underscore both sides `__init__`, `__str__`

#### Configuration Files

You WILL organize configuration files as:

- **Base config**: `config/default.yaml`
- **Profiles**: `config/profiles/<profile_name>.yaml` (beginner.yaml, intermediate.yaml, advanced.yaml)
- **Schemas**: `configurator/config_schema.py`

#### Documentation Files

You WILL organize documentation as:

- **Root level**: High-level guides (README.md, CONTRIBUTING.md, LICENSE)
- **Blueprint files**: Root level `*_Blueprint.md` files
- **Detailed docs**: `docs/<category>/<topic>.md`
- **API reference**: `docs/api-reference/<module>.md`
- **Guides**: `docs/<type>-guide/<topic>.md` (e.g., `developer-guide/`, `user-guide/`)

#### Test Files

You WILL organize test files as:

- **Unit tests**: `tests/unit/test_<module>.py`
- **Integration tests**: `tests/integration/test_<feature>_integration.py`
- **Validation tests**: `tests/validation/test_<validation_type>.py`
- **Fixtures**: `tests/conftest.py` (shared fixtures)
- **Test naming**: `test_<what_it_tests>` (methods), `Test<ClassName>` (classes)

#### Script Files

You WILL organize scripts as:

- **Location**: `scripts/<purpose>/`
- **Naming**: `<action>_<target>.sh` or `<action>_<target>.py`
- **Entry point**: `quick-install.sh` at root level
- **Build scripts**: `scripts/build/`
- **Deployment scripts**: `scripts/deployment/`
- **Utility scripts**: `scripts/utils/`

### Import Organization Requirements

You MUST organize imports in this exact order:

```python
# 1. Standard library imports
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

# 2. Third-party imports
import click
from rich.console import Console

# 3. Local imports (absolute)
from configurator.core.installer import Installer
from configurator.exceptions import ModuleExecutionError

# 4. Local imports (relative - within same package only)
from .base import ConfigurationModule
from ..utils.command import run_command
```

### File Size and Structure Requirements

You WILL maintain these file size guidelines:

- **Maximum function length**: ~50 lines
- **Maximum class length**: ~700 lines (base.py is 662 lines)
- **Recommended module size**: 200-500 lines
- **If exceeding 700 lines**: Consider splitting into multiple modules or files

You WILL structure large files as:

```python
"""
Module docstring explaining purpose.

Detailed description if needed.
"""

# 1. Imports (organized by category)

# 2. Module-level constants
CONSTANT_NAME = value

# 3. Module-level variables
module_variable = value

# 4. Main classes (ordered by importance/dependency)
class MainClass:
    pass

class HelperClass:
    pass

# 5. Module-level functions (if any)
def utility_function():
    pass

# 6. Entry point (if executable)
if __name__ == "__main__":
    main()
```

### Directory Structure Requirements

You MUST maintain this directory hierarchy:

```
debian-vps-workstation/
├── .github/                    # GitHub-specific files
│   ├── copilot-instructions.md
│   ├── prompts/                # AI prompt templates
│   └── skills/                 # AI agent skills
│
├── config/                     # Configuration files
│   ├── default.yaml
│   └── profiles/
│
├── configurator/               # Main package (104 files)
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── wizard.py
│   ├── config.py
│   ├── core/                   # Orchestration layer
│   ├── modules/                # Feature modules
│   ├── security/               # Security subsystem
│   ├── rbac/                   # Access control
│   ├── users/                  # User management
│   ├── utils/                  # Utilities
│   ├── observability/          # Monitoring
│   └── plugins/                # Plugin system
│
├── docs/                       # Documentation
│   ├── index.md
│   ├── <category>/
│   └── api-reference/
│
├── tests/                      # Test files
│   ├── unit/
│   ├── integration/
│   ├── validation/
│   └── conftest.py
│
├── scripts/                    # Utility scripts
│   ├── build/
│   ├── deployment/
│   └── utils/
│
├── tools/                      # Development tools
│
└── [Root-level files]          # Configuration, documentation

```

<!-- </requirements> -->

---

## File Organization Process

<!-- <process> -->

### 1. Analysis Phase

You WILL analyze files and identify organization issues:

1. **Scan current structure**: Use `list_dir`, `file_search`, `semantic_search`
2. **Identify misplaced files**: Files not following layer/domain boundaries
3. **Detect naming violations**: Files not following naming conventions
4. **Find size violations**: Files exceeding recommended size limits
5. **Check import patterns**: Validate no circular dependencies exist

### 2. Planning Phase

You WILL create a reorganization plan:

1. **List files to move**: Specify source and destination paths
2. **Identify refactoring needed**: Large files to split, imports to update
3. **Document breaking changes**: Track changes that affect imports
4. **Create migration checklist**: Ensure nothing is missed
5. **Validate layer boundaries**: Ensure moves don't violate architecture

### 3. Execution Phase

You WILL perform file organization operations:

1. **Create necessary directories**: Use `create_directory` for new folders
2. **Move files**: Use `run_in_terminal` with `git mv` to preserve history
3. **Update imports**: Use `multi_replace_string_in_file` to fix import paths
4. **Split large files**: Extract classes/functions to new files
5. **Update documentation**: Fix file path references in docs

### 4. Validation Phase

You WILL validate the reorganization:

1. **Run linting**: Execute `ruff check configurator/` to validate structure
2. **Run type checking**: Execute `mypy configurator/` to check imports
3. **Run tests**: Execute `pytest tests/` to ensure nothing broke
4. **Check documentation**: Verify all file paths in docs are correct
5. **Validate imports**: Ensure no circular dependencies introduced

### 5. Documentation Phase

You WILL document the changes:

1. **Update Project_Folders_Structure_Blueprint.md**: Reflect new structure
2. **Update import paths in docs**: Fix references in documentation
3. **Update CHANGELOG.md**: Document structural changes
4. **Create migration guide**: If changes affect users/developers
5. **Update .github/copilot-instructions.md**: Reflect new file locations

<!-- </process> -->

---

## Common Organization Patterns

<!-- <patterns> -->

### Pattern 1: Moving Misplaced Module Files

**Scenario**: A module file is in the wrong directory

**Process**:

```bash
# 1. Use git mv to preserve history
git mv configurator/wrong_location/module.py configurator/modules/module.py

# 2. Update imports in all files
# From: from configurator.wrong_location.module import Module
# To:   from configurator.modules.module import Module

# 3. Update container.py registration
# Verify module is registered in dependency injection container

# 4. Run tests
pytest tests/unit/test_module.py
```

### Pattern 2: Splitting Large Files

**Scenario**: A file exceeds 700 lines and should be split

**Process**:

```python
# Original: configurator/core/large_module.py (1000 lines)

# Split into:
# - configurator/core/large_module.py (main class, 400 lines)
# - configurator/core/large_module_helpers.py (helper functions, 300 lines)
# - configurator/core/large_module_types.py (type definitions, 300 lines)

# Update imports:
# In large_module.py:
from .large_module_helpers import helper_function
from .large_module_types import CustomType
```

### Pattern 3: Organizing Test Files

**Scenario**: Test files are disorganized or misnamed

**Process**:

```
# Correct structure:
tests/
├── unit/
│   ├── test_config.py              # Tests for configurator/config.py
│   ├── test_docker.py              # Tests for configurator/modules/docker.py
│   └── test_rollback.py            # Tests for configurator/core/rollback.py
│
├── integration/
│   ├── test_docker_integration.py  # Integration tests for Docker module
│   └── test_parallel_execution.py  # Integration tests for parallel execution
│
└── validation/
    ├── test_system_validation.py   # System validation tests
    └── test_module_validation.py   # Module validation tests
```

### Pattern 4: Organizing Documentation

**Scenario**: Documentation files are scattered or poorly organized

**Process**:

```
docs/
├── index.md                        # Main documentation entry
├── installation/
│   ├── quick-start.md              # Quick installation guide
│   └── advanced.md                 # Advanced installation
├── user-guide/
│   ├── getting-started.md          # Getting started guide
│   └── configuration.md            # Configuration guide
├── developer-guide/
│   ├── architecture.md             # Architecture overview
│   ├── module-development.md       # Module development guide
│   └── testing.md                  # Testing guide
└── api-reference/
    ├── core.md                     # Core API reference
    └── modules.md                  # Modules API reference
```

### Pattern 5: Cleaning Up Generated Files

**Scenario**: Generated files, cache, or temporary files should be removed/organized

**Process**:

```bash
# 1. Ensure .gitignore includes generated directories
# .gitignore should have:
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
dist/
*.egg-info/
.coverage
venv/

# 2. Clean up generated files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/

# 3. Remove from git if accidentally committed
git rm -r --cached configurator/__pycache__
```

<!-- </patterns> -->

---

## Organization Best Practices

<!-- <best-practices> -->

### File Placement Rules

1. **Layer Boundary Enforcement**

   - You MUST place files in the correct architectural layer
   - You WILL NEVER create imports that violate layer dependencies
   - Core layer CANNOT import from modules layer
   - Modules CANNOT import other modules directly

2. **Domain Cohesion**

   - You WILL group related files in domain-specific directories
   - Security files stay in `configurator/security/`
   - RBAC files stay in `configurator/rbac/`
   - User management files stay in `configurator/users/`

3. **Single Responsibility**

   - You WILL ensure each file has ONE clear purpose
   - If a file does multiple things, split it
   - Example: Don't combine user creation and team management in one file

4. **Discoverability**
   - You WILL use descriptive, searchable file names
   - Avoid abbreviations unless widely understood (e.g., `rbac`, `ssh`)
   - Group related files with common prefixes (e.g., `supply_chain_*.py`)

### Import Management Rules

1. **Import Path Consistency**

   - You WILL use absolute imports from package root
   - You WILL use relative imports only within same package
   - Never mix absolute and relative for same module

2. **Import Order**

   - You MUST follow: stdlib → third-party → local
   - You WILL alphabetize within each category
   - You WILL use `ruff` to enforce import order

3. **Circular Dependency Prevention**
   - You WILL NEVER create circular imports
   - If needed, use dependency injection instead
   - Move shared code to a lower layer or utility module

### Documentation Update Rules

1. **File Path References**

   - You MUST update ALL documentation when moving files
   - Search for old file paths in `docs/` and update
   - Update code examples to use new import paths

2. **Blueprint Updates**

   - You WILL update `Project_Folders_Structure_Blueprint.md`
   - Update any architecture diagrams
   - Reflect changes in `Project_Architecture_Blueprint.md`

3. **Changelog Maintenance**
   - You WILL document structural changes in `CHANGELOG.md`
   - Specify which files were moved and why
   - Include migration notes if needed

### Git Best Practices

1. **Preserve File History**

   - You WILL ALWAYS use `git mv` instead of manual move + add
   - Preserves blame history and makes tracking easier
   - Example: `git mv old/path.py new/path.py`

2. **Atomic Commits**

   - You WILL commit file moves separately from code changes
   - Commit 1: Move files with `git mv`
   - Commit 2: Update imports
   - Commit 3: Update documentation

3. **Clear Commit Messages**
   - Use: "refactor: move <file> to <location> for <reason>"
   - Example: "refactor: move docker.py to modules/ for layer consistency"

<!-- </best-practices> -->

---

## Quality Standards

<!-- <quality-standards> -->

### Organization Quality Metrics

You WILL achieve these quality standards:

1. **Layer Compliance**: 100% of files in correct architectural layer
2. **Naming Compliance**: 100% of files follow naming conventions
3. **Import Validity**: Zero circular dependencies
4. **Size Compliance**: <5% of files exceed size recommendations
5. **Documentation Accuracy**: 100% of file paths correct in docs
6. **Test Mapping**: 1:1 mapping between source files and test files (unit tests)

### Validation Checklist

After reorganization, you MUST verify:

- [ ] All files are in their correct layer directories
- [ ] All file names follow snake_case convention
- [ ] All class names follow PascalCase convention
- [ ] All imports are organized (stdlib → third-party → local)
- [ ] No circular dependencies exist
- [ ] All tests pass (`pytest tests/`)
- [ ] Linting passes (`ruff check configurator/`)
- [ ] Type checking passes (`mypy configurator/`)
- [ ] Documentation paths are updated
- [ ] CHANGELOG.md is updated
- [ ] Project_Folders_Structure_Blueprint.md is updated

### Common Organization Issues to Fix

You WILL identify and fix these common problems:

1. **Misplaced Files**

   - Utility code in module layer → Move to `configurator/utils/`
   - Module code in core layer → Move to `configurator/modules/`
   - Test code outside tests/ → Move to appropriate test directory

2. **Naming Violations**

   - CamelCase file names → Convert to snake_case
   - Unclear names → Rename to descriptive names
   - Inconsistent prefixes → Standardize naming patterns

3. **Import Issues**

   - Circular imports → Refactor using dependency injection
   - Absolute imports to same package → Use relative imports
   - Unorganized imports → Reorder according to convention

4. **Size Violations**

   - Files >700 lines → Split into multiple files
   - Functions >50 lines → Extract helper functions
   - Classes with too many methods → Consider composition

5. **Documentation Drift**
   - Outdated file paths in docs → Update all references
   - Missing API documentation → Add docstrings
   - Broken links → Fix or remove

<!-- </quality-standards> -->

---

## Prohibited Patterns

<!-- <prohibited> -->

### NEVER Do These

You WILL NEVER:

1. **Break Layer Boundaries**

   - ❌ Import from modules/ in core/
   - ❌ Direct imports between modules
   - ❌ Circular dependencies

2. **Violate Naming Conventions**

   - ❌ CamelCase file names (e.g., `DockerModule.py`)
   - ❌ Mixed case (e.g., `Docker_Module.py`)
   - ❌ Unclear abbreviations (e.g., `dm.py`)

3. **Create Disorganization**

   - ❌ Put unrelated files in same directory
   - ❌ Mix test files with source files
   - ❌ Leave generated files in repository

4. **Move Files Without Updating**

   - ❌ Move file without updating imports
   - ❌ Move file without updating documentation
   - ❌ Move file without updating tests

5. **Ignore Git Best Practices**
   - ❌ Use `mv` instead of `git mv`
   - ❌ Combine moves and changes in one commit
   - ❌ Skip commit messages or use vague ones

<!-- </prohibited> -->

---

## Example Reorganization Scenarios

<!-- <scenarios> -->

### Scenario 1: Organizing a New Feature Module

**Task**: A new feature module `kubernetes.py` was added but placed incorrectly

**Current**: `configurator/kubernetes.py`
**Expected**: `configurator/modules/kubernetes.py`

**Steps**:

```bash
# 1. Move file to correct location
git mv configurator/kubernetes.py configurator/modules/kubernetes.py

# 2. Update imports in container.py
# Add to module registry in configurator/core/container.py

# 3. Create corresponding test file
touch tests/unit/test_kubernetes.py

# 4. Update documentation
# Add entry to docs/modules/kubernetes.md

# 5. Validate
pytest tests/unit/test_kubernetes.py
ruff check configurator/modules/kubernetes.py
mypy configurator/modules/kubernetes.py
```

### Scenario 2: Splitting a Large Module

**Task**: `configurator/core/installer.py` is 1200 lines and should be split

**Current**: `configurator/core/installer.py` (1200 lines)

**Target Structure**:

```
configurator/core/
├── installer.py              # Main installer class (500 lines)
├── installer_validation.py   # Validation logic (300 lines)
├── installer_execution.py    # Execution logic (400 lines)
```

**Steps**:

```python
# 1. Extract validation methods
# Create configurator/core/installer_validation.py
# Move all validation-related methods

# 2. Extract execution methods
# Create configurator/core/installer_execution.py
# Move all execution-related methods

# 3. Update installer.py imports
from .installer_validation import validate_system, validate_modules
from .installer_execution import execute_parallel, execute_sequential

# 4. Update all tests to import from new locations

# 5. Run full test suite
pytest tests/
```

### Scenario 3: Organizing Scattered Documentation

**Task**: Documentation files are scattered in multiple locations

**Current**:

```
/home/racoon/Desktop/debian-vps-workstation/
├── README.md
├── docs/ARCHITECTURE.md
├── docs/CLI-REFERENCE.md
├── configurator/modules/README.md  # Misplaced
├── tests/TESTING.md  # Misplaced
```

**Target**:

```
docs/
├── index.md                        # Main entry (link to README.md)
├── architecture.md                 # From docs/ARCHITECTURE.md
├── cli-reference.md                # From docs/CLI-REFERENCE.md
├── developer-guide/
│   ├── module-development.md       # From configurator/modules/README.md
│   └── testing.md                  # From tests/TESTING.md
```

**Steps**:

```bash
# 1. Standardize naming (lowercase with hyphens)
git mv docs/ARCHITECTURE.md docs/architecture.md
git mv docs/CLI-REFERENCE.md docs/cli-reference.md

# 2. Move misplaced documentation
git mv configurator/modules/README.md docs/developer-guide/module-development.md
git mv tests/TESTING.md docs/developer-guide/testing.md

# 3. Update mkdocs.yml navigation
# Update nav section to reflect new structure

# 4. Update internal links
# Search and replace old paths with new paths in all .md files

# 5. Validate documentation builds
mkdocs build --strict
```

### Scenario 4: Cleaning Up Test Organization

**Task**: Test files are poorly organized and don't match source structure

**Current**:

```
tests/
├── test_docker.py
├── test_git.py
├── integration_docker.py  # Wrong naming
├── validate_system.py     # Missing test_ prefix
```

**Target**:

```
tests/
├── unit/
│   ├── test_docker.py
│   ├── test_git.py
├── integration/
│   ├── test_docker_integration.py
├── validation/
│   ├── test_system_validation.py
```

**Steps**:

```bash
# 1. Create directory structure
mkdir -p tests/unit tests/integration tests/validation

# 2. Move and rename files
git mv tests/test_docker.py tests/unit/test_docker.py
git mv tests/test_git.py tests/unit/test_git.py
git mv tests/integration_docker.py tests/integration/test_docker_integration.py
git mv tests/validate_system.py tests/validation/test_system_validation.py

# 3. Update pytest.ini if needed
# Ensure testpaths includes new structure

# 4. Update import paths in test files
# Fix any relative imports affected by move

# 5. Run test suite
pytest tests/ -v
```

<!-- </scenarios> -->

---

## Success Criteria

<!-- <success-criteria> -->

A file organization task is complete when:

1. **Structural Compliance**

   - All files are in their correct architectural layer
   - All directories follow established hierarchy
   - No files violate layer boundary rules

2. **Naming Compliance**

   - 100% of files follow naming conventions
   - No CamelCase file names
   - All names are descriptive and clear

3. **Import Validity**

   - Zero circular dependencies
   - All imports follow organized structure
   - No broken imports

4. **Test Coverage**

   - All source files have corresponding test files
   - Test structure mirrors source structure
   - All tests pass

5. **Documentation Accuracy**

   - All file paths in documentation are correct
   - Architecture blueprints reflect current structure
   - CHANGELOG.md documents changes

6. **Quality Validation**
   - `ruff check configurator/` passes
   - `mypy configurator/` passes
   - `pytest tests/` passes
   - Git history preserved with `git mv`

<!-- </success-criteria> -->

---

## Quick Reference

### File Placement Decision Tree

```
Is this a new file?
├─ Yes: Determine file type
│  ├─ Module implementation? → configurator/modules/
│  ├─ Core orchestration? → configurator/core/
│  ├─ Security component? → configurator/security/
│  ├─ Utility function? → configurator/utils/
│  ├─ Test file? → tests/<type>/
│  └─ Documentation? → docs/<category>/
│
└─ No: Is it misplaced?
   ├─ Yes: Move to correct layer/domain
   └─ No: Is it following naming conventions?
      ├─ Yes: Done
      └─ No: Rename to follow conventions
```

### Common Commands

```bash
# Move file preserving history
git mv old/path.py new/path.py

# Find files to organize
find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*"

# Check for circular imports
python -m pylint --enable=cyclic-import configurator/

# Validate import organization
ruff check --select I configurator/

# Run tests after reorganization
pytest tests/ -v

# Validate documentation links
mkdocs build --strict
```

---

**Last Updated:** January 16, 2026
**Version:** 1.0
**Applies to:** debian-vps-workstation v2.0+

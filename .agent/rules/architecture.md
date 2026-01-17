---
trigger: always_on
glob: "**/*.py"
description: "Core architectural principles (4-Layer model, DI, Fail-safe)."
---

You are the system architect. You ensure the project adheres to the 4-Layer Modular Architecture.

# Architectural Rules

1.  **4-Layer Model**: Respect these boundaries:
    - **Presentation**: User Interface only.
    - **Orchestration**: Logic coordination, DI, State.
    - **Feature**: Independent business logic modules.
    - **Foundation**: Shared utilities, security (No deps on above).

2.  **Dependency Flow**:
    - Downward (Presenter -> Orchestrator -> Feature -> Foundation)
    - Inward (to core domain)
    - NEVER Upward (Foundation cannot import Feature).

3.  **Module Isolation**:
    - Modules MUST NOT import from other modules.
    - Use the Foundation layer for shared code.

4.  **Fail-Safe Defaults**:
    - Security options enabled by default.
    - Destructive actions require explicit confirmation.
    - **Rollback**: Register rollback actions BEFORE state changes.

5.  **Concurrency**:
    - Use `ThreadPoolExecutor` for system operations (filesystem, apt).
    - Avoid `async/await` for blocking I/O to prevent freezing.

6.  **Contextual Errors**:
    - Exceptions MUST explain: WHAT happened, WHY it happened, HOW to fix it.
    - Inherit from `ConfiguratorError`.

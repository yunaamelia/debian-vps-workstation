---
trigger: always_on
glob: "**/*.py"
description: "Rules for component interaction, layer boundaries, and extensions."
---

You are an integration specialist. You manage how different parts of the system talk to each other to prevent coupling.

# Integration Rules

1. **Communication Matrix**:
    - **Presenter -> Orchestrator**: Direct calls.
    - **Orchestrator -> Feature**: Interface/Base Class calls.
    - **Feature -> Foundation**: Direct utility calls.
    - **Foundation -> \***: NO upstream calls.

2. **Feature Isolation**:
    - Modules must be completely independent plugins.
    - No direct imports between `configurator/modules/a.py` and `b.py`.

3. **Registration**:
    - **Modules**: Must register in `modules/__init__.py`.
    - **Services**: Register in `container.py` (DI).
    - **Validators**: Register in tier `__init__.py`.

4. **Events & Hooks**:
    - Use for side effects (logging, reporting).
    - Handlers must be idempotent (safe to run twice).
    - Failure in a hook must not crash the app.

5. **Testing Interactions**:
    - Integration tests MUST verify rollback success.
    - Test happy paths AND error propagation paths.

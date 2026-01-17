---
applyTo: "**"
---

# Workflow Instructions

> Permanent workflow guidelines for consistent development practices.

---

## Workflow Philosophy

### Core Principles

1. **Modularity First**: Design features as independent, self-contained modules that can be tested, deployed, and maintained in isolation
2. **Fail-Safe by Default**: All operations must be reversible with explicit rollback mechanisms
3. **Validation Before Action**: Never execute state changes without prior validation
4. **Observable Progress**: Users must always know what the system is doing and why
5. **Graceful Degradation**: Partial failures must not compromise system stability

### Guiding Values

- **Predictability**: Same inputs produce same outputs across environments
- **Transparency**: Operations explain what they're doing in human-readable terms
- **Recoverability**: Any operation can be undone to restore previous state
- **Extensibility**: New features integrate without modifying existing code

---

## Development Process

### Feature Development Lifecycle

1. **Define Interface First**
   - Create abstract base class or interface before implementation
   - Define method signatures with complete type hints
   - Document expected behavior in docstrings

2. **Implement Core Logic**
   - Start with the happy path
   - Use dependency injection for external services
   - Add rollback registration before any state changes

3. **Add Error Handling**
   - Use domain-specific custom exceptions
   - Log errors with full context
   - Return meaningful error messages to users

4. **Register with System**
   - Add to dependency injection container if service
   - Register in package initialization if module
   - Add CLI command if user-facing

5. **Write Tests**
   - Unit tests for core logic
   - Integration tests for workflows
   - Mock external dependencies

### Three-Phase Module Pattern

All feature modules must implement this lifecycle:

```
validate() → configure() → verify()
```

| Phase       | Purpose                                | Requirements                        |
| ----------- | -------------------------------------- | ----------------------------------- |
| `validate`  | Check prerequisites are met            | Must be idempotent, no side effects |
| `configure` | Apply changes to system                | Must register rollback first        |
| `verify`    | Confirm changes achieved desired state | Must be independent of configure    |

---

## Branching Strategy

### Branch Types

| Type    | Pattern             | Purpose                 | Lifespan    |
| ------- | ------------------- | ----------------------- | ----------- |
| Main    | `main`              | Production-ready code   | Permanent   |
| Feature | `feature/<name>`    | New feature development | Until merge |
| Bugfix  | `bugfix/<name>`     | Bug fixes               | Until merge |
| Hotfix  | `hotfix/<name>`     | Urgent production fixes | Until merge |
| Release | `release/<version>` | Release preparation     | Until tag   |

### Branch Rules

- All features must branch from and merge back to `main`
- Hotfixes branch from `main` and merge to both `main` and any active release branches
- Never commit directly to `main`—all changes require pull requests
- Keep branches short-lived; merge or close within one iteration

---

## Code Review Process

### Review Checklist

Before approval, reviewers must verify:

- [ ] Code follows established patterns and naming conventions
- [ ] All state changes register rollback actions
- [ ] CLI commands handle exceptions gracefully
- [ ] Feature modules implement three-phase lifecycle
- [ ] Validators return proper result objects
- [ ] Async operations support dry-run mode
- [ ] Tests cover happy path and error cases
- [ ] Documentation is updated for user-facing changes

### Review Standards

- **Blocking Issues**: Security vulnerabilities, data loss risks, missing rollback
- **Suggested Changes**: Style improvements, optimization opportunities
- **Comments**: Questions, clarifications, alternative approaches

---

## Testing Requirements

### Test Hierarchy

| Level       | Scope                 | Purpose                 | Speed  |
| ----------- | --------------------- | ----------------------- | ------ |
| Unit        | Single function/class | Logic correctness       | Fast   |
| Integration | Multiple components   | Interaction correctness | Medium |
| System      | Full application      | End-to-end correctness  | Slow   |

### Quality Gates

All code must pass before merge:

1. **All unit tests pass** (100% required)
2. **Integration tests pass** (100% required)
3. **Code coverage maintained** (no reduction from baseline)
4. **Static analysis clean** (no new warnings)
5. **Documentation builds** (no broken links)

### Testing Principles

- Mock external dependencies (network, filesystem, databases)
- Test error paths, not just happy paths
- Verify rollback mechanisms actually work
- Use fixtures for consistent test data

---

## Deployment Pipeline

### Pipeline Stages

```
Validate → Build → Test → Stage → Deploy → Verify
```

| Stage    | Actions                         | Gate                            |
| -------- | ------------------------------- | ------------------------------- |
| Validate | Lint, type check, security scan | Zero issues                     |
| Build    | Compile, package, containerize  | Build succeeds                  |
| Test     | Unit, integration, system tests | All tests pass                  |
| Stage    | Deploy to staging environment   | Deployment succeeds             |
| Deploy   | Deploy to production            | Approval + staging verification |
| Verify   | Smoke tests, health checks      | All verification passes         |

### Deployment Principles

- All deployments must be automated and reproducible
- Manual steps require documentation and approval
- Rollback plan must exist before any deployment
- Feature flags enable gradual rollout

---

## Collaboration Guidelines

### Communication Patterns

| When             | Action                                            |
| ---------------- | ------------------------------------------------- |
| Starting feature | Create issue/ticket with acceptance criteria      |
| Blocking issue   | Raise immediately, don't wait for standup         |
| Design decision  | Document in ADR (Architecture Decision Record)    |
| Breaking change  | Announce to team, update changelog, major version |
| Completion       | Update ticket, notify stakeholders                |

### Code Ownership

- Module owners review changes to their modules
- Security changes require security lead review
- API changes require documentation update
- Breaking changes require team consensus

### Documentation Standards

- User-facing features require user documentation
- Code changes require updated code comments
- Architecture changes require updated diagrams
- All decisions require rationale documentation

---

## Quality Standards

### Non-Negotiable Requirements

1. **Rollback Registration**: All state changes must register rollback actions before execution
2. **Exception Handling**: All CLI commands must handle exceptions and exit gracefully
3. **Lifecycle Compliance**: All modules must implement validate/configure/verify lifecycle
4. **Result Objects**: All validators must return structured result objects
5. **Dry-Run Support**: All destructive operations must support preview mode
6. **Progress Reporting**: All long-running operations must report progress

### Code Quality Metrics

| Metric                | Target            | Blocking Threshold |
| --------------------- | ----------------- | ------------------ |
| Test coverage         | ≥ 80%             | < 70%              |
| Cyclomatic complexity | ≤ 10 per function | > 15               |
| Duplicate code        | ≤ 3%              | > 5%               |
| Documentation         | 100% public APIs  | < 90%              |

### Patterns to Avoid

| Anti-Pattern             | Correct Approach                   |
| ------------------------ | ---------------------------------- |
| Missing rollback         | Always `add_*` before state change |
| Bare `except:` clauses   | Catch specific exceptions          |
| Hardcoded paths          | Use configuration values           |
| Blocking main thread     | Use async/parallel execution       |
| Ignoring dry-run mode    | Check dry-run flag before changes  |
| Missing progress updates | Report progress regularly          |

---

## Extension Points

When adding new functionality, use established extension mechanisms:

| Extension Type | Location/Pattern             | Integration Method              |
| -------------- | ---------------------------- | ------------------------------- |
| Feature Module | Inherit from base class      | Register in container           |
| Validator      | Add to appropriate tier      | Register with orchestrator      |
| Hook           | Implement hook interface     | Register with hooks manager     |
| Plugin         | Follow plugin structure      | Drop into plugins directory     |
| Reporter       | Implement reporter interface | Inject via dependency injection |

---

## Key Design Patterns

Apply these patterns consistently:

| Pattern              | Application                                     |
| -------------------- | ----------------------------------------------- |
| Dependency Injection | Accept optional deps with defaults              |
| Template Method      | `validate() → configure() → verify()` lifecycle |
| Command Pattern      | Rollback actions as executable objects          |
| Observer Pattern     | Hooks for lifecycle events                      |
| Circuit Breaker      | Resilience for external operations              |
| Tiered Validation    | Critical → High → Medium priority               |
| Strategy Pattern     | Swappable execution strategies                  |

---

_These workflow guidelines establish a permanent framework for consistent development practices. Implementation details may evolve, but these principles remain constant._

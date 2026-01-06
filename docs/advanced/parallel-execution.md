# Advanced: Parallel Module Execution

The `vps-configurator` supports parallel execution of independent modules to significantly reduce installation time.

## How it works

The installer builds a **Dependency Graph** of all enabled modules.
It then groups modules into "batches" that can run simultaneously.

**Example:**
- `system`, `security` (Priority 10, 20) -> Sequential (usually) or Parallel if independent?
Actually, `security` doesn't depend on `system` directly in code, but implicit priority ordering is preserved via sequential execution within batches if needed?
No, the parallel executor runs items in a batch *concurrently*.
Batches are ordered sequentially.

If `system` must run before `security`, it should be a dependency.
If not declared as dependency, they might run in parallel!
**Important:** Modules with implicit dependencies must declare them in `depends_on`.

## Configuration

Parallel execution is enabled by default.

To disable (e.g., for debugging):
`config.yaml`:
```yaml
performance:
  parallel_execution: false
  max_workers: 4
```

CLI:
```bash
vps-configurator install --no-parallel
```

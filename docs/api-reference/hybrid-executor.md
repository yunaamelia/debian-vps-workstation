# HybridExecutor

**Module:** `configurator.core.execution.hybrid`

Hybrid execution engine.

Intelligently routes module execution to optimal executor:

- ParallelExecutor: For independent modules
- PipelineExecutor: For large sequential modules

## Methods

### `__init__(self, max_workers: int = 4, logger: Optional[logging.Logger] = None)`

---

### `can_handle(self, contexts: List[configurator.core.execution.base.ExecutionContext]) -> bool`

Hybrid executor can handle any contexts.

---

### `execute(self, contexts: List[configurator.core.execution.base.ExecutionContext], callback: Optional[Callable] = None) -> Dict[str, configurator.core.execution.base.ExecutionResult]`

Execute modules using optimal strategy.

Strategy:

1. Categorize contexts (pipeline vs parallel)
2. Route each group to appropriate executor
3. Merge results

---

### `get_name(self) -> str`

---

# PROMPT 1.1: PARALLEL EXECUTION ENGINE IMPLEMENTATION

## 📋 Context

This is the **First Foundation Feature** of the Debian VPS Configurator.
We need a robust parallel execution engine to run independent configuration tasks concurrently (e.g., installing non-dependent packages, configuring independent services). This will significantly reduce the total execution time (target 90% reduction).

## 🎯 Objective

Implement a `ParallelExecutor` class in `configurator/core/parallel.py` that utilizes `concurrent.futures.ThreadPoolExecutor` to run tasks in parallel. Ideally, it should handle dependencies (DAG) or at least simple lists of tasks.

## 🛠️ Requirements

### Functional

1. **Parallel Execution**: Run a list of callable tasks concurrently.
2. **Configurable Workers**: Number of threads must be configurable via `config.yaml` or CLI args.
3. **Error Handling**: If one task fails, capture the exception but allow others to finish (configurable: fail-fast or fail-safe).
4. **Result Aggregation**: Return a report of successes and failures.
5. **Progress Tracking**: Integrate with a progress bar (Rich library).

### Non-Functional

1. **Thread Safety**: Ensure shared resources (logging, file writes) are thread-safe.
2. **Performance**: Minimal overhead for managing threads.

## 📝 Specifications

### Configuration (`config.yaml`)

```yaml
performance:
  parallel_execution:
    enabled: true
    max_workers: 4 # Default to CPU count
    fail_fast: false
```

### Class Signature (`configurator/core/parallel.py`)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any, Dict
from dataclasses import dataclass

@dataclass
class TaskResult:
    task_name: str
    status: str  # 'success', 'failed', 'skipped'
    result: Any
    error: Exception = None
    execution_time: float = 0.0

class ParallelExecutor:
    def __init__(self, max_workers: int = 4, fail_fast: bool = False):
        pass

    def execute_tasks(self, tasks: List[Callable]) -> List[TaskResult]:
        """
        Executes a list of callables in parallel.
        Named tasks are preferred for reporting.
        """
        pass
```

## 🪜 Implementation Steps

1. **Create the Module**:

    - Create `configurator/core/parallel.py`.
    - Define the `TaskResult` dataclass.
    - Define the `ParallelExecutor` class.

2. **Implement `__init__`**:

    - Load `max_workers` from config if not provided.

3. **Implement `execute_tasks`**:

    - Use `ThreadPoolExecutor`.
    - Submit tasks.
    - Use `tqdm` or `rich.progress` to show a progress bar.
    - Catch exceptions inside the thread execution to prevent crashing only that thread.
    - Collect results.

4. **Add Helper**:

    - Create a decorator `@parallel_task(name="...")` to wrap functions if needed.

5. **Integration Test**:
    - Create a test script `tests/unit/test_parallel.py` that runs 5 dummy tasks sleeping for 1 second each. Total time should be ~1 second (with 5 workers), not 5 seconds.

## 🔍 Validation Checklist

- [ ] 5 tasks of 1s run in approx 1s with 5 workers.
- [ ] Exceptions are caught and reported in `TaskResult`.
- [ ] Progress bar updates correctly.
- [ ] `fail_fast=True` stops execution on first error (optional, nice to have).

---

**Output**: Generate the python code for `configurator/core/parallel.py` and the test file `tests/unit/test_parallel.py`.

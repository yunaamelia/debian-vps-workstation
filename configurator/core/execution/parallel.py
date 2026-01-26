import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from configurator.core.execution.base import ExecutionContext, ExecutionResult, ExecutorInterface


class ParallelExecutor(ExecutorInterface):
    """
    Parallel executor using ThreadPoolExecutor.

    Best for: Independent modules with no sequential dependencies.
    """

    def __init__(self, max_workers: int = 4, logger: Optional[logging.Logger] = None) -> None:
        self.max_workers = max_workers
        self.logger = logger or logging.getLogger(__name__)

    def get_name(self) -> str:
        return "ParallelExecutor"

    def can_handle(self, contexts: List[ExecutionContext]) -> bool:
        """
        Parallel executor can handle any contexts.

        Returns True if:
        - More than 1 context
        - No context has force_sequential=True
        """
        if len(contexts) <= 1:
            return False

        # Check if any module requires sequential execution
        for context in contexts:
            module = context.module_instance
            if getattr(module, "force_sequential", False):
                return False

        return True

    def execute(
        self,
        contexts: List[ExecutionContext],
        callback: Optional[Callable[..., Any]] = None,
    ) -> Dict[str, ExecutionResult]:
        """Execute modules in parallel."""
        self.logger.info(
            f"ParallelExecutor: Executing {len(contexts)} modules with {self.max_workers} workers"
        )

        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_context = {
                executor.submit(self._execute_module, context, callback): context
                for context in contexts
            }

            # Collect results as they complete
            for future in as_completed(future_to_context):
                context = future_to_context[future]

                try:
                    result = future.result()
                    results[context.module_name] = result
                except Exception as e:
                    self.logger.error(
                        f"Unexpected error executing {context.module_name}: {e}", exc_info=True
                    )
                    results[context.module_name] = ExecutionResult(
                        module_name=context.module_name,
                        success=False,
                        started_at=datetime.now(),
                        completed_at=datetime.now(),
                        duration_seconds=0,
                        error=e,
                    )

        return results

    def _execute_module(
        self,
        context: ExecutionContext,
        callback: Optional[Callable[..., Any]],
    ) -> ExecutionResult:
        """Execute a single module."""
        module = context.module_instance
        started_at = datetime.now()
        thread_name = threading.current_thread().name

        # Get module-specific logger from LogManager
        from configurator.logger import get_log_manager

        log_manager = get_log_manager()
        # Use a localized logger
        module_logger = log_manager.get_logger(context.module_name)

        # We replace self.logger with module_logger for this execution context
        # But wait, self.logger is the executor's logger.
        # We should use module_logger for logging inside this method for this module.
        logger = module_logger

        try:
            logger.debug(f"[{thread_name}] Starting execution of {context.module_name}")

            # Inject logger into module
            if hasattr(module, "logger"):
                module.logger = logger

            # Notify start
            if callback:
                callback(context.module_name, "started", {})

            if context.dry_run:
                logger.info(f"[{thread_name}] DRY RUN mode enabled for {context.module_name}")

            # Validate
            if callback:
                callback(context.module_name, "validating", {})

            if hasattr(module, "validate"):
                if not module.validate():
                    raise Exception(f"Validation failed for {context.module_name}")
            else:
                logger.debug(
                    f"[{thread_name}] Module {context.module_name} has no validate method, skipping"
                )

            # Configure
            if callback:
                callback(context.module_name, "configuring", {})

            if hasattr(module, "configure"):
                # In dry-run we might skip actual configure if implemented, but here we assume module handles logic or we call it
                # If dry_run is passed in context, maybe we should pass it to module?
                # For now assuming module.configure() does the right thing or we are running it.
                # If the module doesn't accept args, we just call it.
                if not module.configure():
                    raise Exception(f"Configuration failed for {context.module_name}")
            else:
                logger.debug(
                    f"[{thread_name}] Module {context.module_name} has no configure method, skipping"
                )

            # Verify
            if callback:
                callback(context.module_name, "verifying", {})

            if hasattr(module, "verify"):
                if not module.verify():
                    logger.warning(
                        f"[{thread_name}] Verification warnings for {context.module_name}"
                    )

            # Success
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            if callback:
                callback(context.module_name, "completed", {"duration": duration})

            logger.debug(f"[{thread_name}] Finished {context.module_name} in {duration:.2f}s")

            return ExecutionResult(
                module_name=context.module_name,
                success=True,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
            )

        except Exception as e:
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            logger.error(f"[{thread_name}] Failed {context.module_name}: {e}")

            if callback:
                callback(context.module_name, "failed", {"error": str(e)})

            return ExecutionResult(
                module_name=context.module_name,
                success=False,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration,
                error=e,
            )

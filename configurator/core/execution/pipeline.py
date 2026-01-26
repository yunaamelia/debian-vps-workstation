import logging
from datetime import datetime
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

from configurator.core.execution.base import ExecutionContext, ExecutionResult, ExecutorInterface


class PipelineExecutor(ExecutorInterface):
    """
    Pipeline-based executor for large sequential modules.

    Best for:
    - Large modules with many sequential steps (e.g., desktop)
    - Modules with force_sequential=True
    - Modules with heavy resource usage
    """

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def get_name(self) -> str:
        return "PipelineExecutor"

    def can_handle(self, contexts: List[ExecutionContext]) -> bool:
        """
        Pipeline is best for:
        - Single module
        - Module with force_sequential=True
        - Module with large_module=True
        """
        if len(contexts) != 1:
            return False

        module = contexts[0].module_instance
        return getattr(module, "force_sequential", False) or getattr(module, "large_module", False)

    def execute(
        self,
        contexts: List[ExecutionContext],
        callback: Optional[Callable[..., Any]] = None,
    ) -> Dict[str, ExecutionResult]:
        """Execute modules using pipeline approach."""
        self.logger.info(f"PipelineExecutor: Executing {len(contexts)} module(s)")

        results = {}

        for context in contexts:
            result = self._execute_pipeline(context, callback)
            results[context.module_name] = result

        return results

    def _execute_pipeline(
        self,
        context: ExecutionContext,
        callback: Optional[Callable[..., Any]],
    ) -> ExecutionResult:
        """Execute single module via pipeline."""
        module = context.module_instance
        started_at = datetime.now()

        try:
            # Create execution pipeline
            pipeline = self._create_pipeline(context)

            # Execute each stage
            for stage_name, stage_success, stage_data in pipeline:
                if callback:
                    callback(context.module_name, stage_name, stage_data)

                if not stage_success:
                    raise Exception(f"Pipeline stage '{stage_name}' failed")

            # Success
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()

            if callback:
                callback(context.module_name, "completed", {"duration": duration})

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

    def _create_pipeline(
        self, context: ExecutionContext
    ) -> Generator[Tuple[str, bool, Dict[str, Any]], None, None]:
        """
        Create execution pipeline for module.

        Yields:
            (stage_name, success, metadata) tuples
        """
        module = context.module_instance

        # Stage 1: Validate
        if hasattr(module, "validate"):
            yield ("validating", module.validate(), {})
        else:
            yield ("validating", True, {"skipped": True})

        # Stage 2: Pre-configure hooks (if exists)
        if hasattr(module, "pre_configure"):
            yield ("pre_configure", module.pre_configure(), {})

        # Stage 3: Configure (main installation)
        if hasattr(module, "configure"):
            yield ("configuring", module.configure(), {})
        else:
            yield ("configuring", True, {"skipped": True})

        # Stage 4: Post-configure hooks (if exists)
        if hasattr(module, "post_configure"):
            yield ("post_configure", module.post_configure(), {})

        # Stage 5: Verify
        if hasattr(module, "verify"):
            yield ("verifying", module.verify(), {})
        else:
            yield ("verifying", True, {"skipped": True})

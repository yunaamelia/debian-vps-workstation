import logging
from typing import Any, Callable, Dict, List, Optional

from configurator.core.execution.base import ExecutionContext, ExecutionResult, ExecutorInterface
from configurator.core.execution.parallel import ParallelExecutor
from configurator.core.execution.pipeline import PipelineExecutor


class HybridExecutor(ExecutorInterface):
    """
    Hybrid execution engine.

    Intelligently routes module execution to optimal executor:
    - ParallelExecutor: For independent modules
    - PipelineExecutor: For large sequential modules
    """

    def __init__(self, max_workers: int = 4, logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or logging.getLogger(__name__)

        # Initialize sub-executors
        self.parallel_executor = ParallelExecutor(max_workers=max_workers, logger=self.logger)
        self.pipeline_executor = PipelineExecutor(logger=self.logger)

    def get_name(self) -> str:
        return "HybridExecutor"

    def can_handle(self, contexts: List[ExecutionContext]) -> bool:
        """Hybrid executor can handle any contexts."""
        return True

    def execute(
        self,
        contexts: List[ExecutionContext],
        callback: Optional[Callable[..., Any]] = None,
    ) -> Dict[str, ExecutionResult]:
        """
        Execute modules using optimal strategy.

        Strategy:
        1. Categorize contexts (pipeline vs parallel)
        2. Route each group to appropriate executor
        3. Merge results
        """
        self.logger.info(f"HybridExecutor: Routing {len(contexts)} module(s)")

        # Categorize modules
        pipeline_contexts = []
        parallel_contexts = []

        for context in contexts:
            if self._should_use_pipeline(context):
                pipeline_contexts.append(context)
                self.logger.debug(
                    f"Routing {context.module_name} to PipelineExecutor "
                    f"(force_sequential={getattr(context.module_instance, 'force_sequential', False)})"
                )
            else:
                parallel_contexts.append(context)
                self.logger.debug(f"Routing {context.module_name} to ParallelExecutor")

        results = {}

        # Execute pipeline modules (sequential by definition)
        for context in pipeline_contexts:
            pipeline_results = self.pipeline_executor.execute([context], callback)
            results.update(pipeline_results)

        # Execute parallel modules
        if parallel_contexts:
            parallel_results = self.parallel_executor.execute(parallel_contexts, callback)
            results.update(parallel_results)

        return results

    def _should_use_pipeline(self, context: ExecutionContext) -> bool:
        """Determine if context should use pipeline executor."""
        module = context.module_instance

        return getattr(module, "force_sequential", False) or getattr(module, "large_module", False)

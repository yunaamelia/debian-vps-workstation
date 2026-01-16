# Performance Optimization

## Strategy

1.  **Parallel Execution**: Independent modules run concurrently.
2.  **Lazy Loading**: Modules are imported only when needed.
3.  **Package Caching**: APT packages are cached to avoid re-downloading.

## Tuning

Adjust `max_workers` in `config/default.yaml` to optimize for your CPU core count.

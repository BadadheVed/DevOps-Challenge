from prometheus_client import CollectorRegistry, Counter, Histogram

# LOCAL registry for this worker pod (created once at import time)
REGISTRY = CollectorRegistry()

LLM_CALLS = Counter(
    'llm_calls_total',
    'Total LLM function calls by function name and status',
    ['function', 'status'],
    registry=REGISTRY
)

LLM_LATENCY = Histogram(
    'llm_function_latency_seconds',
    'LLM function execution latency in seconds',
    ['function'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 7.0, 10.0),
    registry=REGISTRY
)
__all__ = ['REGISTRY', 'LLM_CALLS', 'LLM_LATENCY']
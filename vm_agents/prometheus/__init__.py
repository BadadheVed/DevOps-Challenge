
from .registry import GLOBAL_REGISTRY
from .outcomes import mark_success, mark_failure, mark_latency, reset_outcome
from .prometheus import CounterMiddleware, GaugeMiddleware, HistogramMiddleware

# Export the global registry for /metrics endpoint
REGISTRY = GLOBAL_REGISTRY

__all__ = [
    "mark_success",
    "mark_failure",
    "mark_latency",
    "reset_outcome",
    "CounterMiddleware",
    "GaugeMiddleware",
    "HistogramMiddleware",
    "REGISTRY",
]

from prometheus_client import Counter, Gauge, Histogram
from .prometheus import REGISTRY   # IMPORT existing registry


LLM_CALLS = Counter(
    "llm_calls_total",
    "Total LLM calls by function name and status",
    ["function", "status"],
    registry=REGISTRY
)

LLM_IN_FLIGHT = Gauge(
    "LLM_IN_FLIGHT",
    "LLM Calls  currently executing",
    ["function"],
    registry=REGISTRY
)

LLM_LATENCY = Histogram(
    "llm_execution_latency_seconds",
    "LLM execution latency in seconds",
    ["function"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 7.0, 10.0),
    registry=REGISTRY
)

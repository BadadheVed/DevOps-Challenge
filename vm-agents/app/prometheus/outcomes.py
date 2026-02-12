import logging
from prometheus.functions import LLM_CALLS, LLM_LATENCY

logger = logging.getLogger(__name__)


def mark_success(function_name: str) -> None:
    """Record a successful function execution."""
    try:
        LLM_CALLS.labels(function=function_name, status="success").inc()
    except Exception as e:
        logger.error(f"Failed to mark success for {function_name}: {e}")
        pass


def mark_failure(function_name: str) -> None:
    """Record a failed function execution."""
    try:
        LLM_CALLS.labels(function=function_name, status="failure").inc()
    except Exception as e:
        logger.error(f"Failed to mark failure for {function_name}: {e}")
        pass


def mark_latency(function_name: str, duration_ms: float) -> None:
    """Record function execution latency in milliseconds."""
    try:
        duration_seconds = duration_ms / 1000.0
        LLM_LATENCY.labels(function=function_name).observe(duration_seconds)
    except Exception as e:
        logger.error(f"Failed to mark latency for {function_name}: {e}")
        pass


def reset_outcome() -> None:
    """No-op for backward compatibility."""
    pass

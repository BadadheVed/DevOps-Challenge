import asyncio
from contextvars import ContextVar
from .functions import LLM_CALLS, LLM_LATENCY

# Track recorded outcomes per context to prevent duplicates
# Use a None default and initialize a fresh set per context when needed
_outcomes_marked: ContextVar[set | None] = ContextVar("outcomes_marked", default=None)


def _is_async_context() -> bool:
    """Check if we're running in an async context."""
    try:
        asyncio.current_task()
        return True
    except RuntimeError:
        return False


def mark_success(function_name: str) -> None:
    """
    Record a successful function execution. Only marks once per context.
    Safe to call from both sync and async functions.
    """
    try:
        if _is_async_context():
            try:
                outcome_key = (function_name, "success")
                marked_outcomes = _outcomes_marked.get()
                if marked_outcomes is None:
                    marked_outcomes = set()
                if outcome_key in marked_outcomes:  # Already recorded
                    return
                LLM_CALLS.labels(function=function_name, status="success").inc()
                marked_outcomes.add(outcome_key)
                _outcomes_marked.set(marked_outcomes)
            except Exception:
                pass
        else:
            try:
                outcome_key = (function_name, "success")
                marked_outcomes = _outcomes_marked.get()
                if marked_outcomes is None:
                    marked_outcomes = set()
                if outcome_key in marked_outcomes:  # Already recorded
                    return
                LLM_CALLS.labels(function=function_name, status="success").inc()
                marked_outcomes.add(outcome_key)
                _outcomes_marked.set(marked_outcomes)
            except Exception:
                pass
    except Exception:
        pass  # Metrics never break app


def mark_failure(function_name: str) -> None:
    """
    Record a failed function execution. Only marks once per context.
    Safe to call from both sync and async functions.
    """
    try:
        if _is_async_context():
            try:
                outcome_key = (function_name, "failed")
                marked_outcomes = _outcomes_marked.get()
                if marked_outcomes is None:
                    marked_outcomes = set()
                if outcome_key in marked_outcomes:  # Already recorded
                    return
                LLM_CALLS.labels(function=function_name, status="failed").inc()
                marked_outcomes.add(outcome_key)
                _outcomes_marked.set(marked_outcomes)
            except Exception:
                pass
        else:
            try:
                outcome_key = (function_name, "failed")
                marked_outcomes = _outcomes_marked.get()
                if marked_outcomes is None:
                    marked_outcomes = set()
                if outcome_key in marked_outcomes:  # Already recorded
                    return
                LLM_CALLS.labels(function=function_name, status="failed").inc()
                marked_outcomes.add(outcome_key)
                _outcomes_marked.set(marked_outcomes)
            except Exception:
                pass
    except Exception:
        pass  # Metrics never break app


def mark_latency(function_name: str, duration_seconds: float) -> None:
    """
    Record function execution latency in seconds.
    Safe to call from both sync and async functions.
    
    Args:
        function_name: Name of the function
        duration_seconds: Execution time in seconds
    """
    try:
        if _is_async_context():
            try:
                LLM_LATENCY.labels(function=function_name).observe(duration_seconds)
            except Exception:
                pass
        else:
            try:
                LLM_LATENCY.labels(function=function_name).observe(duration_seconds)
            except Exception:
                pass
    except Exception:
        pass


def reset_outcome() -> None:
    """
    Reset outcome tracking for the next message.
    Safe to call from both sync and async functions.
    """
    try:
        if _is_async_context():
            try:
                _outcomes_marked.set(set())
            except Exception:
                pass
        else:
            try:
                _outcomes_marked.set(set())
            except Exception:
                pass
    except Exception:
        pass

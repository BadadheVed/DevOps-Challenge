from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import time
import logging

logger = logging.getLogger(__name__)


REGISTRY = CollectorRegistry()


REQUEST_TOTAL = Counter(
    'http_requests_total', 
    'Total HTTP requests by method, endpoint, and status code', 
    ['method', 'endpoint', 'status_code'], 
    registry=REGISTRY
)

 
REQUEST_DURATION = Histogram(
    "http_request_duration_ms",
    "HTTP request duration by method and endpoint (milliseconds)",
    ["method", "endpoint"],
    buckets=(10, 50, 100, 250, 500, 1000, 2500, 5000, 10000),
    registry=REGISTRY,
)

# GAUGE metric
ACTIVE_REQUESTS = Gauge(
    'http_requests_active', 
    'Active HTTP requests by endpoint (normalized dynamic routes)', 
    ['endpoint'],
    registry=REGISTRY
)

def _get_normalized_endpoint(request: Request) -> str:
    """Extract route template to avoid high cardinality.

    - Uses route.path for FastAPI routes (e.g., /user/{user_id})
    - Falls back to raw path from ASGI scope (never includes query params)
    """
    route = request.scope.get('route')

    if route and hasattr(route, 'path'):
        return route.path  # Returns /user/{user_id} instead of /user/123

    # Fallback: use ASGI scope path (excludes query params)
    return request.scope.get('path', '/')


class CounterMiddleware(BaseHTTPMiddleware):
    """COUNTER - Total requests (method + endpoint + status_code)"""

    async def dispatch(self, request: Request, call_next):
        status_code = 500  # Default to 500 if exception occurs
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            # Record metrics even if exception occurred
            endpoint = _get_normalized_endpoint(request)
            try:
                REQUEST_TOTAL.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status_code=str(status_code)
                ).inc()
            except Exception as metric_error:
                logger.error(f"Failed to record counter metric: {metric_error}")
            # Re-raise the original exception (FastAPI will handle it as 500)
            raise
        
        # Record metrics for successful response
        endpoint = _get_normalized_endpoint(request)
        try:
            REQUEST_TOTAL.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()
        except Exception as metric_error:
            logger.error(f"Failed to record counter metric: {metric_error}")
        
        return response


class HistogramMiddleware(BaseHTTPMiddleware):
    """HISTOGRAM - Request latency (method + endpoint)"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
        except Exception as e:
            # Still record latency even if exception occurs
            duration_ms = (time.time() - start_time) * 1000
            endpoint = _get_normalized_endpoint(request)
            try:
                REQUEST_DURATION.labels(
                    method=request.method,
                    endpoint=endpoint,
                ).observe(duration_ms)
            except Exception as metric_error:
                logger.error(f"Failed to record histogram metric: {metric_error}")
            raise

        duration_ms = (time.time() - start_time) * 1000
        endpoint = _get_normalized_endpoint(request)

        try:
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(duration_ms)
        except Exception as metric_error:
            logger.error(f"Failed to record histogram metric: {metric_error}")

        return response


class GaugeMiddleware(BaseHTTPMiddleware):
    """GAUGE - Active requests tracking"""

    async def dispatch(self, request: Request, call_next):
        try:
            ACTIVE_REQUESTS.labels(endpoint="all").inc()
        except Exception as metric_error:
            logger.error(f"Failed to increment active requests gauge: {metric_error}")
        
        try:
            response = await call_next(request)
            return response
        finally:
            try:
                ACTIVE_REQUESTS.labels(endpoint="all").dec()
            except Exception as metric_error:
                logger.error(f"Failed to decrement active requests gauge: {metric_error}")




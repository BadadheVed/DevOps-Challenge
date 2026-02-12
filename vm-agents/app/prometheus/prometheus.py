from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge
import time

from .registry import GLOBAL_REGISTRY

# Use the global registry that all processes share
REGISTRY = GLOBAL_REGISTRY


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
        response = await call_next(request)

        # Get endpoint AFTER call_next - route is now matched
        endpoint = _get_normalized_endpoint(request)

        REQUEST_TOTAL.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=str(response.status_code)
        ).inc()

        return response


class HistogramMiddleware(BaseHTTPMiddleware):
    """HISTOGRAM - Request latency (method + endpoint)"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Get endpoint AFTER call_next - route is now matched
        endpoint = _get_normalized_endpoint(request)

        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration_ms)

        return response


class GaugeMiddleware(BaseHTTPMiddleware):
   

    async def dispatch(self, request: Request, call_next):
        ACTIVE_REQUESTS.labels(endpoint="all").inc()
        try:
            response = await call_next(request)
            return response
        finally:
            ACTIVE_REQUESTS.labels(endpoint="all").dec()




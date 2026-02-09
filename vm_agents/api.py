"""
FastAPI app using the GLOBAL registry
Tests if multiple instances share the same metrics or collide
"""
import logging
import random
import time
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry
import uvicorn

from prometheus.registry import GLOBAL_REGISTRY
from prometheus.prometheus import REQUEST_TOTAL, REQUEST_DURATION, ACTIVE_REQUESTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Prometheus Registry Test - Global")

# Middleware to track HTTP metrics
class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path
        
        # Get normalized endpoint
        route = request.scope.get('route')
        endpoint = route.path if route and hasattr(route, 'path') else path
        
        # Increment active requests
        ACTIVE_REQUESTS.labels(endpoint=endpoint).inc()
        
        start_time = time.time()
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            status_code = response.status_code
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            status_code = 500
            ACTIVE_REQUESTS.labels(endpoint=endpoint).dec()
            raise
        finally:
            ACTIVE_REQUESTS.labels(endpoint=endpoint).dec()
        
        # Record metrics
        REQUEST_TOTAL.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration_ms)
        
        logger.info(f"{method} {endpoint} - {status_code} - {duration_ms:.2f}ms")
        return response

app.add_middleware(PrometheusMiddleware)

# Test metrics using GLOBAL_REGISTRY
TEST_COUNTER = Counter(
    'api_test_operations_total',
    'Test operations using global registry',
    ['operation', 'result'],
    registry=GLOBAL_REGISTRY
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "registry_type": "GLOBAL"}

@app.get("/api/operation/{operation_id}")
async def perform_operation(operation_id: int):
    """Simulate an operation and record metrics"""
    success = random.random() > 0.2  # 80% success rate
    
    if success:
        TEST_COUNTER.labels(operation='test_op', result='success').inc()
        logger.info(f"✓ Operation {operation_id} succeeded (GLOBAL REGISTRY)")
        return {"operation_id": operation_id, "status": "success"}
    else:
        TEST_COUNTER.labels(operation='test_op', result='failure').inc()
        logger.error(f"✗ Operation {operation_id} failed (GLOBAL REGISTRY)")
        return {"operation_id": operation_id, "status": "failure"}

@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics from GLOBAL_REGISTRY"""
    return generate_latest(GLOBAL_REGISTRY)

@app.get("/info")
async def info():
    """Show which registry this app is using"""
    return {
        "app": "API with GLOBAL Registry",
        "registry_id": id(GLOBAL_REGISTRY),
        "description": "This app uses the shared GLOBAL_REGISTRY. All instances share the same metrics."
    }

if __name__ == "__main__":
    logger.info("Starting FastAPI with GLOBAL_REGISTRY on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

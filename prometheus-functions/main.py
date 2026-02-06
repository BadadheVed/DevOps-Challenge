import time
import asyncio
import logging
import os
from fastapi import FastAPI
from prometheus_client import push_to_gateway
from prometheus.functions import REGISTRY
from prometheus import CounterMiddleware, HistogramMiddleware, GaugeMiddleware
from prometheus.outcomes import mark_failure, reset_outcome, mark_success
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pushgateway configuration
PUSHGATEWAY_URL = "http://pushgateway-prometheus-pushgateway.monitoring.svc.cluster.local:9091"
PUSH_INTERVAL = 5  # seconds
JOB_NAME = "gemini-stt"
# Note: Not using instance label - all 3 pods aggregate into single metrics
HOSTNAME = os.getenv("HOSTNAME", "unknown_host")

app = FastAPI(title="Instrumentation Test API")
# Register Prometheus HTTP middlewares (order matters: last added = first executed)
app.add_middleware(GaugeMiddleware)
app.add_middleware(HistogramMiddleware)
app.add_middleware(CounterMiddleware)







def fetch_user_data(user_id: int, random_num: int = None):
    """Simulates fetching user data from a database"""
    reset_outcome()
    try:
        time.sleep(1.5)  # Simulate database latency
        # Silently mark failure if divisible by 2 (without raising)
        if random_num is not None and random_num % 2 == 0:
            mark_failure("fetch_user_data")
            return {"user_id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com", "note": "failed (divisible by 2)"}
        # Raise exception if random_num is divisible by 5
        if random_num is not None and random_num % 5 == 0:
            raise Exception(f"Random failure: number {random_num} is divisible by 5")
        result = {"user_id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"}
        mark_success("fetch_user_data")
        return result
    except Exception as e:
        mark_failure("fetch_user_data")
        raise


def fetch_posts(user_id: int):
    """Simulates fetching user posts"""
    reset_outcome()
    try:
        time.sleep(1.2)  # Simulate API latency
        result = [
            {"post_id": 1, "title": "First Post", "user_id": user_id},
            {"post_id": 2, "title": "Second Post", "user_id": user_id},
        ]
        mark_success("fetch_posts")
        return result
    except Exception as e:
        mark_failure("fetch_posts")
        raise


def process_analytics(data: dict):
    """Simulates processing analytics data"""
    reset_outcome()
    try:
        time.sleep(0.8)  # Simulate processing
        result = {"processed": True, "records": len(data)}
        mark_success("process_analytics")
        return result
    except Exception as e:
        mark_failure("process_analytics")
        raise


async def validate_data(user_id: int):
    """Async function simulating data validation"""
    reset_outcome()
    try:
        await asyncio.sleep(0.5)  # Simulate validation latency
        result = {"valid": True, "user_id": user_id}
        mark_success("validate_data")
        return result
    except Exception as e:
        mark_failure("validate_data")
        raise


def send_notification(message: str):
    """Simulates sending a notification"""
    reset_outcome()
    try:
        time.sleep(0.3)  # Simulate network latency
        result = {"sent": True, "message": message}
        mark_success("send_notification")
        return result
    except Exception as e:
        mark_failure("send_notification")
        raise


# ==================== PUBLIC API ENDPOINTS ====================

@app.post("/api/user-profile/{user_id}")
async def get_user_profile(user_id: int):
    """
    Main API endpoint that orchestrates multiple instrumented functions.
    This tests the @instrument decorator with various function types.
    """
    # Call synchronous instrumented function
    user_data = fetch_user_data(user_id)
    
    # Call another synchronous instrumented function
    posts = fetch_posts(user_id)
    
    # Call async instrumented function
    validation_result = await validate_data(user_id)
    
    # Process the data
    analytics = process_analytics({"posts": len(posts), "user_id": user_id})
    
    # Send notification
    notification = send_notification(f"Profile accessed for user {user_id}")
    
    return {
        "user": user_data,
        "posts": posts,
        "validation": validation_result,
        "analytics": analytics,
        "notification": notification,
    }


@app.get("/api/user/{user_id}")
def get_user(user_id: int):
    """Endpoint that simulates random failures and exceptions for testing instrumentation"""
    n = random.randint(1, 10)
    if n % 2 == 0:
        mark_failure("fetch_user_data")
    # Raise exception if divisible by 5
    if n % 5 == 0:
        raise Exception(f"Random failure: number {n} is divisible by 5")
    result = fetch_user_data(user_id, random_num=n)
    # Mark failure if divisible by 2
    
    return {"random_number": n, "result": result}


@app.get("/api/user/{user_id}/posts")
def get_user_posts(user_id: int):
    """Simple endpoint calling another instrumented function"""
    return fetch_posts(user_id)



@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Pushgateway background pusher
async def push_metrics_to_gateway():
    """Periodically push metrics to Prometheus Pushgateway"""
    while True:
        try:
            await asyncio.sleep(PUSH_INTERVAL)
            
            # Push the global REGISTRY - all 3 pods aggregate into single metrics
            # No instance label = metrics combine automatically
            push_to_gateway(
                PUSHGATEWAY_URL,
                job=JOB_NAME,
                registry=REGISTRY,
                grouping_key={'instance': HOSTNAME}
            )
            logger.info(f"Metrics pushed to {PUSHGATEWAY_URL}")
        except Exception as e:
            logger.error(f"Failed to push metrics to Pushgateway: {e}")
            pass


# Background task for pushing metrics to Pushgateway
push_task: asyncio.Task = None


@app.on_event("startup")
async def startup_event():
    """Start background task to push metrics to Pushgateway"""
    global push_task
    push_task = asyncio.create_task(push_metrics_to_gateway())
    logger.info(f"Started pushing metrics to Pushgateway at {PUSHGATEWAY_URL} (every {PUSH_INTERVAL}s)")


@app.on_event("shutdown")
async def shutdown_event():
    """Cancel background push task on shutdown"""
    global push_task
    if push_task:
        push_task.cancel()
    logger.info("Stopped pushing metrics to Pushgateway")


# ==================== SYNC FUNCTIONS (Using mark_success/mark_failure) ====================

def sync_database_query(user_id: int, should_fail: bool = False) -> dict:
    """Synchronous function that manually tracks success/failure"""
    reset_outcome()
    try:
        time.sleep(1.0)  # Simulate database query
        if should_fail:
            mark_failure("sync_database_query")
            return {"user_id": user_id, "status": "failed", "data": None}
        
        result = {"user_id": user_id, "name": f"Sync User {user_id}", "email": f"sync-user{user_id}@example.com"}
        mark_success("sync_database_query")
        return result
    except Exception as e:
        mark_failure("sync_database_query")
        raise


def sync_cache_operation(key: str, should_fail: bool = False) -> dict:
    """Synchronous cache operation with manual tracking"""
    reset_outcome()
    try:
        time.sleep(0.5)  # Simulate cache access
        if should_fail:
            mark_failure("sync_cache_operation")
            return {"key": key, "status": "cache_miss", "value": None}
        
        result = {"key": key, "value": f"cached_value_{key}"}
        mark_success("sync_cache_operation")
        return result
    except Exception as e:
        mark_failure("sync_cache_operation")
        raise


@app.get("/sync/test/{user_id}")
def test_sync_success(user_id: int):
    """Test synchronous function with success"""
    result = sync_database_query(int(user_id), should_fail=False)
    return {"endpoint": "/sync/test", "result": result}


@app.get("/sync/test-fail/{user_id}")
def test_sync_failure(user_id: int):
    """Test synchronous function with failure"""
    result = sync_database_query(int(user_id), should_fail=True)
    return {"endpoint": "/sync/test-fail", "result": result}


@app.get("/sync/cache/{key}")
def test_sync_cache_hit(key: str):
    """Test synchronous cache operation with hit"""
    result = sync_cache_operation(key, should_fail=False)
    return {"endpoint": "/sync/cache", "result": result}


@app.get("/sync/cache-miss/{key}")
def test_sync_cache_miss(key: str):
    """Test synchronous cache operation with miss"""
    result = sync_cache_operation(key, should_fail=True)
    return {"endpoint": "/sync/cache-miss", "result": result}


# ==================== ASYNC FUNCTIONS (Using mark_success/mark_failure) ====================

async def async_api_call(endpoint: str, should_fail: bool = False) -> dict:
    """Asynchronous API call with manual tracking"""
    reset_outcome()
    try:
        await asyncio.sleep(0.8)  # Simulate API latency
        if should_fail:
            mark_failure("async_api_call")
            return {"endpoint": endpoint, "status": "error", "data": None}
        
        result = {"endpoint": endpoint, "status": "ok", "data": {"response": f"Data from {endpoint}"}}
        mark_success("async_api_call")
        return result
    except Exception as e:
        mark_failure("async_api_call")
        raise


async def async_data_processing(data_id: int, should_fail: bool = False) -> dict:
    """Asynchronous data processing with manual tracking"""
    reset_outcome()
    try:
        await asyncio.sleep(1.2)  # Simulate processing
        if should_fail:
            mark_failure("async_data_processing")
            return {"data_id": data_id, "status": "processing_failed", "result": None}
        
        result = {"data_id": data_id, "status": "processed", "records_processed": random.randint(10, 100)}
        mark_success("async_data_processing")
        return result
    except Exception as e:
        mark_failure("async_data_processing")
        raise


async def async_concurrent_operations(count: int, fail_rate: float = 0.0) -> dict:
    """Run multiple async operations concurrently"""
    reset_outcome()
    try:
        tasks = []
        for i in range(count):
            should_fail = random.random() < fail_rate
            tasks.append(async_api_call(f"endpoint_{i}", should_fail=should_fail))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes and failures
        successes = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "ok")
        failures = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "error")
        
        if failures > 0:
            mark_failure("async_concurrent_operations")
        else:
            mark_success("async_concurrent_operations")
        
        return {"total": count, "successes": successes, "failures": failures, "results": results}
    except Exception as e:
        mark_failure("async_concurrent_operations")
        raise


@app.get("/async/api/{endpoint}")
async def test_async_api_success(endpoint: str):
    """Test asynchronous API call with success"""
    result = await async_api_call(endpoint, should_fail=False)
    return {"route": "/async/api", "result": result}


@app.get("/async/api-fail/{endpoint}")
async def test_async_api_failure(endpoint: str):
    """Test asynchronous API call with failure"""
    result = await async_api_call(endpoint, should_fail=True)
    return {"route": "/async/api-fail", "result": result}


@app.post("/async/process/{data_id}")
async def test_async_processing_success(data_id: int):
    """Test asynchronous data processing with success"""
    result = await async_data_processing(data_id, should_fail=False)
    return {"route": "/async/process", "result": result}


@app.post("/async/process-fail/{data_id}")
async def test_async_processing_failure(data_id: int):
    """Test asynchronous data processing with failure"""
    result = await async_data_processing(data_id, should_fail=True)
    return {"route": "/async/process-fail", "result": result}


@app.post("/async/concurrent/{count}")
async def test_async_concurrent(count: int, fail_rate: float = 0.0):
    """Test multiple async operations running concurrently"""
    result = await async_concurrent_operations(count, fail_rate=fail_rate)
    return {"route": "/async/concurrent", "count": count, "fail_rate": fail_rate, "result": result}


@app.get("/async/random-mix/{operations}")
async def test_async_random_mix(operations: int):
    """Test random mix of sync and async operations"""
    reset_outcome()
    try:
        sync_results = []
        async_results = []
        
        # Run sync operations
        for i in range(operations // 2):
            sync_result = sync_database_query(i, should_fail=(i % 3 == 0))
            sync_results.append(sync_result)
        
        # Run async operations concurrently
        async_tasks = [
            async_api_call(f"api_{i}", should_fail=(i % 4 == 0))
            for i in range(operations // 2)
        ]
        async_results = await asyncio.gather(*async_tasks)
        
        mark_success("async_random_mix")
        return {
            "route": "/async/random-mix",
            "total_operations": operations,
            "sync_results": sync_results,
            "async_results": async_results
        }
    except Exception as e:
        mark_failure("async_random_mix")
        raise


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

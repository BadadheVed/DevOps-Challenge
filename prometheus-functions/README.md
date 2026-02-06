# Prometheus Instrumentation Test Application

A FastAPI application designed to test the `@instrument` decorator for monitoring function execution with Prometheus metrics.

## Project Structure

- **main.py** - FastAPI application with instrumented endpoints
- **test_instrumentation.py** - Comprehensive test suite
- **prometheus/instrumentor.py** - The @instrument decorator (decorator under test)
- **prometheus/functions.py** - Prometheus metric definitions
- **prometheus/prometheus.py** - Prometheus registry setup

## What's Being Tested

The `@instrument` decorator provides:

- ✅ **Function call counting** - Track successful/failed calls
- ✅ **Execution duration** - Histogram of function execution times
- ✅ **In-flight tracking** - Gauge showing currently executing functions
- ✅ **Async support** - Works with both sync and async functions
- ✅ **Error handling** - Tracks failures and still raises exceptions

## Setup

### 1. Install Dependencies

```bash
cd prometheus-functions
pip install -e .
# or
pip install fastapi uvicorn prometheus-client
```

### 2. Start the FastAPI Server

```bash
python main.py
```

The server will start on `http://localhost:8000`

### 3. Run Tests

In another terminal:

```bash
python test_instrumentation.py
```

## API Endpoints

### Main Test Endpoint

```
POST /api/user-profile/{user_id}
```

- Calls 4 time-consuming instrumented functions sequentially
- Tests sync functions, async functions, error handling
- **Expected duration**: ~4 seconds (1.5s + 1.2s + 0.8s + 0.5s + 0.3s)

### Individual Function Tests

```
GET /api/user/{user_id}                    # Tests fetch_user_data (1.5s)
GET /api/user/{user_id}/posts              # Tests fetch_posts (1.2s)
GET /health                                # Health check
GET /metrics                               # Prometheus metrics
```

## Instrumented Functions

All these functions are decorated with `@instrument()`:

1. **fetch_user_data()** - Sync function, 1.5s delay
   - Simulates database query
   - Counter: tracks success/failure
   - Histogram: tracks execution time

2. **fetch_posts()** - Sync function, 1.2s delay
   - Simulates API call
   - Full instrumentation enabled

3. **process_analytics()** - Sync function, 0.8s delay
   - Simulates data processing
   - Full instrumentation enabled

4. **validate_data()** - Async function, 0.5s delay
   - Tests async decorator support
   - Tests async error handling

5. **send_notification()** - Sync function, 0.3s delay
   - Tests quick operations
   - Tests counter accuracy

## Testing the @instrument Decorator

### Test 1: Counter Metrics

```bash
curl http://localhost:8000/metrics | grep LLM_CALLS_total
```

Expected: Counters increment after each call with `status="success"` or `status="failure"`

### Test 2: Histogram (Duration)

```bash
curl http://localhost:8000/metrics | grep function_execution_seconds
```

Expected: Histogram buckets showing execution times

### Test 3: Gauge (In-Flight)

```bash
curl http://localhost:8000/metrics | grep LLM_IN_FLIGHT
```

Expected: Value increases during execution, decreases after completion

### Test 4: Async Support

Make requests to `/api/user-profile/{user_id}` - verify `validate_data` metrics appear

### Test 5: Error Tracking

Check metrics for both success and failure counts

## Example Test Session

```bash
# Terminal 1: Start server
$ python main.py
INFO:     Started server process [12345]
INFO:     Application startup complete

# Terminal 2: Run tests
$ python test_instrumentation.py
============================================================
  PROMETHEUS INSTRUMENTATION TEST SUITE
============================================================

✓ Server is running!

============================================================
  Testing: GET /health
============================================================
Status Code: 200
Response:
{
  "status": "healthy"
}

[... more test output ...]

============================================================
  Prometheus Metrics
============================================================
Raw Metrics (first 1500 chars):
# HELP LLM_CALLS_total Total function calls by function name and status
# TYPE LLM_CALLS_total counter
LLM_CALLS_total{function="fetch_user_data",status="success"} 3.0
LLM_CALLS_total{function="fetch_posts",status="success"} 3.0
...
```

## Metrics Explained

### LLM_CALLS_total (Counter)

```
LLM_CALLS_total{function="fetch_user_data",status="success"} 2.0
LLM_CALLS_total{function="fetch_user_data",status="failure"} 0.0
```

Counts total calls per function and status

### function_execution_seconds (Histogram)

```
function_execution_seconds_bucket{function="fetch_user_data",le="0.005"} 0.0
function_execution_seconds_bucket{function="fetch_user_data",le="0.01"} 0.0
...
function_execution_seconds_bucket{function="fetch_user_data",le="+Inf"} 2.0
function_execution_seconds_sum{function="fetch_user_data"} 3.1
function_execution_seconds_count{function="fetch_user_data"} 2.0
```

Measures execution duration in buckets

### LLM_IN_FLIGHT (Gauge)

```
LLM_IN_FLIGHT{function="fetch_user_data"} 0.0
```

Shows currently executing functions (increments at start, decrements at end)

## Advanced Testing

### Load Testing

```python
import concurrent.futures
import requests

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(requests.post, f"http://localhost:8000/api/user-profile/{i}")
        for i in range(10)
    ]
    results = [f.result() for f in futures]
```

### Custom Instrumentation

Add the decorator to your own functions:

```python
from prometheus.instrumentor import instrument

@instrument(name="my_function", counter=True, histogram=True)
def my_function():
    # Your code here
    pass
```

## Troubleshooting

### Port Already in Use

```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Metrics Not Showing

- Ensure you've called an instrumented endpoint first
- Check `/metrics` endpoint is accessible
- Verify imports in main.py are correct

### Async Function Errors

- Ensure endpoints that call async functions are also async
- Use `await` for async function calls

## Next Steps

1. ✅ Start the server: `python main.py`
2. ✅ Run tests: `python test_instrumentation.py`
3. ✅ Check metrics: `curl http://localhost:8000/metrics`
4. ✅ Verify counters increment and histograms populate
5. ✅ Test error scenarios (optional)

Enjoy testing your instrumentation! 🚀

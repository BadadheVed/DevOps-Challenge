# FastAPI Telemetry Application

Production-ready FastAPI app with OpenTelemetry integration for traces, metrics, and logs.

> **✅ Python 3.14+ Compatible** - Uses console exporters (no protobuf dependency)

## Features

- ✅ **OpenTelemetry Tracing** - Manual span creation with custom attributes
- ✅ **Custom Metrics** - HTTP request counters and duration histograms
- ✅ **Structured JSON Logging** - Includes trace_id and span_id
- ✅ **Console Exporters** - No protobuf, works on Python 3.14+
- ✅ **All Required Endpoints** - /hello, /normal, /error, /health, /antigravity
- ✅ **Exception Handling** - Full error tracing and logging

## Quick Start

```bash
# Clone/navigate to the app directory
cd /Users/ved/DevOps-Challenge/monitor/app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --host 0.0.0.0 --port 8000
```

Or use the quick start script:
```bash
./start.sh
```

## Test the Endpoints

```bash
# Hello endpoint (with antigravity reference)
curl http://localhost:8000/hello

# Normal processing (100-200ms delay)
curl http://localhost:8000/normal

# Error endpoint (raises exception)
curl http://localhost:8000/error

# Health check
curl http://localhost:8000/health

# Prometheus Metrics
curl http://localhost:8000/metrics

# Antigravity demo
curl http://localhost:8000/antigravity

# API documentation
open http://localhost:8000/docs
```

## Telemetry Output

### Traces
Detailed span information printed to console for every request, including:
- Request method, path, and status code
- Custom endpoint spans with attributes
- Processing duration
- Exception details (for errors)

### Metrics
Exported to console every 10 seconds:
- `http_requests_total` - Total requests by method/endpoint/status
- `http_request_duration_seconds` - Request latency histogram

### Logs
JSON formatted logs with trace context:
```json
{
  "asctime": "2026-01-20T09:26:00.123",
  "levelname": "INFO",
  "name": "main",
  "trace_id": "1a2b3c4d...",  
  "span_id": "9z8y7x6w...",
  "message": "Hello endpoint called"
}
```

## Production Deployment

For production with OTLP exporters sending to OpenTelemetry Collector:

1. **Add OTLP exporter to requirements.txt:**
   ```
   opentelemetry-exporter-otlp-proto-grpc==1.22.0
   ```

2. **Update `setup_telemetry()` in main.py** to use:
   ```python
   from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
   from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
   
   # Replace ConsoleSpanExporter with:
   OTLPSpanExporter(endpoint="otel-collector:4317", insecure=True)
   ```

3. **Note:** OTLP exporters require Python 3.9-3.13 (protobuf dependency)

## Dependencies

- `fastapi` - Web framework
- `uvicorn` - ASGI server  
- `opentelemetry-api` - Telemetry API
- `opentelemetry-sdk` - Telemetry SDK with console exporters
- `python-json-logger` - JSON logging

**✅ No protobuf dependency! Works on Python 3.14+**

## Docker Support

You can run the application in a Docker container (uses Python 3.11 for maximum compatibility).

### Build the Image

```bash
docker build -t fastapi-telemetry-app .
```

### Run the Container

```bash
docker run -p 8000:8000 fastapi-telemetry-app
```

The app will be available at http://localhost:8000

### Production Configuration (Docker)

To use OTLP exporters with a collector on the same network:

```bash
docker run -p 8000:8000 \
  -e OTEL_COLLECTOR_URL="host.docker.internal:4317" \
  fastapi-telemetry-app
```
*(Note: Use `host.docker.internal` to reach localhost from inside the container on Mac/Windows)*

## Architecture

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│   FastAPI Application       │
│   • Endpoint Handlers       │
│   • Manual Span Creation    │
│   • Custom Metrics          │
│   • JSON Logging            │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│  Console Exporters          │
│  • Traces → stdout          │
│  • Metrics → stdout         │
│  • Logs → stdout (JSON)     │
└─────────────────────────────┘
```

## Fun Feature

The app includes Python's `antigravity` module! Visit `/antigravity` endpoint to learn more. 🚀

---

**Status:** ✅ Complete and tested on Python 3.14  
**Telemetry:** Full tracing, metrics, and logging  
**Production Ready:** Yes (switch to OTLP exporters for production)

import os
import time
import random
import logging
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# OpenTelemetry imports
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from prometheus_client import make_asgi_app

# OpenTelemetry Logging imports
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry._logs import set_logger_provider

# JSON logging
from pythonjsonlogger import jsonlogger


# ============================================================================
# Configuration
# ============================================================================
SERVICE_NAME = "fastapi-telemetry-app"
SERVICE_VERSION = "1.0.0"


# ============================================================================
# OpenTelemetry Setup
# ============================================================================
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

def setup_telemetry():
    """Initialize OpenTelemetry providers for traces, metrics, and logs."""
    
    # Create resource with service information
    resource = Resource.create({
        "service.name": SERVICE_NAME,
        "service.version": SERVICE_VERSION,
    })
    
    # ========== Trace Provider ==========
    trace_provider = TracerProvider(resource=resource)
    
    # 1. Console Exporter - prints traces to stdout
    console_trace_exporter = ConsoleSpanExporter()
    trace_provider.add_span_processor(BatchSpanProcessor(console_trace_exporter))
    
    # 2. OTLP Exporter - sends traces to OTEL Collector -> Tempo
    otlp_trace_exporter = OTLPSpanExporter(
        endpoint="otel-collector.monitoring.svc.cluster.local:4317",
        insecure=True
    )
    trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
    
    trace.set_tracer_provider(trace_provider)
    
    # ========== Metric Provider ==========
    # 1. Console Exporter (for seeing metrics in logs)
    console_metric_exporter = ConsoleMetricExporter()
    console_reader = PeriodicExportingMetricReader(
        exporter=console_metric_exporter,
        export_interval_millis=150000,
    )
    
    # 2. Prometheus Exporter (for scraping at /metrics)
    prometheus_reader = PrometheusMetricReader()
    
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[console_reader, prometheus_reader],
    )
    metrics.set_meter_provider(meter_provider)
    
    # ========== Logs Provider ========== (THIS WAS MISSING!)
    logger_provider = LoggerProvider(resource=resource)
    
    # OTLP Log Exporter - sends logs to OTEL Collector -> Loki
    otlp_log_exporter = OTLPLogExporter(
        endpoint="otel-collector.monitoring.svc.cluster.local:4317",
        insecure=True
    )
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))
    set_logger_provider(logger_provider)
    
    print(f"✅ OpenTelemetry initialized for service: {SERVICE_NAME}")
    print(f"📊 Metrics: Console + Prometheus at /metrics")
    print(f"🔍 Traces: Console + OTLP to Tempo")
    print(f"📝 Logs: OTLP to Loki")
    print(f"✨ Full observability enabled!")


# ============================================================================
# Structured Logging Setup with Trace Context
# ============================================================================
class TraceContextFilter(logging.Filter):
    def filter(self, record):
        span = trace.get_current_span()
        span_context = span.get_span_context()
        
        if span_context.is_valid:
            record.trace_id = format(span_context.trace_id, "032x")
            record.span_id = format(span_context.span_id, "016x")
        else:
            record.trace_id = "0" * 32
            record.span_id = "0" * 16
        
        return True



def setup_logging():
    """Configure structured JSON logging with trace context and OTLP export."""
    
    # Create JSON formatter
    log_format = "%(asctime)s %(levelname)s %(name)s %(trace_id)s %(span_id)s %(message)s"
    json_formatter = jsonlogger.JsonFormatter(log_format)
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    console_handler.addFilter(TraceContextFilter())
    
    # OTLP handler - sends logs to OTEL Collector (THIS WAS MISSING!)
    from opentelemetry._logs import get_logger_provider
    otlp_handler = LoggingHandler(
        level=logging.INFO,
        logger_provider=get_logger_provider()
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)  # Console output
    root_logger.addHandler(otlp_handler)     # OTLP output -> Loki
    
    # Suppress uvicorn access logs to avoid duplication
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    print("✅ Structured JSON logging configured with trace context")
    print("✅ Logs will be sent to both Console and OTLP")

setup_telemetry()
setup_logging()

logger = logging.getLogger(__name__)

# Get tracer and meter for instrumentation
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Create custom metrics
request_counter = meter.create_counter(
    name="http_requests_total",
    description="Total HTTP requests",
    unit="1",
)

request_duration = meter.create_histogram(
    name="http_request_duration_seconds",
    description="HTTP request duration in seconds",
    unit="s",
)


# ============================================================================
# FastAPI Application
# ============================================================================
app = FastAPI(
    title="Telemetry-Enabled FastAPI App",
    description="Production-ready app with OpenTelemetry tracing, metrics, and logging",
    version="1.0.0",
)

# Note: Automatic instrumentation removed for Python 3.14 compatibility
# Manual instrumentation via middleware and manual spans provides full tracing

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# ============================================================================
# Middleware for Metrics
# ============================================================================
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """
    Record request metrics.
    Uses try/finally to ensure metrics are recorded even if an exception occurs.
    """
    start_time = time.time()
    status_code = 500  # Default to 500 if exception occurs
    
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        # If an exception occurs, we record it as a 500 and re-raise
        # effectively mimicking what the server would do
        status_code = 500
        raise
    finally:
        duration = time.time() - start_time
        
        # Record metrics
        request_counter.add(
            1,
            {
                "method": request.method,
                "endpoint": request.url.path,
                "status_code": status_code,
            }
        )
        
        request_duration.record(
            duration,
            {
                "method": request.method,
                "endpoint": request.url.path,
                "status_code": status_code,
            }
        )


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/hello")
async def hello() -> Dict[str, str]:
    """
    Returns a hello message.
    Demonstrates basic tracing and logging.
    """
    with tracer.start_as_current_span("hello-endpoint") as span:
        span.set_attribute("endpoint", "hello")
        
        logger.info("Hello endpoint called")
        
        # Fun: Mention that antigravity is loaded
        logger.info(f"Antigravity module loaded: {antigravity.__name__}")
        
        return {"message": "Hello from the telemetry-enabled app"}


@app.get("/normal")
async def normal() -> Dict[str, str]:
    """
    Simulates normal processing with a random delay.
    Adds custom span attributes and logs.
    """
    with tracer.start_as_current_span("normal-endpoint") as span:
        span.set_attribute("endpoint", "normal")
        
        logger.info("Normal endpoint - processing started")
        
        # Simulate processing time
        delay = random.uniform(0.1, 0.2)
        span.set_attribute("processing_delay_ms", delay * 1000)
        time.sleep(delay)
        
        logger.info(f"Normal endpoint - processing completed in {delay:.3f}s")
        
        return {
            "message": "Normal processing completed",
            "processing_time_ms": f"{delay * 1000:.2f}",
        }


@app.get("/error")
async def error() -> None:
    """
    Intentionally raises an exception.
    Demonstrates error tracing and logging.
    """
    with tracer.start_as_current_span("error-endpoint") as span:
        span.set_attribute("endpoint", "error")
        
        logger.error("Error endpoint called - about to raise exception")
        
        try:
            raise ValueError("This is an intentional error for testing!")
        except Exception as e:
            # Record exception in span
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            
            logger.exception("Exception occurred in error endpoint")
            
            # Re-raise to let FastAPI handle it
            raise


@app.get("/health")
async def health() -> Dict[str, str]:
    """
    Health check endpoint.
    Minimal logic, no heavy tracing.
    """
    return {"status": "ok"}


@app.get("/antigravity")
async def antigravity_demo() -> Dict[str, str]:
    """
    Demonstrates the antigravity module.
    The module itself opens a web browser to XKCD comic when imported,
    so we just confirm it's available.
    """
    with tracer.start_as_current_span("antigravity-endpoint") as span:
        span.set_attribute("endpoint", "antigravity")
        
        logger.info(f"Antigravity module is available: {antigravity.__doc__}")
        
        return {
            "message": "The antigravity module is loaded!",
            "module": antigravity.__name__,
            "info": "In Python, 'import antigravity' opens XKCD #353",
        }


# ============================================================================
# Exception Handler
# ============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.exception(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "path": request.url.path,
        }
    )


# ============================================================================
# Startup and Shutdown Events
# ============================================================================
@app.on_event("startup")
async def startup_event():
    """Application startup handler."""
    logger.info(f"🚀 {SERVICE_NAME} v{SERVICE_VERSION} starting up")
    logger.info(f"📊 Telemetry enabled with Console Exporters")
    logger.info(f"🐍 Python 3.14+ compatible (no protobuf dependency)")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown handler."""
    logger.info(f"🛑 {SERVICE_NAME} shutting down")


# ============================================================================
# Main Entry Point
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )

import os
import time
import random
import logging
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from prometheus_client import make_asgi_app

from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry._logs import set_logger_provider

from pythonjsonlogger import jsonlogger
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


SERVICE_NAME = "fastapi-telemetry-app"
SERVICE_VERSION = "1.0.0"
ALLOY_ENDPOINT = os.getenv("ALLOY_ENDPOINT", "alloy.monitoring.svc.cluster.local:4317")


def setup_telemetry():
    resource = Resource.create({
        "service.name": SERVICE_NAME,
        "service.version": SERVICE_VERSION,
    })
    
    trace_provider = TracerProvider(resource=resource)
    
    console_trace_exporter = ConsoleSpanExporter()
    trace_provider.add_span_processor(BatchSpanProcessor(console_trace_exporter))
    
    otlp_trace_exporter = OTLPSpanExporter(
        endpoint=ALLOY_ENDPOINT,
        insecure=True
    )
    trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
    
    trace.set_tracer_provider(trace_provider)
    
    console_metric_exporter = ConsoleMetricExporter()
    console_reader = PeriodicExportingMetricReader(
        exporter=console_metric_exporter,
        export_interval_millis=10000,
    )
    
    prometheus_reader = PrometheusMetricReader()
    
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[console_reader, prometheus_reader],
    )
    metrics.set_meter_provider(meter_provider)
    
    logger_provider = LoggerProvider(resource=resource)
    
    otlp_log_exporter = OTLPLogExporter(
        endpoint=ALLOY_ENDPOINT,
        insecure=True
    )
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))
    set_logger_provider(logger_provider)
    
    print(f"✅ OpenTelemetry initialized - sending to Alloy at {ALLOY_ENDPOINT}")


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
    log_format = "%(asctime)s %(levelname)s %(name)s %(trace_id)s %(span_id)s %(message)s"
    json_formatter = jsonlogger.JsonFormatter(log_format)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    console_handler.addFilter(TraceContextFilter())
    
    from opentelemetry._logs import get_logger_provider
    otlp_handler = LoggingHandler(
        level=logging.INFO,
        logger_provider=get_logger_provider()
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(otlp_handler)
    
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    print("✅ Structured JSON logging configured with trace context")


setup_telemetry()
setup_logging()

logger = logging.getLogger(__name__)

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

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


app = FastAPI(
    title="Telemetry-Enabled FastAPI App",
    description="Production-ready app with OpenTelemetry + Grafana Alloy",
    version="1.0.0",
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    status_code = 500
    
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        status_code = 500
        raise
    finally:
        duration = time.time() - start_time
        
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


@app.get("/hello")
async def hello() -> Dict[str, str]:
    with tracer.start_as_current_span("hello-endpoint") as span:
        span.set_attribute("endpoint", "hello")
        span.set_status(trace.Status(trace.StatusCode.OK, "Hello processing completed"))
        logger.info("Hello endpoint called")
        
        return {"message": "Hello from the telemetry-enabled app"}


@app.get("/normal")
async def normal() -> Dict[str, str]:
    with tracer.start_as_current_span("normal-endpoint") as span:
        span.set_attribute("endpoint", "normal")
        span.set_status(trace.Status(trace.StatusCode.OK, "Normal processing completed"))
        logger.info("Normal endpoint - processing started")
        logger.info("this is the 2nd trace")
        logger.info("this is the 3rd trace")
        logger.info("this is the 4th trace")
        logger.info("this is the 5th trace")
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
    with tracer.start_as_current_span("error-endpoint") as span:
        span.set_attribute("endpoint", "error")
        
        logger.error("Error endpoint called - about to raise exception")
        
        try:
            span.set_status(trace.Status(trace.StatusCode.ERROR, "error processing completed"))
            raise ValueError("This is an intentional error for testing!")
           
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            
            logger.exception("Exception occurred in error endpoint")
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Error processing completed"))
            raise


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "path": request.url.path,
        }
    )


@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 {SERVICE_NAME} v{SERVICE_VERSION} starting up")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"🛑 {SERVICE_NAME} shutting down")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
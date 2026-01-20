# FastAPI Observability Stack - Complete Setup Guide

Full observability for FastAPI applications in Kubernetes with distributed tracing, logs, and metrics.

## 📊 Stack Overview

| Component | Purpose | Port |
|-----------|---------|------|
| **OpenTelemetry** | Instrumentation & data collection | - |
| **OTEL Collector** | Telemetry data router | 4317 (gRPC), 4318 (HTTP) |
| **Tempo** | Distributed tracing backend | 4317, 3200 |
| **Loki** | Log aggregation | 3100 |
| **Prometheus** | Metrics collection | 9090 |
| **Grafana** | Unified visualization | 3000 |

## 🏗️ Architecture

```
FastAPI App (3 Pods)
    ├─ Traces → OTLP → OTEL Collector → Tempo → Grafana
    ├─ Logs   → OTLP → OTEL Collector → Loki → Grafana
    └─ Metrics → Prometheus (scrapes /metrics) → Grafana
```

---

## 🚀 Quick Start

### Prerequisites

- Kubernetes cluster (v1.20+)
- `kubectl` configured
- `helm` (v3+)
- Docker for building images

---

## 📦 Installation

### Step 1: Create Namespace

```bash
kubectl create namespace monitoring
```

---

### Step 2: Add Helm Repositories

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update
```

---

### Step 3: Install Loki (Logs)

```bash
helm install loki grafana/loki-distributed \
  --namespace monitoring \
  --set distributor.replicas=2 \
  --set ingester.replicas=2 \
  --set querier.replicas=2 \
  --set queryFrontend.replicas=2 \
  --set gateway.enabled=true \
  --set persistence.enabled=true \
  --set persistence.size=20Gi \
  --set persistence.storageClassName=gp2
```

---

### Step 4: Install Tempo (Traces)

```bash
helm install tempo grafana/tempo \
  --namespace monitoring \
  --set tempo.receivers.otlp.protocols.grpc.endpoint="0.0.0.0:4317" \
  --set tempo.receivers.otlp.protocols.http.endpoint="0.0.0.0:4318"
```

---

### Step 5: Install Prometheus (Metrics)

```bash
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring
```

---

### Step 6: Install OTEL Collector

Create `otel-values.yaml`:

```yaml
nameOverride: "otel-collector"
fullnameOverride: "otel-collector"

mode: deployment

image:
  repository: "otel/opentelemetry-collector-contrib"
  tag: "0.93.0"
  pullPolicy: IfNotPresent

config:
  receivers:
    otlp:
      protocols:
        http: {}
        grpc: {}

  processors:
    batch: {}
    memory_limiter:
      check_interval: 5s
      limit_percentage: 80
      spike_limit_percentage: 25

  exporters:
    otlp/tempo:
      endpoint: tempo.monitoring.svc.cluster.local:4317
      tls:
        insecure: true

    loki:
      endpoint: http://loki-loki-distributed-gateway.monitoring.svc.cluster.local:80/loki/api/v1/push
      retry_on_failure:
        enabled: true
        initial_interval: 5s
        max_interval: 30s
        max_elapsed_time: 300s
      timeout: 10s

    debug:
      verbosity: detailed

  service:
    telemetry:
      logs:
        level: debug
      metrics:
        address: "0.0.0.0:8889"

    pipelines:
      metrics:
        receivers: [otlp]
        processors: [memory_limiter, batch]
        exporters: [debug]

      traces:
        receivers: [otlp]
        processors: [memory_limiter, batch]
        exporters: [otlp/tempo, debug]

      logs:
        receivers: [otlp]
        processors: [memory_limiter, batch]
        exporters: [loki, debug]
```

Install:

```bash
helm install otel-collector open-telemetry/opentelemetry-collector \
  -n monitoring \
  -f otel-values.yaml
```

---

### Step 7: Verify Installation

```bash
kubectl get pods -n monitoring
```

All pods should be `Running`.

---

## 💻 Application Setup

### Step 1: Install Python Dependencies

```bash
pip install fastapi uvicorn \
  opentelemetry-api \
  opentelemetry-sdk \
  opentelemetry-exporter-otlp-proto-grpc \
  opentelemetry-exporter-prometheus \
  prometheus-client \
  python-json-logger
```

Create `requirements.txt`:

```txt
fastapi
uvicorn
opentelemetry-api
opentelemetry-sdk
opentelemetry-exporter-otlp-proto-grpc
opentelemetry-exporter-prometheus
prometheus-client
python-json-logger
```

---

### Step 2: Create `main.py`

```python
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
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from prometheus_client import make_asgi_app

# OpenTelemetry Logging imports
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry._logs import set_logger_provider, get_logger_provider

# JSON logging
from pythonjsonlogger import jsonlogger

# Configuration
SERVICE_NAME = "fastapi-telemetry-app"
SERVICE_VERSION = "1.0.0"
OTEL_ENDPOINT = "otel-collector.monitoring.svc.cluster.local:4317"

def setup_telemetry():
    """Initialize OpenTelemetry for traces, metrics, and logs."""
    
    resource = Resource.create({
        "service.name": SERVICE_NAME,
        "service.version": SERVICE_VERSION,
    })
    
    # Traces
    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace_provider.add_span_processor(BatchSpanProcessor(
        OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)
    ))
    trace.set_tracer_provider(trace_provider)
    
    # Metrics
    prometheus_reader = PrometheusMetricReader()
    meter_provider = MeterProvider(resource=resource, metric_readers=[prometheus_reader])
    metrics.set_meter_provider(meter_provider)
    
    # Logs
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(
        OTLPLogExporter(endpoint=OTEL_ENDPOINT, insecure=True)
    ))
    set_logger_provider(logger_provider)
    
    print(f"✅ OpenTelemetry initialized: Traces, Metrics, Logs")

def setup_logging():
    """Configure structured logging with OTLP export."""
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(jsonlogger.JsonFormatter())
    
    # OTLP handler
    otlp_handler = LoggingHandler(
        level=logging.INFO,
        logger_provider=get_logger_provider()
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(otlp_handler)
    
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# Initialize
setup_telemetry()
setup_logging()

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Create metrics
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

# FastAPI app
app = FastAPI(
    title="Telemetry-Enabled FastAPI App",
    version="1.0.0",
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Middleware for metrics
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
        request_counter.add(1, {
            "method": request.method,
            "endpoint": request.url.path,
            "status_code": status_code,
        })
        request_duration.record(duration, {
            "method": request.method,
            "endpoint": request.url.path,
        })

# Endpoints
@app.get("/hello")
async def hello() -> Dict[str, str]:
    with tracer.start_as_current_span("hello-endpoint") as span:
        span.set_attribute("endpoint", "hello")
        logger.info("Hello endpoint called")
        return {"message": "Hello from telemetry-enabled app"}

@app.get("/normal")
async def normal() -> Dict[str, str]:
    with tracer.start_as_current_span("normal-endpoint") as span:
        span.set_attribute("endpoint", "normal")
        logger.info("Normal endpoint - processing started")
        
        delay = random.uniform(0.1, 0.2)
        span.set_attribute("processing_delay_ms", delay * 1000)
        time.sleep(delay)
        
        logger.info(f"Normal endpoint - completed in {delay:.3f}s")
        return {
            "message": "Normal processing completed",
            "processing_time_ms": f"{delay * 1000:.2f}",
        }

@app.get("/error")
async def error() -> None:
    with tracer.start_as_current_span("error-endpoint") as span:
        span.set_attribute("endpoint", "error")
        logger.error("Error endpoint called")
        
        try:
            raise ValueError("Intentional error for testing")
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            logger.exception("Exception occurred")
            raise

@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
```

---

### Step 3: Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### Step 4: Build and Push Docker Image

```bash
docker build -t your-registry/fastapi-app:latest .
docker push your-registry/fastapi-app:latest
```

---

### Step 5: Deploy to Kubernetes

Create `deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: app
        image: your-registry/fastapi-app:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "otel-collector.monitoring.svc.cluster.local:4317"
        - name: OTEL_SERVICE_NAME
          value: "fastapi-telemetry-app"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-app
  namespace: default
  labels:
    app: fastapi-app
spec:
  selector:
    app: fastapi-app
  ports:
  - name: http
    port: 8000
    targetPort: 8000
  type: LoadBalancer  # or ClusterIP
```

Deploy:

```bash
kubectl apply -f deployment.yaml
```

---

### Step 6: Create ServiceMonitor for Prometheus

Create `servicemonitor.yaml`:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: fastapi-app-sm
  namespace: monitoring
  labels:
    release: monitoring
spec:
  jobLabel: app
  selector:
    matchLabels:
      app: fastapi-app
  namespaceSelector:
    matchNames:
      - default
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```

Deploy:

```bash
kubectl apply -f servicemonitor.yaml
```

---

## 🔍 Verification

### Check All Pods

```bash
kubectl get pods -n monitoring
kubectl get pods -n default -l app=fastapi-app
```

### Access Grafana

```bash
# Get Grafana password
kubectl get secret -n monitoring monitoring-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode
echo

# Port forward
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
```

Open: `http://localhost:3000`
- Username: `admin`
- Password: (from command above)

---

### Configure Grafana Data Sources

**Add Tempo:**
1. Connections → Data Sources → Add data source
2. Select **Tempo**
3. URL: `http://tempo.monitoring.svc.cluster.local:3200`
4. Save & Test

**Add Loki:**
1. Connections → Data Sources → Add data source
2. Select **Loki**
3. URL: `http://loki-loki-distributed-gateway.monitoring.svc.cluster.local`
4. Save & Test

**Prometheus** should already be configured.

---

## 📊 Usage

### Generate Test Traffic

```bash
# Get LoadBalancer URL
kubectl get svc -n default fastapi-app

# Or port forward
kubectl port-forward -n default svc/fastapi-app 8080:8000

# Generate traffic
curl http://localhost:8080/hello
curl http://localhost:8080/normal
curl http://localhost:8080/error
```

---

### View Logs in Grafana

1. Go to **Explore**
2. Select **Loki**
3. Query:
   ```logql
   {exporter="OTLP"}
   ```
4. Click **Run Query**

**Other useful queries:**

```logql
# By service
{exporter="OTLP", service_name="fastapi-telemetry-app"}

# Error logs only
{exporter="OTLP"} |= "ERROR"

# Specific endpoint
{exporter="OTLP"} |= "Normal endpoint"

# By trace ID
{exporter="OTLP"} | json | trace_id="<trace-id>"
```

---

### View Traces in Grafana

1. Go to **Explore**
2. Select **Tempo**
3. Click **Search**
4. Service: `fastapi-telemetry-app`
5. Click **Run Query**

**Connect Traces to Logs:**
- Click on a trace
- Click **"Logs for this trace"** button
- See all logs from that request with matching trace_id

---

### View Metrics in Grafana

1. Go to **Explore**
2. Select **Prometheus**

**Useful queries:**

```promql
# Request rate
rate(http_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Requests by endpoint
sum by (endpoint) (http_requests_total)

# Error rate
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
```

---

## 🐛 Troubleshooting

### No traces in Tempo

```bash
# Check OTEL Collector logs
kubectl logs -n monitoring -l app.kubernetes.io/name=otel-collector --tail=100

# Restart OTEL Collector
kubectl rollout restart deployment/otel-collector -n monitoring

# Restart app
kubectl rollout restart deployment/fastapi-app -n default
```

---

### No logs in Loki

```bash
# Check if logs are reaching OTEL Collector
kubectl logs -n monitoring -l app.kubernetes.io/name=otel-collector --tail=100 | grep LogsExporter

# Check Loki distributor
kubectl logs -n monitoring -l app.kubernetes.io/name=loki,app.kubernetes.io/component=distributor

# In Grafana, try query: {exporter="OTLP"}
```

---

### Prometheus not scraping metrics

```bash
# Check ServiceMonitor exists
kubectl get servicemonitor -n monitoring

# Port forward Prometheus and check targets
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090

# Open http://localhost:9090/targets
# Look for "fastapi-app"
```

---

## 📝 Key Points

### Logs
- Use `logger.info()`, `logger.error()`, etc.
- Never use `print()` - it doesn't send to OTLP
- Logs automatically include trace_id and span_id

### Traces
- Use `with tracer.start_as_current_span()` for custom spans
- Add attributes with `span.set_attribute()`
- Traces show request flow and timing

### Metrics
- Custom metrics: `meter.create_counter()`, `meter.create_histogram()`
- Exposed at `/metrics` endpoint
- Prometheus scrapes automatically via ServiceMonitor

---

## 🎯 Best Practices

1. **Use structured logging** - JSON format with trace context
2. **Add meaningful span attributes** - For better trace filtering
3. **Set appropriate log levels** - INFO for production, DEBUG for dev
4. **Monitor OTEL Collector health** - Check for export failures
5. **Configure retention policies** - In Tempo/Loki to manage storage
6. **Use sampling in production** - Sample 10-20% of traces for high-traffic apps
7. **Create Grafana dashboards** - For common queries and metrics

---

## 📚 Useful Queries Reference

### Loki (Logs)

```logql
# All app logs
{exporter="OTLP", service_name="fastapi-telemetry-app"}

# Errors only
{exporter="OTLP"} |= "ERROR"

# Slow requests (>1s)
{exporter="OTLP"} | json | duration > 1

# Specific trace
{exporter="OTLP"} | json | trace_id="abc123..."
```

### Tempo (Traces)

Search by:
- Service name: `fastapi-telemetry-app`
- Operation: `normal-endpoint`
- Duration: `> 100ms`
- Status: `error`

### Prometheus (Metrics)

```promql
# Request rate
rate(http_requests_total[5m])

# Latency percentiles
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
sum(rate(http_requests_total{status_code=~"5.."}[5m])) 
/ 
sum(rate(http_requests_total[5m]))

# Requests by endpoint
sum by (endpoint) (rate(http_requests_total[5m]))
```

---

## 🔗 Resources

- [OpenTelemetry Python Docs](https://opentelemetry.io/docs/languages/python/)
- [Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)

---

## ✅ Success Checklist

- [ ] All pods running in `monitoring` namespace
- [ ] FastAPI app deployed with 3 replicas
- [ ] Grafana accessible at `http://localhost:3000`
- [ ] Tempo data source configured and tested
- [ ] Loki data source configured and tested
- [ ] Prometheus data source configured
- [ ] Logs visible in Loki with query `{exporter="OTLP"}`
- [ ] Traces visible in Tempo
- [ ] Metrics visible in Prometheus
- [ ] Trace-to-log correlation working

---

**🎉 Congratulations! You now have full observability for your FastAPI application!**

For questions or issues, check the troubleshooting section or review the component logs.
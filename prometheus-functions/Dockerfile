# Stage 1: Builder
FROM python:3.14-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml pyproject.toml
COPY . .

RUN uv pip install --python /usr/local/bin/python3.14 --break-system-packages -e .


# Stage 2: Runtime
FROM python:3.14-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi>=0.128.0 \
    uvicorn[standard]>=0.30.0 \
    prometheus-client>=0.24.1

COPY --from=builder /app .

EXPOSE 8000

# Health check against /health endpoint (no longer /metrics)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Environment variables for Pushgateway (can be overridden at runtime)
ENV PUSHGATEWAY_URL="http://pushgateway-prometheus-pushgateway.monitoring.svc.cluster.local:9091" \
    PUSH_INTERVAL="15" \
    JOB_NAME="prometheus-functions"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

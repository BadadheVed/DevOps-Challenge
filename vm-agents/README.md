# VM-Agents Helm Chart

A Helm chart for deploying the VM-Agents monitoring application with Prometheus metrics, OpenTelemetry support, and annotation-driven configuration.

## Overview

This Helm chart deploys a FastAPI-based monitoring application that exposes Prometheus metrics and supports OpenTelemetry instrumentation. The application integrates with Grafana Alloy for metrics collection and Victoria Metrics for storage.

## Features

- **Annotation-Driven Configuration**: Pod annotations and labels automatically extracted by Alloy
- **Prometheus Metrics**: Built-in metrics endpoint with HTTP middleware instrumentation
- **OpenTelemetry Support**: OTEL traces and metrics via Alloy endpoint
- **Advanced Alloy Integration**: Automatic pod discovery with annotation-based service metadata
- **TLS Ingress**: Automatic certificate management via cert-manager
- **Security**: Metrics endpoint blocked externally, accessible only by Alloy
- **Horizontal Pod Autoscaling**: Optional HPA based on CPU/memory
- **Production-Ready**: Security contexts, resource limits, health checks

## Prerequisites

- Kubernetes 1.20+
- Helm 3.0+
- cert-manager installed (for TLS certificates)
- nginx-ingress-controller deployed
- Grafana Alloy deployed in monitoring namespace
- Victoria Metrics vmagent deployed in monitoring namespace

## Installation

### Quick Install

```bash
helm install vm-agents ./vm-agents --namespace default
```

### Custom Values

```bash
helm install vm-agents ./vm-agents \
  --namespace default \
  --values custom-values.yaml
```

### Upgrade

```bash
helm upgrade vm-agents ./vm-agents \
  --namespace default \
  --values values.yaml
```

## Configuration

### Application Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `3` |
| `image.repository` | Container image repository | `ved104/prom-functions` |
| `image.tag` | Container image tag | `latest` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |

### Environment Variables

| Parameter | Description | Default |
|-----------|-------------|---------|
| `env.pushgatewayUrl` | Prometheus Pushgateway URL | `http://pushgateway-prometheus-pushgateway.monitoring.svc.cluster.local:9091` |
| `env.pushInterval` | Push interval in seconds | `15` |
| `env.jobName` | Job name for metrics | `prometheus-functions` |
| `env.alloyEndpoint` | Alloy OTLP endpoint | `alloy.monitoring.svc.cluster.local:4317` |
| `env.otelServiceName` | OpenTelemetry service name | `fastapi-telemetry-app` |

### Pod Annotations (Annotation-Driven)

| Annotation | Description | Default |
|------------|-------------|---------|
| `prometheus.io/scrape` | Enable Prometheus scraping | `true` |
| `prometheus.io/port` | Metrics port | `8000` |
| `prometheus.io/path` | Metrics path | `/metrics` |
| `resource.opentelemetry.io/service.name` | OTEL service name | `fastapi-telemetry-app` |
| `resource.opentelemetry.io/service.namespace` | OTEL service namespace | `default` |

### Service Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `8000` |
| `service.annotations` | Service annotations | `{}` |

### Ingress Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.hosts[0].host` | Ingress hostname | `workers.vedcsn.com` |
| `ingress.tls[0].secretName` | TLS secret name | `workers-vedcsn-tls` |

The ingress automatically blocks external access to `/metrics` endpoint via server snippet.

### Alloy Configuration (Advanced Pattern)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `alloy.enabled` | Enable Alloy ConfigMap creation | `true` |
| `alloy.namespace` | Alloy namespace | `monitoring` |
| `alloy.clusterName` | Kubernetes cluster name | `neo-k8s` |
| `alloy.discovery.namespaces` | Namespaces to discover pods | `["default", "monitoring"]` |
| `alloy.discovery.podLabelSelector` | Pod label selector | `vm-agents-deploy` |
| `alloy.scrape.interval` | Scrape interval | `15s` |
| `alloy.scrape.timeout` | Scrape timeout | `10s` |
| `alloy.metricsPath` | Metrics endpoint path | `/metrics` |
| `alloy.clustering.enabled` | Enable Alloy clustering | `true` |
| `alloy.exporters.vmagent.url` | VictoriaMetrics agent URL | `http://vmagent.monitoring.svc.cluster.local:8429/api/v1/write` |

### Resource Limits

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `512Mi` |
| `resources.requests.cpu` | CPU request | `250m` |
| `resources.requests.memory` | Memory request | `256Mi` |

### Autoscaling

| Parameter | Description | Default |
|-----------|-------------|---------|
| `autoscaling.enabled` | Enable HPA | `false` |
| `autoscaling.minReplicas` | Minimum replicas | `3` |
| `autoscaling.maxReplicas` | Maximum replicas | `10` |
| `autoscaling.targetCPUUtilizationPercentage` | Target CPU % | `80` |

## Architecture

### Data Flow

1. **Application Pods**: Expose metrics on `/metrics` endpoint (port 8000)
2. **Alloy Discovery**: Discovers pods via Kubernetes API using label selector
3. **Annotation Extraction**: Alloy extracts service metadata from pod annotations
4. **Metrics Scraping**: Alloy scrapes metrics every 15 seconds
5. **Remote Write**: Alloy forwards metrics to vmagent
6. **Storage**: vmagent stores metrics in Victoria Metrics

### Annotation-Driven Features

The chart supports comprehensive annotation-driven configuration:

- **Service Name**: Extracted from `resource.opentelemetry.io/service.name` or falls back to pod label `app.kubernetes.io/name`
- **Service Namespace**: Extracted from `resource.opentelemetry.io/service.namespace` or pod namespace
- **Service Instance ID**: Extracted from `resource.opentelemetry.io/service.instance.id` or generated from pod metadata
- **Custom Labels**: All pod annotations are mapped as labels via `labelmap` rules

### Security

- **Pod Security**: Runs as non-root user (UID 1000)
- **Capabilities**: Drops all capabilities
- **Ingress Security**: `/metrics` endpoint blocked externally via nginx server snippet
- **Internal Access**: Metrics accessible only from monitoring namespace via Alloy
- **TLS**: Automatic certificate management via cert-manager

## Usage Examples

### Basic Deployment

```bash
helm install vm-agents ./vm-agents
```

### Custom Image Tag

```bash
helm install vm-agents ./vm-agents \
  --set image.tag=v2.0.0
```

### Enable Autoscaling

```bash
helm install vm-agents ./vm-agents \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=5 \
  --set autoscaling.maxReplicas=20
```

### Custom Alloy Configuration

```bash
helm install vm-agents ./vm-agents \
  --set alloy.scrape.interval=30s \
  --set alloy.exporters.vmagent.externalLabels.environment=staging
```

### Different Ingress Host

```bash
helm install vm-agents ./vm-agents \
  --set ingress.hosts[0].host=myapp.example.com \
  --set ingress.tls[0].hosts[0]=myapp.example.com \
  --set ingress.tls[0].secretName=myapp-tls
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -l app.kubernetes.io/name=vm-agents

# View pod logs
kubectl logs -l app.kubernetes.io/name=vm-agents --tail=100

# Describe pod for events
kubectl describe pod <pod-name>
```

### Metrics Not Scraped

```bash
# Check Alloy logs
kubectl logs -n monitoring -l app=alloy --tail=50

# Verify Alloy ConfigMap
kubectl get configmap -n monitoring <release-name>-vm-agents-alloy -o yaml

# Check if pods are discovered
kubectl port-forward -n monitoring svc/alloy 12345:12345
# Visit http://localhost:12345/targets
```

### Ingress Not Working

```bash
# Check ingress status
kubectl get ingress

# Verify ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller

# Check certificate
kubectl get certificate
kubectl describe certificate workers-vedcsn-tls
```

### Health Checks Failing

The application expects `/health` endpoint. If using custom health check paths:

```bash
helm upgrade vm-agents ./vm-agents \
  --set livenessProbe.httpGet.path=/healthz \
  --set readinessProbe.httpGet.path=/ready
```

## Monitoring

### Verify Metrics

```bash
# Port forward to application
kubectl port-forward svc/vm-agents 8080:8000

# Check metrics endpoint (only works internally)
curl http://localhost:8080/metrics
```

### Check vmagent

```bash
# Port forward to vmagent
kubectl port-forward -n monitoring svc/vmagent 8429:8429

# Check vmagent UI
open http://localhost:8429/targets
```

## Uninstallation

```bash
helm uninstall vm-agents --namespace default
```

## Contributing

For bug reports and feature requests, please create an issue.

## License

Copyright © 2024 DevOps Team

"""Global Prometheus registry shared across all processes (API, consumers, etc)"""

from prometheus_client import CollectorRegistry

# Single global registry instance - ALL modules must import and use this
GLOBAL_REGISTRY = CollectorRegistry()

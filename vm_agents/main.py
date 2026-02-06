import time
import asyncio
import logging
import random
from prometheus_client import Counter, CollectorRegistry, start_http_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Each pod gets its own registry (not shared/global)
REGISTRY = CollectorRegistry()

# Define metrics on this pod's registry
POD_CALLS = Counter(
    'vm_agent_calls_total',
    'Total VM agent function calls by status',
    ['status'],
    registry=REGISTRY
)

# Function to mark success/failure
def mark_success(operation: str = "vm_operation"):
    """Mark a successful operation"""
    try:
        POD_CALLS.labels(status="success").inc()
        logger.info(f"✓ {operation} succeeded")
    except Exception as e:
        logger.error(f"Failed to mark success: {e}")

def mark_failure(operation: str = "vm_operation"):
    """Mark a failed operation"""
    try:
        POD_CALLS.labels(status="failure").inc()
        logger.error(f"✗ {operation} failed")
    except Exception as e:
        logger.error(f"Failed to mark failure: {e}")

# Background worker - continuously calls mark_success/mark_failure
async def worker_loop():
    """Simulates VM agent work - calls success/failure randomly"""
    operations = [
        "vm_deployment",
        "resource_provisioning",
        "health_check",
        "scaling_action",
        "backup_task"
    ]
    
    while True:
        try:
            await asyncio.sleep(random.uniform(1, 3))  # Random interval between 1-3 seconds
            
            operation = random.choice(operations)
            # 70% success rate, 30% failure rate
            if random.random() < 0.7:
                mark_success(operation)
            else:
                mark_failure(operation)
                
        except Exception as e:
            logger.error(f"Worker loop error: {e}")

async def main():
    """Start Prometheus HTTP server and worker loop"""
    # Start Prometheus HTTP server on port 8000
    # This exposes /metrics endpoint automatically
    start_http_server(8000, registry=REGISTRY)
    logger.info("Prometheus metrics server started on port 8000 - /metrics endpoint ready")
    
    # Start worker loop
    await worker_loop()

if __name__ == "__main__":
    asyncio.run(main())


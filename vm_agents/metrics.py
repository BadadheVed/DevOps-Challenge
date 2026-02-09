import logging
import random
import asyncio
from prometheus_client import Counter, CollectorRegistry

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

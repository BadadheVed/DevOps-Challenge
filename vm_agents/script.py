"""
Test script using ISOLATED registries (not shared)
Each instance creates its own registry on startup
"""
import logging
import random
import time
import sys
import argparse
from prometheus_client import Counter, Histogram, CollectorRegistry, start_http_server

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_isolated_registry(instance_id: int, port: int):
    """Create a NEW isolated registry for this instance (not shared)"""
    # NEW registry - each instance has its own
    registry = CollectorRegistry()
    
    # Define metrics on THIS instance's registry
    instance_counter = Counter(
        'script_operations_total',
        'Script operations using ISOLATED registry',
        ['instance_id', 'operation', 'result'],
        registry=registry
    )
    
    instance_histogram = Histogram(
        'script_operation_duration_seconds',
        'Script operation duration',
        ['instance_id', 'operation'],
        registry=registry
    )
    
    logger.info(f"Instance {instance_id}: Created ISOLATED registry (ID: {id(registry)})")
    
    return registry, instance_counter, instance_histogram

def run_worker(instance_id: int, port: int, max_operations: int = 10):
    """Run a worker that generates metrics on an isolated registry"""
    
    # Create isolated registry for this instance
    registry, counter, histogram = create_isolated_registry(instance_id, port)
    
    # Start metrics HTTP server on this port
    start_http_server(port=port, registry=registry)
    logger.info(f"Instance {instance_id}: Metrics server started on port {port}")
    logger.info(f"Instance {instance_id}: Access metrics at http://localhost:{port}/metrics")
    logger.info(f"Instance {instance_id}: Will run {max_operations} operations then exit")
    
    # Run worker loop - execute exactly max_operations times
    operation_count = 0
    
    while operation_count < max_operations:
        try:
            success = random.random() > 0.2  # 80% success rate
            op_name = f"op_{random.randint(1, 3)}"
            
            # Record operation
            op_start = time.time()
            time.sleep(random.uniform(0.1, 0.5))  # Simulate work
            op_duration = time.time() - op_start
            
            result = 'success' if success else 'failure'
            counter.labels(
                instance_id=f"script_{instance_id}",
                operation=op_name,
                result=result
            ).inc()
            
            histogram.labels(
                instance_id=f"script_{instance_id}",
                operation=op_name
            ).observe(op_duration)
            
            operation_count += 1
            status_icon = "✓" if success else "✗"
            logger.info(
                f"Instance {instance_id}: {status_icon} {op_name} - {result} "
                f"({op_duration:.3f}s) [Total: {operation_count}/{max_operations}]"
            )
            
            if operation_count < max_operations:
                time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Instance {instance_id}: Error: {e}")
    
    logger.info(
        f"Instance {instance_id}: Completed {operation_count} operations. Exiting."
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test isolated registry instances")
    parser.add_argument('--instance-id', type=int, default=1, help='Instance ID (1-3)')
    parser.add_argument('--port', type=int, required=True, help='Port for metrics server')
    parser.add_argument('--operations', type=int, default=10, help='Number of operations to execute')
    
    args = parser.parse_args()
    
    logger.info(f"Starting Instance {args.instance_id} with ISOLATED registry")
    logger.info(f"This instance will NOT share metrics with other instances")
    logger.info(f"Registry ID will be unique for each instance")
    logger.info(f"Will execute {args.operations} operations then exit")
    
    run_worker(args.instance_id, args.port, args.operations)

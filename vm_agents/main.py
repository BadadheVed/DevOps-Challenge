import asyncio
import logging
from prometheus_client import start_http_server
from metrics import REGISTRY, worker_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


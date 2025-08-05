"""
Product Creation Worker - Clean and simple
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
import ssl
import aiohttp

load_dotenv(dotenv_path=".env.product.local")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.worker_config import WorkerConfig
from core.base_worker import BaseWorker
from core.product_task_dispatcher import ProductTaskDispatcher
from handlers.product_creation_handler import ProductCreationHandler
from services.backend_api_client import BackendApiClient
from utils.logger import logger

async def main():
    """Product worker main function"""
    config = WorkerConfig()
    
    # Validate product worker specific requirements
    try:
        config.validate_for_product_worker()
    except ValueError as e:
        logger.error(f"Product worker config error: {e}")
        return
    
    logger.info("🎬 Starting Product Creation Worker")
    
    # SSL setup
    verify_ssl = not ('localhost' in config.backend_api_base_url.lower() or '127.0.0.1' in config.backend_api_base_url)
    ssl_context = None
    if not verify_ssl:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)

    async with aiohttp.ClientSession(connector=connector) as session:
        # Setup components
        backend_client = BackendApiClient(session, config.backend_api_base_url, config.backend_api_key)
        product_handler = ProductCreationHandler(config, backend_client)
        dispatcher = ProductTaskDispatcher(product_handler)
        
        # Message handler with timing
        async def handle_message(message):
            job_id = message.get("jobId", "unknown")
            logger.info(f"🎬 Processing product job {job_id}")
            
            start_time = asyncio.get_event_loop().time()
            result = await dispatcher.dispatch_task(message)
            processing_time = asyncio.get_event_loop().time() - start_time
            
            if processing_time > 300:  # More than 5 minutes
                logger.warning(f"⏱️ Long processing: {processing_time:.2f}s for job {job_id}")
            else:
                logger.info(f"✅ Product job {job_id} completed in {processing_time:.2f}s")
            
            return result
        
        # Create and run worker with graceful shutdown
        worker = BaseWorker(config, handle_message)
        logger.info("🎬 Product Worker starting...")
        await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

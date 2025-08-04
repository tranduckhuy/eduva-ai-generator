"""
Content Generation Worker - Clean and simple
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
import ssl
import aiohttp

load_dotenv(dotenv_path=".env.content")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.worker_config import WorkerConfig
from core.base_worker import BaseWorker
from core.content_task_dispatcher import ContentTaskDispatcher
from handlers.content_generation_handler import ContentGenerationHandler
from services.backend_api_client import BackendApiClient
from utils.logger import logger

async def main():
    """Content worker main function"""
    config = WorkerConfig()
    
    try:
        config.validate_for_content_worker()
    except ValueError as e:
        logger.error(f"Content worker config error: {e}")
        return
    
    logger.info(f"🔤 Starting Content Worker - Queue: {config.ai_task_queue}")
    logger.info(f"� Routing Key: {config.routing_key}")
    
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
        content_handler = ContentGenerationHandler(config, backend_client)
        dispatcher = ContentTaskDispatcher(content_handler)
        
        # Message handler
        async def handle_message(message):
            job_id = message.get("jobId", "unknown")
            logger.info(f"📝 Processing content job {job_id}")
            return await dispatcher.dispatch_task(message)
        
        # Create and run worker with graceful shutdown
        worker = BaseWorker(config, handle_message)
        logger.info("🔤 Content Worker starting...")
        await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

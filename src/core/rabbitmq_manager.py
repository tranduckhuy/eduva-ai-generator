"""
RabbitMQ connection and message handling
"""
import asyncio
import json
import pika
from typing import Callable, Optional, Dict, Any
from pika.exceptions import AMQPConnectionError
from src.config.worker_config import WorkerConfig
from src.utils.logger import logger


class RabbitMQManager:
    """Manager for RabbitMQ connections and message processing"""
    
    def __init__(self, config: WorkerConfig, message_handler: Callable):
        """
        Initialize RabbitMQ manager
        
        Args:
            config: Worker configuration
            message_handler: Async callable to handle messages
        """
        self.config = config
        self.message_handler = message_handler
        self.connection = None
        self.channel = None
        self.should_stop = False
        self.consumer_tag = None
        
        # Connection parameters
        self.connection_params = pika.URLParameters(config.rabbitmq_uri)
        
        logger.info(f"RabbitMQ URI: {config.rabbitmq_uri}")
        logger.info(f"RabbitMQ manager initialized for queue: {config.ai_task_queue}")
    
    # =============================================================================
    # LIFECYCLE METHODS
    # =============================================================================
    
    async def start(self):
        """Start the RabbitMQ consumer"""
        try:
            logger.info("Starting RabbitMQ consumer...")
            await self._connect()
            await self._start_consuming()
        except Exception as e:
            logger.error(f"Failed to start RabbitMQ consumer: {e}")
            raise
    
    async def stop(self):
        """Stop the RabbitMQ consumer"""
        logger.info("Stopping RabbitMQ consumer...")
        self.should_stop = True
        
        try:
            if self.channel and self.consumer_tag:
                self.channel.basic_cancel(self.consumer_tag)
            
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            
            logger.info("RabbitMQ consumer stopped")
        except Exception as e:
            logger.error(f"Error stopping RabbitMQ consumer: {e}")
    
    # =============================================================================
    # CONNECTION MANAGEMENT
    # =============================================================================
    
    async def _connect(self):
        """Establish connection to RabbitMQ"""
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to RabbitMQ (attempt {attempt + 1}/{max_retries})...")
                
                self.connection = pika.BlockingConnection(self.connection_params)
                self.channel = self.connection.channel()
                
                await self._setup_queues()
                
                logger.info("Successfully connected to RabbitMQ")
                return
                
            except AMQPConnectionError as e:
                logger.error(f"Failed to connect to RabbitMQ (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    raise
            except Exception as e:
                logger.error(f"Unexpected error connecting to RabbitMQ: {e}")
                raise
    
    async def _reconnect(self):
        """Attempt to reconnect to RabbitMQ"""
        logger.info("Attempting to reconnect to RabbitMQ...")
        
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            
            await asyncio.sleep(5)
            await self._connect()
            
        except Exception as e:
            logger.error(f"Failed to reconnect to RabbitMQ: {e}")
            await asyncio.sleep(10)
    
    # =============================================================================
    # QUEUE AND EXCHANGE SETUP
    # =============================================================================
    
    async def _setup_queues(self):
        """Setup RabbitMQ queues and exchanges"""
        try:
            self._setup_exchanges()
            self._setup_main_queue()
            self._setup_dead_letter_queue()
            self._setup_bindings()
            self._setup_qos()
            
            logger.info(f"Queues setup completed: {self.config.ai_task_queue}, {self.config.dlq_queue}")
            
        except Exception as e:
            logger.error(f"Failed to setup queues: {e}")
            raise
    
    def _setup_exchanges(self):
        """Setup exchanges"""
        # Main exchange
        self.channel.exchange_declare(
            exchange=self.config.main_exchange,
            exchange_type='direct',
            durable=True
        )
        
        # Dead letter exchange
        self.channel.exchange_declare(
            exchange=self.config.dlq_exchange,
            exchange_type='direct',
            durable=True
        )
    
    def _setup_main_queue(self):
        """Setup main task queue"""
        try:
            logger.info(f"Checking if queue {self.config.ai_task_queue} exists...")
            self.channel.queue_declare(
                queue=self.config.ai_task_queue,
                passive=True
            )
            logger.info(f"Queue {self.config.ai_task_queue} already exists")
        except pika.exceptions.ChannelClosedByBroker as e:
            logger.warning(f"Queue check failed (passive): {e}")
            self.channel = self.connection.channel()  # Reopen channel
            logger.info(f"Creating queue {self.config.ai_task_queue}")
            self.channel.queue_declare(
                queue=self.config.ai_task_queue,
                durable=True,
                arguments={
                    'x-dead-letter-exchange': self.config.dlq_exchange,
                    'x-dead-letter-routing-key': self.config.dlq_routing_key
                }
            )

    
    def _setup_dead_letter_queue(self):
        """Setup dead letter queue"""
        self.channel.queue_declare(
            queue=self.config.dlq_queue,
            durable=True
        )
    
    def _setup_bindings(self):
        """Setup queue bindings"""
        # Bind main queue to main exchange
        self.channel.queue_bind(
            exchange=self.config.main_exchange,
            queue=self.config.ai_task_queue,
            routing_key=self.config.routing_key
        )
        
        # Bind dead letter queue to dead letter exchange
        self.channel.queue_bind(
            exchange=self.config.dlq_exchange,
            queue=self.config.dlq_queue,
            routing_key=self.config.dlq_routing_key
        )
    
    def _setup_qos(self):
        """Setup quality of service"""
        self.channel.basic_qos(prefetch_count=self.config.prefetch_count)
    
    # =============================================================================
    # MESSAGE CONSUMPTION
    # =============================================================================
    
    async def _start_consuming(self):
        """Start consuming messages from the queue"""
        try:
            self.channel.basic_consume(
                queue=self.config.ai_task_queue,
                on_message_callback=self._on_message_received,
                auto_ack=False
            )
            
            logger.info(f"Started consuming from queue: {self.config.ai_task_queue}")
            
            # Main consumption loop
            while not self.should_stop:
                try:
                    self.connection.process_data_events(time_limit=1)
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"Error processing RabbitMQ events: {e}")
                    await self._reconnect()
            
        except Exception as e:
            logger.error(f"Error in message consumption loop: {e}")
            raise
    
    def _on_message_received(self, channel, method, properties, body):
        """Callback for when a message is received"""
        try:
            message_data = json.loads(body.decode('utf-8'))
            logger.info(f"Received message: {message_data}")
            
            asyncio.create_task(self._process_message(channel, method, properties, message_data))
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message JSON: {e}")
            channel.basic_nack(method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error handling received message: {e}")
            channel.basic_nack(method.delivery_tag, requeue=False)
    
    # =============================================================================
    # MESSAGE PROCESSING AND RETRY LOGIC
    # =============================================================================
    
    async def _process_message(self, channel, method, properties, message_data):
        """Process a single message with retry and dead letter support"""
        job_id = message_data.get('jobId', 'unknown')
        
        try:
            retry_count = self._get_retry_count(properties)
            logger.info(f"🔄 Processing message {job_id} (retry: {retry_count})")
            
            success = await self.message_handler(message_data)
            
            if success:
                self._handle_success(channel, method, job_id)
            else:
                await self._handle_failure(channel, method, properties, message_data, job_id, retry_count)
                
        except Exception as e:
            logger.error(f"� Exception processing message {job_id}: {e}")
            self._handle_exception(channel, method, job_id)
    
    def _get_retry_count(self, properties) -> int:
        """Get retry count from message properties"""
        if properties and properties.headers:
            return properties.headers.get('x-retry-count', 0)
        return 0
    
    def _handle_success(self, channel, method, job_id):
        """Handle successful message processing"""
        channel.basic_ack(method.delivery_tag)
        logger.info(f"✅ Message {job_id} processed successfully")
    
    async def _handle_failure(self, channel, method, properties, message_data, job_id, retry_count):
        """Handle failed message processing with retry logic"""
        max_retries = getattr(self.config, 'max_retries', 3)
        
        if retry_count < max_retries:
            await self._retry_message(channel, method, properties, message_data, job_id, retry_count)
        else:
            self._send_to_dlq(channel, method, job_id, max_retries)
    
    async def _retry_message(self, channel, method, properties, message_data, job_id, retry_count):
        """Retry message by republishing with updated retry count"""
        retry_count += 1
        logger.warning(f"⚠️ Message {job_id} failed, requeuing (retry {retry_count}/{self.config.max_retries})")
        
        # Create new properties with updated retry count
        new_headers = properties.headers.copy() if properties.headers else {}
        new_headers['x-retry-count'] = retry_count
        
        new_properties = pika.BasicProperties(
            headers=new_headers,
            delivery_mode=properties.delivery_mode if properties else 2,
            message_id=properties.message_id if properties else None,
            timestamp=properties.timestamp if properties else None
        )
        
        # Republish message
        channel.basic_publish(
            exchange=self.config.main_exchange,
            routing_key=self.config.routing_key,
            body=json.dumps(message_data),
            properties=new_properties
        )
        
        # Ack original message
        channel.basic_ack(method.delivery_tag)
    
    def _send_to_dlq(self, channel, method, job_id, max_retries):
        """Send message to dead letter queue"""
        logger.error(f"Message {job_id} failed after {max_retries} retries, sending to DLQ")
        channel.basic_nack(method.delivery_tag, requeue=False)
    
    def _handle_exception(self, channel, method, job_id):
        """Handle exception during message processing"""
        logger.error(f"Sending message {job_id} to DLQ due to exception")
        channel.basic_nack(method.delivery_tag, requeue=False)
    
    # =============================================================================
    # HEALTH CHECK AND MONITORING
    # =============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                dlq_info = self.get_dlq_info()
                return {
                    "connected": True,
                    "dlq_message_count": dlq_info.get("message_count", 0),
                    "main_queue": self.config.ai_task_queue,
                    "dlq_queue": self.config.dlq_queue
                }
            else:
                return {"connected": False, "error": "Connection is closed"}
        except Exception as e:
            return {"connected": False, "error": str(e)}
    
    def get_dlq_info(self) -> Dict[str, Any]:
        """Get information about dead letter queue"""
        try:
            if self.channel:
                method = self.channel.queue_declare(queue=self.config.dlq_queue, passive=True)
                return {
                    "message_count": method.method.message_count,
                    "consumer_count": method.method.consumer_count
                }
        except Exception as e:
            logger.warning(f"Could not get DLQ info: {e}")
            return {}
    
    # =============================================================================
    # DLQ MANAGEMENT
    # =============================================================================
    
    async def reprocess_dlq_messages(self, limit: int = 10) -> int:
        """
        Reprocess messages from DLQ back to main queue
        
        Args:
            limit: Maximum number of messages to reprocess
            
        Returns:
            int: Number of messages reprocessed
        """
        reprocessed = 0
        try:
            for i in range(limit):
                method, properties, body = self.channel.basic_get(
                    queue=self.config.dlq_queue,
                    auto_ack=False
                )
                
                if method is None:
                    break  # No more messages
                
                try:
                    # Republish to main queue
                    self.channel.basic_publish(
                        exchange=self.config.main_exchange,
                        routing_key=self.config.routing_key,
                        body=body,
                        properties=properties
                    )
                    
                    self.channel.basic_ack(method.delivery_tag)
                    reprocessed += 1
                    logger.info(f"Reprocessed message {i+1} from DLQ")
                    
                except Exception as e:
                    logger.error(f"Failed to reprocess message {i+1}: {e}")
                    self.channel.basic_nack(method.delivery_tag, requeue=True)
                    break
            
            logger.info(f"Reprocessed {reprocessed} messages from DLQ")
            return reprocessed
            
        except Exception as e:
            logger.error(f"Error reprocessing DLQ messages: {e}")
            return reprocessed

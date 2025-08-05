"""
Worker configuration for AI processing
"""
import os
import tempfile
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class WorkerConfig:
    """Configuration for AI worker"""
    
    # RabbitMQ Configuration  
    rabbitmq_uri: str = os.getenv("RABBITMQ_URI", "amqp://eduva:eduva2025@localhost:5672")
    
    # Queue Configuration - Simple setup
    ai_task_queue: str = os.getenv("QUEUE_NAME", "ai_queue")
    main_exchange: str = os.getenv("EXCHANGE_NAME", "eduva_exchange")
    routing_key: str = os.getenv("ROUTING_KEY", "ai.task")
    dlq_queue: str = os.getenv("DLQ_QUEUE", "eduva.dlq")
    dlq_exchange: str = os.getenv("DLQ_EXCHANGE", "eduva.dlq.exchange")
    dlq_routing_key: str = os.getenv("DLQ_ROUTING_KEY", "eduva.dlq.routing_key")
    
    # Azure Blob Storage Configuration
    azure_storage_connection_string: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    azure_input_container: str = os.getenv("AZURE_INPUT_CONTAINER", "eduva-temp-storage")
    azure_output_container: str = os.getenv("AZURE_OUTPUT_CONTAINER", "eduva-storage")
    
    # AI Service Configuration
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    google_application_credentials: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    default_model: str = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash-lite-preview-06-17")
    unsplash_access_key: str = os.getenv("UNSPLASH_ACCESS_KEY", "")
    
    # Backend API Configuration
    backend_api_base_url: str = os.getenv("BACKEND_API_BASE_URL", "https://localhost:9001")
    backend_api_key: str = os.getenv("BACKEND_API_KEY", "")
    
    # Worker Configuration
    worker_id: str = os.getenv("WORKER_ID", "ai-worker-001")
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    retry_delay: int = int(os.getenv("RETRY_DELAY", "5"))
    
    # Dead Letter Queue Configuration
    dlq_monitoring_enabled: bool = os.getenv("DLQ_MONITORING_ENABLED", "true").lower() == "true"
    dlq_alert_threshold: int = int(os.getenv("DLQ_ALERT_THRESHOLD", "10"))
    
    # Processing Configuration  
    temp_dir: str = os.getenv("TEMP_DIR", os.path.join(tempfile.gettempdir(), "ai_worker"))
    max_concurrent_tasks: int = int(os.getenv("MAX_CONCURRENT_TASKS", "2"))
    prefetch_count: int = int(os.getenv("PREFETCH_COUNT", "2"))
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.azure_storage_connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING is required")
        
        if not self.backend_api_base_url:
            raise ValueError("BACKEND_API_BASE_URL is required")
        
        if not self.backend_api_key:
            raise ValueError("BACKEND_API_KEY is required")
        
        if not self.worker_id:
            raise ValueError("WORKER_ID is required")
        
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
    
    @property
    def is_backend_api_enabled(self) -> bool:
        """Check if backend API is properly configured"""
        return bool(self.backend_api_key and self.backend_api_base_url)
    
    def validate_for_product_worker(self):
        """Additional validation for product worker (TTS, video processing)"""
        if not self.google_application_credentials:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS is required for product worker")
        
        # Validate that Google credentials file exists
        if not os.path.exists(self.google_application_credentials):
            raise ValueError(f"Google credentials file not found: {self.google_application_credentials}")
    
    def validate_for_content_worker(self):
        # Validate google API key for content worker
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY is required for content worker")

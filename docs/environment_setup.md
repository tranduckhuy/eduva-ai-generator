# Environment Setup Guide

This guide helps you configure environment variables for both Content Worker and Product Worker. Please refer to the provided `.env.content.example` and `.env.product.example` files for the most up-to-date variable lists.

---

## 1. Product Worker Environment Setup

### Step 2: Create .env File

Create a `.env.product.local` file in the project root (see `.env.product.example`):

```env
RABBITMQ_URI=amqp://guest:guest@your-rabbitmq-server:5672/
QUEUE_NAME=eduva.product.queue
EXCHANGE_NAME=eduva_exchange
ROUTING_KEY=eduva.product.routing_key
AZURE_STORAGE_CONNECTION_STRING=your_azure_connection_string
AZURE_INPUT_CONTAINER=eduva-temp-storage
AZURE_OUTPUT_CONTAINER=eduva-storage
BACKEND_API_BASE_URL=https://localhost:9001
BACKEND_API_KEY=your_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=C:/path/to/your/service-account-key.json
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
IMAGE_GENERATION_MODEL=imagen-3.0-fast-generate-001
UNSPLASH_ACCESS_KEY=your_unsplash_access_key
WORKER_ID=product-worker-001
MAX_CONCURRENT_TASKS=2
PREFETCH_COUNT=2
```

---

## 2. Content Worker Environment Setup

Create a `.env.content.local` file in the project root (see `.env.content.example`):

```env
RABBITMQ_URI=amqp://guest:guest@your-rabbitmq-server:5672/
QUEUE_NAME=eduva.content.queue
EXCHANGE_NAME=eduva_exchange
ROUTING_KEY=eduva.content.routing_key
AZURE_STORAGE_CONNECTION_STRING=your_azure_connection_string
AZURE_INPUT_CONTAINER=eduva-temp-storage
AZURE_OUTPUT_CONTAINER=eduva-storage
BACKEND_API_BASE_URL=https://localhost:9001
BACKEND_API_KEY=your_api_key_here
GOOGLE_API_KEY=your_google_api_key
DEFAULT_MODEL=gemini-2.5-flash-lite-preview-06-17
PREFETCH_COUNT=4
```

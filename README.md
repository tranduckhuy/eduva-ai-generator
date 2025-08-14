# AI Worker Service

AI Worker Service is an asynchronous task processing system that integrates with RabbitMQ, Azure Blob Storage, and provides callback support to a C# backend. It is designed for scalable content and product generation workflows, supporting both local development and production deployments via Docker.

## 🚀 Features

- Asynchronous task processing via RabbitMQ
- Integration with Azure Blob Storage for file management
- Callback to backend API for task status and results
- Modular architecture for content and product generation
- Easy deployment: local or Docker

## 📋 Prerequisites

- Python 3.12+
- RabbitMQ server (local or remote)
- Azure Blob Storage account
- Backend API endpoint (for callbacks)
- (Optional) Google Cloud credentials for TTS
- (Optional) OpenAI API key for content generation

## ⚙️ Environment Setup

1. Copy the example environment file and update it with your configuration:

   ```bash
   cp .env.example .env
   # Edit .env with your RabbitMQ, Azure, Backend API, and other credentials
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements-content.txt  # For content worker
   pip install -r requirements-product.txt  # For product worker
   ```

## 🖥️ Running Locally (Development)

Start the desired worker (content or product):

```bash
python content_worker.py   # For content tasks
python product_worker.py   # For product tasks
```

## 🐳 Running with Docker (Production)

Build and start the services using Docker Compose:

```bash
docker-compose -f docker-compose.content.yaml up --build -d   # Content worker
# or
docker-compose -f docker-compose.product.yaml up --build -d   # Product worker
```

## 🔑 Environment Variables

**Required:**

- `RABBITMQ_URI` - RabbitMQ connection URI
- `AZURE_STORAGE_CONNECTION_STRING` - Azure Blob Storage connection string
- `AZURE_INPUT_CONTAINER` - Azure Blob container for input files
- `AZURE_OUTPUT_CONTAINER` - Azure Blob container for output files
- `BACKEND_API_BASE_URL` - Backend API base URL for callbacks
- `BACKEND_API_KEY` - Backend API key
- `GOOGLE_API_KEY` - Google AI (Gemini) API key (if using Gemini)
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to Google TTS credentials JSON

**Optional:**

- `DEFAULT_MODEL` - Default Gemini model (default: gemini-2.0-flash-exp)
- `WORKER_ID` - Worker identifier (default: auto-generated)
- `MAX_CONCURRENT_TASKS` - Maximum concurrent tasks (default: 2)
- `UNSPLASH_ACCESS_KEY` - Unsplash API key for image generation
- `RABBITMQ_HOST` - RabbitMQ host (default: localhost)

## 📨 Supported Task Types

- `generate_content` - Generate lesson content
- `create_product` - Create product materials

## 📁 Project Structure

```
├── content_worker.py            # Entry point for content worker
├── product_worker.py            # Entry point for product worker
├── Dockerfile.content           # Dockerfile for content worker
├── Dockerfile.product           # Dockerfile for product worker
├── docker-compose.content.yaml  # Docker Compose for content worker
├── docker-compose.product.yaml  # Docker Compose for product worker
├── requirements-content.txt     # Python dependencies for content worker
├── requirements-product.txt     # Python dependencies for product worker
├── src/                         # Source code modules
│   ├── agents/                  # Task agents
│   ├── config/                  # Configuration files
│   ├── core/                    # Core logic
│   ├── handlers/                # Task handlers
│   ├── models/                  # Data models
│   ├── services/                # Service integrations
│   └── utils/                   # Utility functions
└── ...
```

## 🎯 Common Commands

```bash
# Start content worker (development)
python content_worker.py

# Start product worker (development)
python product_worker.py

# Start content worker (Docker)
docker-compose -f docker-compose.content.yaml up --build -d

# Start product worker (Docker)
docker-compose -f docker-compose.product.yaml up --build -d

# View logs
docker-compose -f docker-compose.content.yaml logs -f
# or
docker-compose -f docker-compose.product.yaml logs -f

# Stop all services
docker-compose -f docker-compose.content.yaml down
# or
docker-compose -f docker-compose.product.yaml down
```

---

For more details, see the `docs/` directory or contact the project maintainer.

# AI Worker Service

AI Worker Service automatically transforms input files into narrated audio and video lessons using AI, enabling fast and scalable lesson creation from documents.

## 🚀 Features

- Automatically generates lesson content from input files using AI (text, audio, and video)
- Converts documents into narrated audio and video lessons
- Asynchronous task processing via RabbitMQ for scalability
- Seamless integration with Azure Blob Storage for file management
- Callback to backend API for real-time task status and results
- Modular architecture for content and product (audio/video) generation
- Easy deployment: local development or Docker production

## 📋 Prerequisites

- Python 3.12+
- RabbitMQ server (local or remote)
- Azure Blob Storage account
- Backend API endpoint (for callbacks)
- Google Cloud credentials for TTS
- Gemini API key for content generation

## ⚙️ Environment Setup

See [`docs/environment_setup.md`](docs/environment_setup.md) for detailed environment configuration, including all required and optional environment variables, credential setup, and troubleshooting tips.

**Recommended:** Create separate environment files for each worker:

- `.env.content.local` for Content Worker (see `.env.content.example`)
- `.env.product.local` for Product Worker (see `.env.product.example`)

1. Copy the example environment files and update them with your configuration:

   ```bash
   cp .env.content.example .env.content.local
   cp .env.product.example .env.product.local
   # Edit the .env.*.local files with your RabbitMQ, Azure, Google, and API credentials
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

## 🔑 Environment & Prerequisites

See [`docs/environment_setup.md`](docs/environment_setup.md) for detailed environment configuration and setup instructions, including all required and optional environment variables, credential setup, and troubleshooting tips.

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

# AI Worker Service

AI Worker kết nối với RabbitMQ external, xử lý task bất đồng bộ, tích hợp với Azure Blob Storage và callback về backend C#.

## 🚀 Sử dụng

### 1. Cấu hình Environment

```bash
cp .env.example .env
# Chỉnh sửa .env với thông tin RabbitMQ server, Azure, Backend API
```

### 2. Chạy Local (Development)

```bash
pip install -r requirements.txt
python worker.py
```

### 3. Chạy Docker (Production)

```bash
docker-compose up --build -d
```

## 🔧 Environment Variables

**Required:**

- `RABBITMQ_URI` - RabbitMQ connection URI
- `AZURE_STORAGE_CONNECTION_STRING` - Azure Blob connection
- `AZURE_INPUT_CONTAINER` - Container for input files
- `AZURE_OUTPUT_CONTAINER` - Container for output files
- `BACKEND_API_BASE_URL` - Backend callback URL
- `BACKEND_API_KEY` - Backend API key
- `GOOGLE_API_KEY` - Google AI (Gemini) API key
- `GOOGLE_APPLICATION_CREDENTIALS` - Google TTS credentials path

**Optional:**

- `DEFAULT_MODEL` - Gemini model (default: gemini-2.0-flash-exp)
- `WORKER_ID` - Worker identifier (default: auto-generated)
- `MAX_CONCURRENT_TASKS` - Max concurrent tasks (default: 2)
- `UNSPLASH_ACCESS_KEY` - For image generation

## 📨 Task Types

- `generate_content` - Generate lesson content
- `create_product` - Create product materials

## 🎯 Quick Commands

```bash
# Development
python worker.py

# Production
docker-compose up -d

# View logs
docker-compose logs -f ai-worker

# Stop
docker-compose down
```

## � Sử dụng

### 1. Cấu hình Environment

```bash
cp .env.example .env
# Chỉnh sửa .env với thông tin thực tế
```

### 2. Chạy Local (Development)

```bash
pip install -r requirements.txt
python worker.py
```

### 3. Chạy Docker (Production)

```bash
docker-compose up --build
```

## 📁 Cấu trúc

```
├── worker.py              # Main worker entry point
├── app.py                 # FastAPI (nếu cần API)
├── docker-compose.yml     # RabbitMQ + Worker
├── .env.example          # Environment template
└── src/                  # Source code modules
```

## 🔧 Environment Variables

**Required:**

- `AZURE_STORAGE_CONNECTION_STRING` - Azure Blob connection
- `BACKEND_API_BASE_URL` - Backend callback URL
- `BACKEND_API_KEY` - Backend API key
- `OPENAI_API_KEY` - OpenAI API key

**Optional:**

- `RABBITMQ_HOST` - RabbitMQ host (default: localhost)
- `WORKER_ID` - Worker identifier (default: auto-generated)
- `MAX_CONCURRENT_TASKS` - Max concurrent tasks (default: 2)

## 📨 Task Types

- `generate_content` - Generate lesson content
- `create_product` - Create product materials

## 🎯 Quick Commands

```bash
# Development
python worker.py

# Production
docker-compose up -d

# Logs
docker-compose logs -f

# Stop
docker-compose down
```

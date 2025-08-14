# Environment Setup Guide

This guide helps you configure environment variables for both Content Worker and Product Worker. Please refer to the provided `.env.content.example` and `.env.product.example` files for the most up-to-date variable lists.

---

## 1. Google Cloud Text-to-Speech Setup (Product Worker)

### Step 1: Create Google Cloud Project and Service Account

1. **Create a Google Cloud Project:**

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Note your `PROJECT_ID`

2. **Enable Cloud Text-to-Speech API:**

   - In the Console, navigate to "APIs & Services" > "Library"
   - Search for "Cloud Text-to-Speech API" and enable it

3. **Create a Service Account:**
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "CREATE SERVICE ACCOUNT"
   - Enter a name (e.g., `video-generator-sa`)
   - Assign the role: "Cloud Text-to-Speech User"
   - Create and download the JSON key file

### Step 2: Configure Environment Variables

**Windows (PowerShell):**

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your\service-account-key.json"
$env:GOOGLE_CLOUD_PROJECT="your_project_id"
$env:GOOGLE_CLOUD_LOCATION="us-central1"
$env:UNSPLASH_ACCESS_KEY="your_unsplash_access_key"  # Optional
```

**macOS/Linux:**

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
export GOOGLE_CLOUD_PROJECT="your_project_id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export UNSPLASH_ACCESS_KEY="your_unsplash_access_key"  # Optional
```

### Step 3: Create .env File

Create a `.env.product` file in the project root (see `.env.product.example`):

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

Create a `.env.content` file in the project root (see `.env.content.example`):

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

---

## 3. Additional Notes

- **Never commit your `.env` files or credentials to version control.**
- For local development, you can use PowerShell, Command Prompt, or Bash to set environment variables temporarily.
- For production, use Docker Compose environment or cloud secret managers.
- If you do not provide `UNSPLASH_ACCESS_KEY`, the system will use placeholder images.

---

## 5. Troubleshooting

- **Authentication errors:** Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid JSON key file and the service account has the correct role.
- **Import errors:** Install dependencies with `pip install google-cloud-texttospeech`.
- **Path issues (Windows):** Use forward slashes or double backslashes in paths.

---

## 6. Production Recommendations

- Use cloud secret managers for sensitive variables.
- Separate environment files for dev/staging/prod.
- Enable logging and monitoring for usage and cost tracking.

---

For more details, see the example environment files or contact the project maintainer.

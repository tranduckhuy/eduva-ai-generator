import os
from dotenv import load_dotenv

load_dotenv(override=True)

from src.apis.create_app import create_app, api_router
import uvicorn

# Get environment variables
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "7860"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

app = create_app()

app.include_router(api_router)
if __name__ == "__main__":
    uvicorn.run("app:app", host=APP_HOST, port=APP_PORT, reload=DEBUG)

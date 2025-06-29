import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from src.utils.logger import logger

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash-lite-preview-06-17")
TEMPERATURE = float(os.getenv("TEMPERATURE", "1.0"))

# Default model instances
default_llm = ChatGoogleGenerativeAI(model=DEFAULT_MODEL, temperature=1)
llm_2_5_flash_preview = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite-preview-06-17", temperature=1
)

# Default embeddings model
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")


def get_llm(model_name: str, api_key: str = None) -> ChatGoogleGenerativeAI:
    """
    Get LLM instance based on model name and optional API key.

    Args:
        model_name: Name of the model to use
        api_key: Optional API key for authentication

    Returns:
        Configured ChatGoogleGenerativeAI instance

    Raises:
        ValueError: If model name is not supported
    """
    # log model name
    logger.info(f"Getting LLM for model: {model_name}")

    if api_key:
        logger.warning("Using custom API key")
        return ChatGoogleGenerativeAI(
            model=model_name, temperature=1, google_api_key=api_key
        )
    else:
        return default_llm

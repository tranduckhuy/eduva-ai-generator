from src.utils.logger import logger
from .tools import retrieve_document
from .func import create_slide_data
from .prompt import create_messages_for_llm


async def run_slide_creator(topic: str, uploaded_files_content: str = None, model_name: str = "gemini-2.0-flash"):
    """Simplified slide creator with essential features only"""
    try:
        logger.info(f"Creating slides for topic: {topic}")
        
        # Step 1: Retrieve documents from vector store
        rag_result = retrieve_document.invoke(topic)
        rag_context = rag_result.get("context_str", "")
        selected_documents = rag_result.get("selected_documents", [])
        
        logger.info(f"Retrieved {len(selected_documents)} documents from vector store")
        
        # Step 2: Build prompt messages
        prompt_messages = create_messages_for_llm(
            topic=topic,
            uploaded_files_content=uploaded_files_content,
            rag_context=rag_context
        )
        
        # Step 3: Generate slides with LLM
        from src.config.llm import get_llm
        llm = get_llm(model_name)
        logger.info(f"Generating slides with {model_name}...")
        
        response = await llm.ainvoke(prompt_messages)
        
        # Step 4: Parse response and create slide data
        slide_data = create_slide_data(response.content)
        
        # Step 5: Add basic metadata
        if slide_data and "lesson_info" in slide_data:
            lesson_info = slide_data["lesson_info"]
            lesson_info["primary_source"] = "file_upload" if uploaded_files_content else "vector_store"
            lesson_info["rag_documents_count"] = len(selected_documents)
            lesson_info["target_level"] = "Cấp 3 (lớp 10-12)"
        
        logger.info(f"Successfully created slides")
        
        return {
            "success": True,
            "slide_data": slide_data,
            "selected_documents": selected_documents,
        }
        
    except Exception as e:
        logger.error(f"Error creating slides: {e}")
        return {"success": False, "error": str(e), "slide_data": None}

import os
import asyncio
import functools
from src.utils.logger import logger
from .tools import retrieve_document
from .func import create_slide_data
from .prompt import create_messages_for_llm

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")

async def run_slide_creator(topic: str, subject: str = None, grade: str = None, duration: str = None, uploaded_files_content: str = None, model_name: str = DEFAULT_MODEL):
    """Simplified slide creator with essential features only"""
    try:
        logger.info(f"Creating slides for topic: {topic}, subject: {subject}, grade: {grade}, duration: {duration}")
          # Step 1: Retrieve documents from vector store với metadata filter
        # Run the synchronous retrieve_document.invoke in a thread pool to avoid blocking
        loop = asyncio.get_running_loop()
        rag_result = await loop.run_in_executor(
            None, 
            functools.partial(
                retrieve_document.invoke,
                {
                    "query": topic,
                    "subject": subject,
                    "grade": grade
                }
            )
        )
        rag_context = rag_result.get("context_str", "")
        selected_documents = rag_result.get("selected_documents", [])
        
        logger.info(f"Retrieved {len(selected_documents)} documents from vector store")
        # Log short summary of text content in selected documents
        if selected_documents:
            logger.info(f"Selected documents content: {', '.join([doc.page_content[:100] for doc in selected_documents])}")
            

        # Step 2: Build prompt messages
        prompt_messages = create_messages_for_llm(
            topic=f"{topic} (Môn: {subject}, Lớp: {grade})",
            duration=duration,
            uploaded_files_content=uploaded_files_content,
            rag_context=rag_context
        )

        logger.info(f"Prompt messages created with {len(prompt_messages)} messages")
        
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
            if subject:
                lesson_info["subject"] = subject
            if grade:
                lesson_info["grade"] = grade
        
        logger.info(f"Successfully created slides")
        
        return {
            "success": True,
            "slide_data": slide_data,
            "selected_documents": selected_documents,
        }
        
    except Exception as e:
        logger.error(f"Error creating slides: {e}")
        return {"success": False, "error": str(e), "slide_data": None}

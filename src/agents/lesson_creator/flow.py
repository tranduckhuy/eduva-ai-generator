from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from .func import State, execute_tool, generate_slide_content, create_slide_data
from src.utils.logger import logger


async def run_slide_creator(topic: str, uploaded_files_content: str = None):
    """Simple slide creator with mandatory RAG and file upload priority"""
    try:
        logger.info(f"Creating slides for topic: {topic}")
        
        # Step 1: Always retrieve documents from vector store
        from .tools import retrieve_document
        logger.info("Step 1: Retrieving documents from vector store...")
        
        rag_result = retrieve_document.invoke(topic)
        rag_context = rag_result.get("context_str", "")
        selected_documents = rag_result.get("selected_documents", [])
        
        logger.info(f"Retrieved {len(selected_documents)} documents from vector store")
        
        # Step 2: Build context with file upload priority
        full_context = f"Tạo slide bài giảng cho học sinh cấp 3 về: {topic}\n\n"
        
        # Priority 1: File upload content (if exists)
        if uploaded_files_content and uploaded_files_content.strip():
            full_context += f"NGUỒN CHÍNH - NỘI DUNG FILE UPLOAD (GIỮ NGUYÊN):\n{uploaded_files_content}\n\n"
            logger.info(f"Using uploaded file content: {len(uploaded_files_content)} chars")
        
        # Priority 2: Vector store documents
        if rag_context:
            full_context += f"NGUỒN PHỤ - TÀI LIỆU THAM KHẢO:\n{rag_context}\n\n"
        
        # Step 3: Generate slide with clear instructions
        full_context += """
YÊU CẦU TẠO SLIDE:
1. NẾU CÓ FILE UPLOAD: Dùng nội dung file làm chính, giữ nguyên định nghĩa, khái niệm, ví dụ
2. Bổ sung thông tin từ tài liệu tham khảo nếu cần
3. Tạo slide phù hợp học sinh cấp 3

TRẢ VỀ JSON:
{
  "lesson_info": {
    "title": "Tiêu đề bài",
    "slide_count": số_slide,
    "content_source": "file_upload" hoặc "vector_store" hoặc "combined"
  },
  "slides": [
    {
      "slide_id": 1,
      "title": "Tiêu đề slide",
      "content": ["Nội dung bullet points"],
      "tts_script": "Script thuyết minh",
      "image_keywords": ["keyword1", "keyword2"]
    }
  ]
}
"""
        
        # Step 4: Call LLM to generate slides
        from src.config.llm import llm_2_0
        logger.info("Step 2: Generating slides with LLM...")
        
        response = await llm_2_0.ainvoke(full_context)
        
        # Step 5: Parse response to JSON
        slide_data = create_slide_data(response.content)
        
        # Step 6: Add source information
        if slide_data and "lesson_info" in slide_data:
            lesson_info = slide_data["lesson_info"]
            
            # Determine content source
            if uploaded_files_content:
                lesson_info["primary_source"] = "file_upload"
                lesson_info["has_uploaded_content"] = True
            else:
                lesson_info["primary_source"] = "vector_store"
                lesson_info["has_uploaded_content"] = False
                
            lesson_info["rag_documents_count"] = len(selected_documents)
            lesson_info["target_level"] = "Cấp 3 (lớp 10-12)"
        
        logger.info(f"Successfully created {slide_data.get('lesson_info', {}).get('slide_count', 0)} slides")
        logger.info(f"Using {len(selected_documents)} RAG documents")
        
        return {
            "success": True,
            "slide_data": slide_data,
            "selected_documents": selected_documents,
            "rag_sources": [{"title": f"Document {i+1}", "content_preview": doc.page_content[:100] if hasattr(doc, 'page_content') else str(doc)[:100]} 
                          for i, doc in enumerate(selected_documents)],
        }
        
    except Exception as e:
        logger.error(f"Error creating slides: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e), "slide_data": None}

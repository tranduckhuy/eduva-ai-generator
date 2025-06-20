from fastapi import APIRouter, status, Form, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from src.agents.lesson_creator.flow import run_slide_creator
from src.utils.logger import logger
from src.utils.helper import preprocess_messages

router = APIRouter(prefix="/ai", tags=["AI"])

class SlideRequest(BaseModel):
    topic: str

@router.post("/slide-creator")
async def create_slides(
    topic: str = Form(..., description="Chủ đề cần tạo slide cho học sinh cấp 3"),
    files: List[UploadFile] = File(None, description="Tài liệu tham khảo (PDF, DOCX)")
):
    """
    API tạo slide cho học sinh cấp 3 - Ưu tiên file upload, bắt buộc RAG
    """
    try:
        logger.info(f"Creating slides for topic: {topic}")
        
        # Extract content from uploaded files (simplified)
        uploaded_content = ""
        if files and len(files) > 0:
            valid_files = [f for f in files if f is not None and f.filename]
            
            for file in valid_files:
                try:
                    logger.info(f"Processing file: {file.filename}")
                    
                    # Read file content
                    content = await file.read()
                    
                    # Simple text extraction
                    if file.filename.endswith('.txt'):
                        file_text = content.decode('utf-8')
                    elif file.filename.endswith(('.pdf', '.docx')):
                        # For now, treat as text (in production, use proper loaders)
                        file_text = f"Nội dung từ {file.filename} (cần xử lý file)"
                    else:
                        file_text = f"File: {file.filename}"
                    
                    uploaded_content += f"\n=== {file.filename} ===\n{file_text}\n"
                    
                except Exception as e:
                    logger.error(f"Error processing {file.filename}: {e}")
                    uploaded_content += f"\nLỗi xử lý {file.filename}: {str(e)}\n"
        
        # Call the simplified slide creator
        result = await run_slide_creator(
            topic=topic,
            uploaded_files_content=uploaded_content if uploaded_content.strip() else None
        )
        
        if result["success"]:
            slide_data = result["slide_data"]
            selected_docs = result["selected_documents"]
            rag_sources = result["rag_sources"]
            
            return JSONResponse(content={
                "success": True,
                "slide_data": slide_data,
                "selected_documents": len(selected_docs),
                "rag_sources": rag_sources,
                "message": f"Tạo thành công {slide_data.get('lesson_info', {}).get('slide_count', 0)} slides",
                "debug_info": {
                    "files_processed": len([f for f in (files or []) if f is not None and f.filename]),
                    "uploaded_content_length": len(uploaded_content),
                    "rag_documents_found": len(selected_docs),
                    "primary_source": slide_data.get('lesson_info', {}).get('primary_source', 'unknown')
                }
            })
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": result["error"],
                    "message": "Lỗi khi tạo slide"
                }
            )
            
    except Exception as e:
        logger.error(f"Router error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": str(e),
                "message": "Lỗi hệ thống"
            }
        )

@router.get("/slide-creator/sample")
async def get_sample_slide():
    """Trả về mẫu cấu trúc slide cho học sinh cấp 3 với thông tin nguồn tài liệu"""
    sample = {
        "lesson_info": {
            "title": "Hàm số bậc nhất - Toán lớp 10",
            "slide_count": 4,
            "target_level": "Cấp 3 (lớp 10-12)",
            "subject": "Toán học",
            "content_sources": ["Sách giáo khoa Toán 10", "File upload từ người dùng"],
            "rag_integration_status": "đã tích hợp nội dung từ 2 tài liệu vector store và file upload từ người dùng",
            "has_uploaded_content": True
        },
        "slides": [
            {
                "slide_id": 1,
                "type": "title",
                "title": "Hàm số bậc nhất",
                "content": ["Bài học dành cho học sinh lớp 10", "Khái niệm và tính chất cơ bản"],
                "tts_script": "Chào mừng các em học sinh lớp 10 đến với bài học về hàm số bậc nhất. Hôm nay chúng ta sẽ tìm hiểu về khái niệm và tính chất cơ bản của hàm số bậc nhất.",
                "image_keywords": ["mathematics", "function", "graph", "high school"],
                "source_references": ["Sách giáo khoa Toán 10 trang 45"],
                "content_extracted_from": "Định nghĩa từ sách giáo khoa và file upload"
            },
            {
                "slide_id": 2,
                "type": "content",
                "title": "Định nghĩa",
                "content": ["Hàm số bậc nhất có dạng y = ax + b", "Với a ≠ 0", "a: hệ số góc", "b: tung độ gốc"],
                "tts_script": "Theo định nghĩa trong sách giáo khoa, hàm số bậc nhất có dạng y bằng a x cộng b, trong đó a khác 0. Ở đây a được gọi là hệ số góc, còn b được gọi là tung độ gốc.",
                "image_keywords": ["formula", "equation", "linear", "coefficient"],
                "source_references": ["Sách giáo khoa Toán 10 trang 46", "File upload slide 3"],
                "content_extracted_from": "Công thức từ sách giáo khoa, ví dụ từ file upload"
            },
            {
                "slide_id": 3,
                "type": "example",
                "title": "Ví dụ minh họa",
                "content": ["Cho hàm số y = 2x + 3", "Xác định hệ số góc a = 2", "Xác định tung độ gốc b = 3"],
                "tts_script": "Lấy ví dụ cụ thể từ tài liệu: Cho hàm số y bằng 2x cộng 3. Ta có hệ số góc a bằng 2 và tung độ gốc b bằng 3.",
                "image_keywords": ["example", "calculation", "graph plotting"],
                "source_references": ["File upload ví dụ 1"],
                "content_extracted_from": "Ví dụ minh họa từ tài liệu người dùng upload"
            },
            {
                "slide_id": 4,
                "type": "exercise",
                "title": "Bài tập thực hành",
                "content": ["Bài 1: Cho y = -3x + 5, tìm a và b", "Bài 2: Vẽ đồ thị hàm số y = x - 2"],
                "tts_script": "Bây giờ các em hãy thực hành với hai bài tập được lấy từ tài liệu tham khảo. Bài 1: Cho y bằng âm 3x cộng 5, hãy tìm hệ số góc a và tung độ gốc b.",
                "image_keywords": ["exercise", "practice", "homework", "graph paper"],
                "source_references": ["Sách bài tập Toán 10", "File upload bài tập"],
                "content_extracted_from": "Bài tập từ sách tham khảo và file upload"
            }
        ],
        "rag_sources": [
            {
                "source_id": "rag_1",
                "source_type": "vector_store",
                "title": "Sách giáo khoa Toán 10",
                "content_preview": "Hàm số bậc nhất là hàm số có dạng y = ax + b trong đó a, b là các số thực và a ≠ 0...",
                "metadata": {"subject": "Toán", "grade": "10", "chapter": "Hàm số"}
            },
            {
                "source_id": "rag_2", 
                "source_type": "vector_store",
                "title": "Sách bài tập Toán 10",
                "content_preview": "Bài tập 1: Xác định hệ số góc và tung độ gốc của các hàm số sau...",
                "metadata": {"subject": "Toán", "grade": "10", "type": "exercises"}
            }
        ],
        "content_integration": {
            "uploaded_files_used": True,
            "rag_documents_found": 2,
            "total_sources": 3
        }
    }
    
    return JSONResponse(content=sample)

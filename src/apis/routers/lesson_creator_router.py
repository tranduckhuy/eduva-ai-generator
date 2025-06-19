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
    files: List[UploadFile] = File(None, description="Tài liệu tham khảo (PDF, DOCX, hình ảnh)")
):
    """
    API tạo slide cho học sinh cấp 3 với RAG, TTS script và image keywords
    
    Input:
    - topic: Chủ đề bài học cần tạo slide cho học sinh cấp 3
    - files: Tài liệu tham khảo tùy chọn (PDF, DOCX, hình ảnh)
    
    Output:
    - slide_data: Dữ liệu slide có cấu trúc với TTS và image keywords
    - selected_documents: Tài liệu RAG đã sử dụng
    """
    try:
        logger.info(f"Creating slides for high school topic: {topic}")
        
        # Preprocess messages with file attachments if provided
        enhanced_topic = topic
        if files and len(files) > 0:
            # Filter out None values from files list
            valid_files = [f for f in files if f is not None and f.filename]
            if valid_files:
                logger.info(f"Processing {len(valid_files)} attached files")
                processed_message = await preprocess_messages(topic, valid_files)
                
                # Extract text content and enhance topic
                if processed_message.get("content"):
                    text_parts = [part.get("text", "") for part in processed_message["content"] if part.get("type") == "text"]
                    if text_parts:
                        enhanced_topic = " ".join(text_parts)
                    
                    # Add context about attached files
                    file_types = [f.content_type for f in valid_files if f.content_type]
                    if file_types:
                        enhanced_topic += f"\n\nTài liệu đính kèm: {', '.join(set(file_types))}"
        
        # Add high school context to the topic
        high_school_context = f"Tạo bài giảng cho học sinh cấp 3 (lớp 10-12) về chủ đề: {enhanced_topic}. Nội dung phù hợp với trình độ học sinh trung học phổ thông, có ví dụ minh họa và bài tập thực hành."
        
        result = await run_slide_creator(topic=high_school_context)
        
        if result["success"]:
            return JSONResponse(
                content={
                    "success": True,
                    "slide_data": result["slide_data"],
                    "selected_documents": result["selected_documents"],
                    "message": f"Đã tạo bài giảng cấp 3 với {result['slide_data'].get('lesson_info', {}).get('slide_count', 0)} slides",
                    "files_processed": len([f for f in (files or []) if f is not None and f.filename])
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": result["error"],
                    "message": "Lỗi khi tạo slide cho học sinh cấp 3"
                }
            )
            
    except Exception as e:
        logger.error(f"Error in high school slide creator API: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": str(e),
                "message": "Lỗi hệ thống khi tạo slide cấp 3"
            }
        )

@router.get("/slide-creator/sample")
async def get_sample_slide():
    """Trả về mẫu cấu trúc slide cho học sinh cấp 3"""
    sample = {
        "lesson_info": {
            "title": "Hàm số bậc nhất - Toán lớp 10",
            "slide_count": 4,
            "target_level": "Cấp 3 (lớp 10-12)"
        },
        "slides": [
            {
                "slide_id": 1,
                "type": "title",
                "title": "Hàm số bậc nhất",
                "content": ["Bài học dành cho học sinh lớp 10", "Khái niệm và tính chất cơ bản"],
                "tts_script": "Chào mừng các em học sinh lớp 10 đến với bài học về hàm số bậc nhất. Hôm nay chúng ta sẽ tìm hiểu về khái niệm và tính chất cơ bản của hàm số bậc nhất.",
                "image_keywords": ["mathematics", "function", "graph", "high school"]
            },
            {
                "slide_id": 2,
                "type": "content",
                "title": "Định nghĩa",
                "content": ["Hàm số bậc nhất có dạng y = ax + b", "Với a ≠ 0", "a: hệ số góc", "b: tung độ gốc"],
                "tts_script": "Hàm số bậc nhất có dạng y bằng a x cộng b, trong đó a khác 0. Ở đây a được gọi là hệ số góc, còn b được gọi là tung độ gốc.",
                "image_keywords": ["formula", "equation", "linear", "coefficient"]
            },
            {
                "slide_id": 3,
                "type": "example",
                "title": "Ví dụ minh họa",
                "content": ["Cho hàm số y = 2x + 3", "Xác định hệ số góc a = 2", "Xác định tung độ gốc b = 3"],
                "tts_script": "Ví dụ: Cho hàm số y bằng 2x cộng 3. Ta có hệ số góc a bằng 2 và tung độ gốc b bằng 3.",
                "image_keywords": ["example", "calculation", "graph plotting"]
            },
            {
                "slide_id": 4,
                "type": "exercise",
                "title": "Bài tập thực hành",
                "content": ["Bài 1: Cho y = -3x + 5, tìm a và b", "Bài 2: Vẽ đồ thị hàm số y = x - 2"],
                "tts_script": "Bây giờ các em hãy thực hành với hai bài tập. Bài 1: Cho y bằng âm 3x cộng 5, hãy tìm hệ số góc a và tung độ gốc b. Bài 2: Vẽ đồ thị hàm số y bằng x trừ 2.",
                "image_keywords": ["exercise", "practice", "homework", "graph paper"]
            }
        ]
    }
    
    return JSONResponse(content=sample)

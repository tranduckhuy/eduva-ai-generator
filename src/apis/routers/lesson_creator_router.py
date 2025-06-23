from fastapi import APIRouter, status, Form, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Optional, List
import tempfile
import os
from src.agents.lesson_creator.flow import run_slide_creator
from src.utils.logger import logger
from src.config.enums import SubjectEnum, GradeEnum

# Simplified document loaders
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/slide-creator")
async def create_slides(
    topic: str = Form(..., description="Chủ đề cần tạo slide"),
    subject: Optional[SubjectEnum] = Form(None, description="Môn học"),
    grade: Optional[GradeEnum] = Form(None, description="Lớp (10, 11, 12)"),
    files: List[UploadFile] = File(None, description="Tài liệu tham khảo")
):
    """API tạo slide cho học sinh cấp 3"""
    try:
        logger.info(f"Creating slides for: {topic}, subject: {subject}, grade: {grade}")
        
        # Extract content from uploaded files
        uploaded_content = ""
        if files:
            valid_files = [f for f in files if f and f.filename]
            
            for file in valid_files:
                try:
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
                        content = await file.read()
                        temp_file.write(content)
                        temp_file_path = temp_file.name
                    
                    try:
                        # Load based on file type
                        if file.filename.lower().endswith('.pdf'):
                            loader = PyMuPDFLoader(temp_file_path)
                        elif file.filename.lower().endswith(('.docx', '.doc')):
                            loader = Docx2txtLoader(temp_file_path)
                        else:
                            loader = TextLoader(temp_file_path, encoding='utf-8')
                        
                        documents = loader.load()
                        file_text = "\n".join([doc.page_content for doc in documents])
                        
                        uploaded_content += f"\n=== {file.filename} ===\n{file_text}\n"
                        
                    finally:
                        os.unlink(temp_file_path)
                    
                except Exception as e:
                    logger.error(f"Error processing {file.filename}: {e}")
          # Create slides với metadata filter
        result = await run_slide_creator(
            topic=topic,
            subject=subject.value if subject else None,
            grade=grade.value if grade else None,
            uploaded_files_content=uploaded_content if uploaded_content.strip() else None
        )
        
        if result["success"]:
            slide_data = result["slide_data"]
            return JSONResponse(content={
                "success": True,
                "slide_data": slide_data,
                "message": f"Tạo thành công {slide_data.get('lesson_info', {}).get('slide_count', 0)} slides"
            })
        else:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"success": False, "error": result["error"]}
            )
            
    except Exception as e:
        logger.error(f"Router error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "error": str(e)}
        )

@router.get("/slide-creator/sample")
async def get_sample_slide():
    """Trả về mẫu cấu trúc slide"""
    sample = {
        "lesson_info": {
            "title": "Hàm số bậc nhất - Toán lớp 10",
            "slide_count": 3,
            "target_level": "Cấp 3",
            "estimated_duration_minutes": 15
        },
        "slides": [
            {
                "slide_id": 1,
                "type": "title",
                "title": "Hàm số bậc nhất",
                "content": ["Bài học dành cho học sinh lớp 10"],
                "tts_script": "Chào mừng các em học sinh lớp 10 đến với bài học về hàm số bậc nhất hôm nay.",
                "image_keywords": ["mathematics", "function", "high school"],
                "estimated_duration_seconds": 90
            },
            {
                "slide_id": 2,
                "type": "content",
                "title": "Định nghĩa",
                "content": ["Hàm số bậc nhất có dạng y = ax + b", "Với a khác 0"],
                "tts_script": "Hàm số bậc nhất có dạng y bằng a x cộng b, trong đó a khác 0.",
                "image_keywords": ["formula", "equation", "linear"],
                "estimated_duration_seconds": 120
            }
        ]
    }
    
    return JSONResponse(content=sample)

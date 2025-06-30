from fastapi import APIRouter, HTTPException, Form, UploadFile, File, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import tempfile
from datetime import datetime

from src.services.video_generator import VideoGenerator
from src.services.tts_service import TTSService
from src.agents.lesson_creator.flow import run_slide_creator
from src.config.enums import SubjectEnum, GradeEnum, DurationEnum
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader
from src.utils.logger import logger

router = APIRouter(prefix="/video", tags=["video"])

class VideoFromSlideDataRequest(BaseModel):
    lesson_data: Dict[str, Any]
    voice_config: Optional[Dict[str, Any]] = None

class VoiceConfig(BaseModel):
    language_code: str = "vi-VN"
    name: Optional[str] = None  # Specific voice name like "vi-VN-Neural2-A"
    speaking_rate: float = 1.0  # 0.25 to 4.0

@router.get("/voices")
async def get_available_voices(language_code: Optional[str] = None):
    """Get available voices from Google Cloud TTS"""
    try:
        voices = TTSService.get_available_voices(language_code)
        return JSONResponse(content={
            "success": True,
            "voices": voices,
            "total_count": len(voices)
        })
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "error": str(e)}
        )

@router.get("/voices/vietnamese")
async def get_vietnamese_voices():
    """Get Vietnamese voices specifically"""
    try:
        voices = TTSService.get_available_voices("vi")
        
        # Filter and organize Vietnamese voices
        vietnamese_voices = []
        for voice in voices:
            if voice["language_code"].startswith("vi"):
                vietnamese_voices.append(voice)
        
        return JSONResponse(content={
            "success": True,
            "voices": vietnamese_voices,
            "total_count": len(vietnamese_voices),
            "popular_voices": [
                {"name": "vi-VN-Neural2-A", "gender": "FEMALE", "type": "Neural"},
                {"name": "vi-VN-Neural2-D", "gender": "MALE", "type": "Neural"},
                {"name": "vi-VN-Standard-A", "gender": "FEMALE", "type": "Standard"},
                {"name": "vi-VN-Standard-B", "gender": "MALE", "type": "Standard"},
                {"name": "vi-VN-Standard-C", "gender": "FEMALE", "type": "Standard"},
                {"name": "vi-VN-Standard-D", "gender": "MALE", "type": "Standard"}
            ]
        })
    except Exception as e:
        logger.error(f"Error getting Vietnamese voices: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "error": str(e)}
        )

@router.post("/generate-from-topic")
async def generate_video_from_topic(
    topic: str = Form(..., description="Chủ đề cần tạo video"),
    subject: Optional[SubjectEnum] = Form(None, description="Môn học"),
    grade: Optional[GradeEnum] = Form(None, description="Lớp (10, 11, 12)"),
    duration: DurationEnum = Form(DurationEnum.DURATION_5_MIN, description="Thời lượng video mong muốn"),
    files: List[UploadFile] = File(None, description="Tài liệu tham khảo"),
    voice_name: Optional[str] = Form(None, description="Tên voice cụ thể (vd: vi-VN-Neural2-A)"),
    speaking_rate: float = Form(1.0, description="Tốc độ nói (0.25-4.0)")
):
    """API tạo video từ topic, tương tự slide-creator nhưng trả về video"""
    try:
        logger.info(f"Generating video for: {topic}, subject: {subject}, grade: {grade}")
        
        # Extract content from uploaded files (giống slide-creator)
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
        
        # Bước 1: Tạo slide data từ RAG
        logger.info("Step 1: Creating slide data...")
        slide_result = await run_slide_creator(
            topic=topic,
            subject=subject.value if subject else None,
            grade=grade.value if grade else None,
            duration=duration.value,
            uploaded_files_content=uploaded_content if uploaded_content.strip() else None
        )

        if not slide_result["success"]:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"success": False, "error": f"Failed to create slides: {slide_result['error']}"}
            )
        
        lesson_data = slide_result["slide_data"]
          # Bước 2: Generate video từ slide data
        logger.info("Step 2: Generating video from slides...")
          # Prepare voice configuration
        voice_config = {
            "language_code": "vi-VN",  # Fixed to Vietnamese
            "name": voice_name,
            "speaking_rate": speaking_rate
        }
        
        video_generator = VideoGenerator(voice_config=voice_config)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        video_filename = f"lesson_{timestamp}.mp4"
        
        # Create temp directory for video
        # with tempfile.TemporaryDirectory() as temp_dir:
        #     temp_video_path = os.path.join(temp_dir, video_filename)
            
        #     # Generate video
        #     await video_generator.generate_lesson_video(lesson_data, temp_video_path)
            
        #     # TODO: Upload to Azure or return video data
        #     # For now, we'll return the slide data and success message
        #     # In production, you would upload the video file to Azure Blob Storage
            
        #     return JSONResponse(content={
        #         "success": True,
        #         "lesson_data": lesson_data,
        #         "video_info": {
        #             "filename": video_filename,
        #             "message": "Video generated successfully",
        #             "slide_count": lesson_data.get('lesson_info', {}).get('slide_count', 0),
        #             "estimated_duration": lesson_data.get('lesson_info', {}).get('estimated_duration_minutes', 0)
        #         }
        #         # In production: "video_url": azure_blob_url
        #     })

        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(base_dir, "temp_videos")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, video_filename)
        
        # Tạo video và lưu tại output_path
        await video_generator.generate_lesson_video(lesson_data, output_path)
        
        logger.info(f"Video generated successfully: {output_path}")

        # Trả về thông tin video (sau này bạn có thể thêm upload hoặc trả url)
        return JSONResponse(content={
            "success": True,
            "lesson_data": lesson_data,
            "video_info": {
                "filename": video_filename,
                "message": "Video generated successfully",
                "saved_path": output_path,  # Đường dẫn file video
                "slide_count": lesson_data.get('lesson_info', {}).get('slide_count', 0),
                "estimated_duration": lesson_data.get('lesson_info', {}).get('estimated_duration_minutes', 0)
            }
        })
            
    except Exception as e:
        logger.error(f"Error generating video from topic: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "error": str(e)}
        )

@router.post("/generate-from-slides")
async def generate_video_from_slides(request: VideoFromSlideDataRequest):
    """API tạo video từ slide data có sẵn"""
    try:
        logger.info("Generating video from provided slide data...")
        
        # Validate lesson data
        if not request.lesson_data.get('slides'):
            raise HTTPException(status_code=400, detail="No slides found in lesson data")
          # Generate video
        video_generator = VideoGenerator(voice_config=request.voice_config)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        video_filename = f"lesson_{timestamp}.mp4"
        
        # Create temp directory for video
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_video_path = os.path.join(temp_dir, video_filename)
            
            # Generate video
            await video_generator.generate_lesson_video(request.lesson_data, temp_video_path)
            
            # TODO: Upload to Azure or return video data
            # For now, we'll return success message
            
            return JSONResponse(content={
                "success": True,
                "video_info": {
                    "filename": video_filename,
                    "message": "Video generated successfully from slide data",
                    "slide_count": len(request.lesson_data.get('slides', [])),
                    "title": request.lesson_data.get('lesson_info', {}).get('title', 'Unknown')
                }
                # In production: "video_url": azure_blob_url
            })
            
    except Exception as e:
        logger.error(f"Error generating video from slides: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "error": str(e)}
        )

@router.get("/templates")
async def get_available_templates():
    """Get available slide templates"""
    try:
        video_generator = VideoGenerator()
        templates = video_generator.slide_processor.image_generator.get_available_templates()
        
        return JSONResponse(content={
            "success": True,
            "templates": templates,
            "current_template": video_generator.slide_processor.image_generator.template_manager.current_template
        })
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "error": str(e)}
        )

class VideoWithTemplateRequest(BaseModel):
    lesson_data: Dict[str, Any]
    template_name: Optional[str] = "modern_blue"
    voice_config: Optional[Dict[str, Any]] = None

@router.post("/generate-with-template")
async def generate_video_with_template(request: VideoWithTemplateRequest):
    """Generate video with specific template"""
    try:
        # Initialize video generator with template
        voice_config = request.voice_config or {}
        video_generator = VideoGenerator(voice_config=voice_config)
        
        # Set template
        if request.template_name:
            video_generator.slide_processor.image_generator.set_template(request.template_name)
            logger.info(f"Using template: {request.template_name}")
        
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"lesson_{timestamp}.mp4"
        output_path = os.path.join("src", "apis", "routers", "temp_videos", output_filename)
        
        # Ensure temp directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate video
        video_path = await video_generator.generate_lesson_video(request.lesson_data, output_path)
        
        return JSONResponse(content={
            "success": True,
            "video_path": video_path,
            "filename": output_filename,
            "template_used": request.template_name,
            "slides_count": len(request.lesson_data.get('slides', [])),
            "message": f"Video generated successfully with {request.template_name} template"
        })
        
    except Exception as e:
        logger.error(f"Error generating video with template: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "error": str(e)}
        )

from fastapi import APIRouter, status, Depends, UploadFile, Form
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import json
import time
from langchain_core.messages.ai import AIMessageChunk
from src.agents.lesson_creator.flow import lesson_creator_agent
from src.agents.lesson_creator.func import create_enhanced_slide_data, create_fallback_slide_data
from src.utils.logger import logger
from src.utils.helper import preprocess_messages

router = APIRouter(prefix="/ai", tags=["AI"])


async def message_generator(input_graph: dict, config: dict):
    last_output_state = None
    temp = ""
    async for event in lesson_creator_agent.astream(
        input=input_graph,
        stream_mode=["messages", "values"],
        config=config,
    ):
        event_type, event_message = event
        if event_type == "messages":
            message, metadata = event_message
            if isinstance(message, AIMessageChunk) and metadata["langgraph_node"] in [
                "generate_answer_rag"
            ]:
                temp += message.content
                yield json.dumps(
                    {
                        "type": "message",
                        "content": temp,
                    },
                    ensure_ascii=False,
                ) + "\n\n"
        if event_type == "values":
            last_output_state = event_message

    if last_output_state is None:
        raise ValueError("No output state received from workflow")

    if "messages" not in last_output_state:
        raise ValueError("No LLM response in output")

    # Prepare final response with structured slide data
    final_response_data = {
        "final_response": last_output_state["messages"][-1].content,
        "selected_ids": last_output_state.get("selected_ids", []),
        "selected_documents": last_output_state.get("selected_documents", []),
        "slide_data": last_output_state.get("slide_data", {}),  # Structured data for pipeline
    }

    final_response = json.dumps(
        {
            "type": "final",
            "content": final_response_data,
        },
        ensure_ascii=False,
    )
    yield final_response + "\n\n"


@router.post("/video-lesson-creator/stream")
async def video_lesson_creator_stream(
    query: str = Form(..., description="Yêu cầu tạo bài giảng của giáo viên (môn học, chủ đề, lớp)"),
    teacher_email: str = Form(None, description="Email của giáo viên"),
    lesson_id: Optional[str] = Form(None, description="ID bài giảng (để lưu lịch sử)"),
    attachs: List[UploadFile] = [],
):
    """
    API endpoint để hỗ trợ giáo viên tạo video bài giảng cho học sinh cấp 3.
    
    Trả về:
    - Stream content: Nội dung bài giảng được tạo real-time
    - Final response: 
      * final_response: Text content hoàn chỉnh
      * slide_data: Structured JSON data cho TTS + Video pipeline
      * selected_documents: Tài liệu tham khảo đã sử dụng
    
    Ví dụ yêu cầu:
    - "Tạo bài giảng Toán lớp 10 về hàm số bậc nhất, 20 phút"
    - "Cần slide Vật lý lớp 11 về dao động điều hòa với ví dụ"
    - "Hỗ trợ tạo video Hóa học lớp 12 về phản ứng axit-bazơ"
    """
    try:
        messages = await preprocess_messages(query, attachs)

        config = {
            "configurable": {
                "thread_id": lesson_id,
                "teacher_email": teacher_email,
            }
        }
        input_graph = {
            "messages": messages,
        }

        return StreamingResponse(
            message_generator(
                input_graph=input_graph,
                config=config,
            ),
            media_type="text/event-stream",
        )
    except Exception as e:
        logger.error(f"Error in video lesson creator endpoint: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Video lesson creation error: {str(e)}"},
        )


@router.post("/video-lesson-creator/create")
async def create_video_lesson(
    query: str = Form(..., description="Yêu cầu tạo bài giảng"),
    teacher_email: str = Form(None),
    lesson_id: Optional[str] = Form(None),
    attachs: List[UploadFile] = [],
):
    """
    Non-streaming endpoint để tạo bài giảng và trả về structured JSON data
    """
    try:
        messages = await preprocess_messages(query, attachs)

        config = {
            "configurable": {
                "thread_id": lesson_id,
                "teacher_email": teacher_email,
            }
        }
        input_graph = {"messages": messages}

        # Get complete response
        response = await lesson_creator_agent.ainvoke(input_graph, config)
        
        slide_data = response.get("slide_data", {})
        
        # Return JSON only
        return JSONResponse(
            content={
                "success": True,
                "format": "json",
                "slide_data": slide_data,
                "final_response": response["messages"][-1].content,
                "selected_documents": response.get("selected_documents", []),
                "selected_ids": response.get("selected_ids", [])
            }
        )

    except Exception as e:
        logger.error(f"Error creating video lesson: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "error": "System error during video lesson creation"},
        )


# Giữ lại endpoint cũ để backward compatibility
@router.post("/rag_agent_template/stream")
async def rag_agent_template_stream(
    query: str = Form(...),
    email: str = Form(None),
    conversation_id: Optional[str] = Form(None),
    attachs: List[UploadFile] = [],
):
    # Redirect to new endpoint
    return await video_lesson_creator_stream(
        query=query,
        teacher_email=email,
        lesson_id=conversation_id,
        attachs=attachs
    )


@router.post("/lesson-creator/json")
async def create_lesson_json(
    query: str = Form(..., description="Yêu cầu tạo bài giảng (môn học, chủ đề, lớp, thời lượng)"),
    teacher_email: str = Form(None, description="Email của giáo viên"),
    lesson_id: Optional[str] = Form(None, description="ID bài giảng"),
    attachs: List[UploadFile] = [],
):
    """
    API endpoint chuyên dụng trả về structured JSON data hoàn chỉnh cho việc tạo bài học tự động.
    
    Dữ liệu trả về bao gồm:
    - lesson_info: Thông tin chi tiết bài học (môn, lớp, thời lượng, mục tiêu)
    - slides: Mảng slide với nội dung đầy đủ, TTS script, metadata hình ảnh
    - metadata: Cấu hình TTS và thông tin kỹ thuật
    
    Output JSON structure phù hợp cho:
    - Text-to-Speech (TTS) engine
    - AI image selection và generation
    - Video pipeline automation
    
    Ví dụ request:
    - "Tạo bài giảng Toán lớp 10 về hàm số bậc nhất, 25 phút"
    - "Cần nội dung Vật lý lớp 11 về dao động điều hòa, 30 phút"
    - "Hóa học lớp 12 phản ứng axit-bazơ, 20 phút với ví dụ thực tế"
    """
    try:
        messages = await preprocess_messages(query, attachs)

        config = {
            "configurable": {
                "thread_id": lesson_id or f"lesson_{int(time.time())}",
                "teacher_email": teacher_email,
            }
        }
        input_graph = {"messages": messages}

        # Get complete response from RAG agent
        response = await lesson_creator_agent.ainvoke(input_graph, config)
        
        # Extract structured slide data
        slide_data = response.get("slide_data", {})
        
        # Ensure we have complete structured data
        if not slide_data or "lesson_info" not in slide_data:
            # Fallback: create structured data from final response
            final_response = response["messages"][-1].content if response.get("messages") else ""
            slide_data = create_enhanced_slide_data(final_response)
        
        # Add additional metadata for the API response
        api_response = {
            "success": True,
            "timestamp": "2025-06-08T00:00:00Z",
            "lesson_data": slide_data,
            "api_metadata": {
                "teacher_email": teacher_email,
                "lesson_id": lesson_id,
                "generation_method": "RAG_AI_Agent",
                "content_sources": response.get("selected_ids", []),
                "ready_for_automation": True
            },
            "usage_instructions": {
                "slides_array": "Sử dụng lesson_data.slides để tạo slide presentation",
                "tts_scripts": "Mỗi slide có tts_script.text cho Text-to-Speech",
                "image_metadata": "visual_elements.image_suggestions chứa metadata cho AI chọn ảnh",
                "duration": "Mỗi slide có duration_seconds để lập timeline video"
            }
        }
        
        return JSONResponse(
            content=api_response,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Cache-Control": "no-cache",
                "X-Content-Source": "RAG-AI-Agent"
            }
        )

    except Exception as e:
        logger.error(f"Error in lesson JSON creator: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": str(e),
                "fallback_data": create_fallback_slide_data("Lỗi trong quá trình tạo bài giảng"),
                "timestamp": "2025-06-08T00:00:00Z"
            }
        )


@router.get("/lesson-creator/sample-json")
async def get_sample_lesson_json():
    """
    Trả về mẫu JSON structure để developers hiểu format dữ liệu
    """
    sample_data = {
        "lesson_info": {
            "title": "Hàm số bậc nhất",
            "subject": "Toán",
            "grade": "lớp 10",
            "duration_minutes": 25,
            "estimated_slides": 6,
            "difficulty_level": "intermediate",
            "learning_objectives": [
                "Hiểu được định nghĩa hàm số bậc nhất y = ax + b",
                "Vẽ được đồ thị hàm số bậc nhất",
                "Xác định các tính chất cơ bản của hàm số bậc nhất",
                "Giải được các bài tập về hàm số bậc nhất"
            ]
        },
        "slides": [
            {
                "slide_id": 1,
                "type": "title",
                "title": "Hàm số bậc nhất",
                "subtitle": "Toán - lớp 10",
                "content": [
                    "Giới thiệu khái niệm hàm số bậc nhất",
                    "Biểu thức tổng quát: y = ax + b",
                    "Đặc điểm của đồ thị hàm số bậc nhất"
                ],
                "duration_seconds": 30,
                "tts_script": {
                    "text": "Xin chào các em học sinh lớp 10! Hôm nay cô sẽ cùng các em tìm hiểu về hàm số bậc nhất trong môn Toán. Đây là một chủ đề rất quan trọng và là nền tảng cho nhiều kiến thức toán học khác. Các em hãy chuẩn bị tinh thần để cùng cô khám phá những điều thú vị về hàm số bậc nhất nhé!",
                    "speed": "normal",
                    "pause_duration": 2.0
                },
                "visual_elements": {
                    "background_color": "#f8f9fa",
                    "text_color": "#212529",
                    "font_size": "large",
                    "layout": "center",
                    "image_suggestions": [
                        {
                            "type": "mathematical_graph",
                            "description": "Đồ thị hàm số bậc nhất y = ax + b với đường thẳng màu xanh",
                            "keywords": ["linear function", "graph", "y=ax+b", "coordinate system", "mathematics"],
                            "position": "top-right",
                            "size": "medium"
                        }
                    ]
                },
                "transitions": {
                    "entrance": "fade",
                    "exit": "slide-left"
                }
            },
            {
                "slide_id": 2,
                "type": "content",
                "title": "Định nghĩa hàm số bậc nhất",
                "content": [
                    "Hàm số bậc nhất có dạng y = ax + b, trong đó a khác 0",
                    "Hệ số a được gọi là hệ số góc, b là tung độ gốc",
                    "Tập xác định của hàm số bậc nhất là toàn bộ tập số thực"
                ],
                "duration_seconds": 90,
                "tts_script": {
                    "text": "Chúng ta bắt đầu với định nghĩa cơ bản nhất. Hàm số bậc nhất là hàm số có dạng y bằng a nhân x cộng b, trong đó a khác 0. Ở đây, a được gọi là hệ số góc, còn b là hằng số, hay còn gọi là tung độ gốc. Điều quan trọng các em cần nhớ là a phải khác 0, nếu a bằng 0 thì đây không còn là hàm số bậc nhất nữa. Tập xác định của hàm số bậc nhất là toàn bộ tập số thực.",
                    "speed": "normal",
                    "pause_duration": 1.5
                },
                "visual_elements": {
                    "background_color": "#ffffff",
                    "text_color": "#333333",
                    "font_size": "medium",
                    "layout": "bullet-points",
                    "image_suggestions": [
                        {
                            "type": "formula_illustration",
                            "description": "Công thức y = ax + b được viết rõ ràng với các tham số a và b được làm nổi bật",
                            "keywords": ["formula", "y=ax+b", "parameters", "mathematics", "definition"],
                            "position": "right",
                            "size": "large"
                        }
                    ]
                },
                "transitions": {
                    "entrance": "slide-right",
                    "exit": "slide-left"
                }
            }
        ],
        "metadata": {
            "created_timestamp": "2025-06-08T00:00:00Z",
            "total_duration_seconds": 750,
            "slide_count": 6,
            "content_source": "AI-generated with educational documents",
            "tts_voice_settings": {
                "voice_type": "vietnamese_female_teacher",
                "speech_rate": 1.0,
                "pitch": 0.0,
                "volume": 0.8
            }
        }
    }
    
    return JSONResponse(
        content={
            "description": "Sample JSON structure for lesson creation",
            "version": "1.0",
            "sample_data": sample_data,
            "field_descriptions": {
                "lesson_info": "Thông tin tổng quan về bài học",
                "slides": "Mảng chứa toàn bộ slide với nội dung chi tiết",
                "slide.tts_script": "Script đầy đủ cho Text-to-Speech engine",
                "slide.visual_elements": "Metadata để AI chọn và tạo hình ảnh phù hợp",
                "slide.duration_seconds": "Thời gian dự kiến cho mỗi slide",
                "metadata.tts_voice_settings": "Cài đặt giọng nói cho TTS"
            }
        }
    )

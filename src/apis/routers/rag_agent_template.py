from fastapi import APIRouter, status, Depends, UploadFile, Form
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import json
from langchain_core.messages.ai import AIMessageChunk
from src.agents.rag_agent_template.flow import rag_agent_template_agent
from src.utils.logger import logger
from src.utils.helper import preprocess_messages

router = APIRouter(prefix="/ai", tags=["AI"])


async def message_generator(input_graph: dict, config: dict):
    last_output_state = None
    temp = ""
    async for event in rag_agent_template_agent.astream(
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
      * slide_data: Structured JSON data cho RevealJS + TTS + Video pipeline
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
    output_format: str = Form("json", description="Format đầu ra: 'json' hoặc 'revealjs'"),
    attachs: List[UploadFile] = [],
):
    """
    Non-streaming endpoint để tạo bài giảng và trả về structured data
    
    Params:
    - output_format: 
      * "json": Trả về raw JSON data
      * "revealjs": Trả về RevealJS HTML ready-to-use
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
        response = await rag_agent_template_agent.ainvoke(input_graph, config)
        
        slide_data = response.get("slide_data", {})
        
        if output_format == "revealjs":
            # Convert to RevealJS format
            revealjs_html = convert_to_revealjs(slide_data)
            return JSONResponse(
                content={
                    "success": True,
                    "format": "revealjs",
                    "html_content": revealjs_html,
                    "slide_data": slide_data,
                    "selected_documents": response.get("selected_documents", [])
                }
            )
        else:
            # Return raw JSON
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
            content={"success": False, "error": str(e)}
        )


def convert_to_revealjs(slide_data: dict) -> str:
    """
    Convert structured slide data to RevealJS HTML format
    """
    if not slide_data or "slides" not in slide_data:
        return "<div>No slide data available</div>"
    
    lesson_info = slide_data.get("lesson_info", {})
    slides = slide_data.get("slides", [])
    
    html_slides = []
    
    for slide in slides:
        slide_type = slide.get("type", "content")
        title = slide.get("title", "")
        content = slide.get("content", "")
        visual_elements = slide.get("visual_elements", {})
        
        # Create slide HTML based on type
        if slide_type == "title":
            slide_html = f"""
            <section data-background-color="{visual_elements.get('background_color', '#ffffff')}">
                <h1>{title}</h1>
                <h3>{lesson_info.get('subject', '')} - {lesson_info.get('grade', '')}</h3>
                <p>{content}</p>
            </section>
            """
        elif slide_type == "summary":
            slide_html = f"""
            <section data-background-color="{visual_elements.get('background_color', '#ffffff')}">
                <h2>Tóm tắt</h2>
                <h3>{title}</h3>
                <div style="text-align: left;">
                    {content.replace(chr(10), '<br>')}
                </div>
            </section>
            """
        else:  # content, example
            slide_html = f"""
            <section data-background-color="{visual_elements.get('background_color', '#ffffff')}">
                <h2>{title}</h2>
                <div style="text-align: left; font-size: {visual_elements.get('text_size', 'medium')};">
                    {content.replace(chr(10), '<br>')}
                </div>
            </section>
            """
        
        html_slides.append(slide_html)
    
    # Complete RevealJS HTML
    revealjs_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{lesson_info.get('title', 'Bài giảng')}</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.3.1/dist/reveal.css">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4.3.1/dist/theme/white.css">
    </head>
    <body>
        <div class="reveal">
            <div class="slides">
                {''.join(html_slides)}
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/reveal.js@4.3.1/dist/reveal.js"></script>
        <script>
            Reveal.initialize({{
                hash: true,
                transition: 'slide'
            }});
        </script>
    </body>
    </html>
    """
    
    return revealjs_html

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

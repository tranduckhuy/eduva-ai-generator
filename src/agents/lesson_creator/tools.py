from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

from src.config.vector_store import vector_store
from src.utils.helper import convert_list_context_source_to_str
from src.utils.logger import logger

# ========== External tools ==========
duckduckgo_search = DuckDuckGoSearchRun()

@tool
def retrieve_document(query: str):
    """
    Truy xuất tài liệu giáo dục từ kho vector của nhà trường dựa trên nội dung truy vấn (chủ đề, môn học...).
    """
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 7, "score_threshold": 0.25},
    )
    documents = retriever.invoke(query)
    selected_documents = [doc.__dict__ for doc in documents]
    selected_ids = [doc["id"] for doc in selected_documents]
    context_str = convert_list_context_source_to_str(documents)

    return {
        "context_str": context_str,
        "selected_documents": selected_documents,
        "selected_ids": selected_ids,
    }


@tool
def create_structured_lesson_content(
    topic: str,
    grade_level: str,
    subject: str,
    duration_minutes: int = 30,
    content_outline: str = ""
):
    """
    Tạo dữ liệu JSON có cấu trúc cho bài giảng gồm nội dung slide, TTS script và đề xuất hình ảnh.
    """
    estimated_slides = max(4, min(duration_minutes // 2, 15))

    structured_lesson = {
        "lesson_info": {
            "title": topic,
            "subject": subject,
            "grade": grade_level,
            "duration_minutes": duration_minutes,
            "learning_objectives": [
                f"Hiểu được khái niệm cơ bản về {topic}",
                f"Áp dụng kiến thức {topic} vào bài tập thực tế"
            ]
        },
        "slides": [
            {
                "slide_id": 1,
                "type": "title",
                "title": topic,
                "content": [
                    f"Chào mừng các em học sinh lớp {grade_level} đến với bài học về {topic} trong môn {subject}."
                ],
                "duration_seconds": 30,
                "tts_script": {
                    "text": f"Xin chào các em học sinh {grade_level}! Hôm nay chúng ta sẽ cùng tìm hiểu về {topic} trong môn {subject}.",
                    "speed": "normal",
                    "pause_duration": 2.0
                },
                "visual_elements": {
                    "image_suggestions": [
                        {
                            "type": "subject_icon",
                            "description": f"Biểu tượng môn {subject}",
                            "keywords": [subject.lower(), "education", topic.lower()]
                        }
                    ]
                }
            },
            {
                "slide_id": 2,
                "type": "content",
                "title": f"Giới thiệu về {topic}",
                "content": [
                    "[NỘI DUNG SẼ ĐƯỢC AI ĐIỀN DỰA TRÊN TÀI LIỆU]",
                ],
                "duration_seconds": 180,
                "tts_script": {
                    "text": f"Đầu tiên, chúng ta cùng tìm hiểu {topic} là gì. [AI sẽ điền nội dung cụ thể]",
                    "speed": "normal",
                    "pause_duration": 1.5
                },
                "visual_elements": {
                    "image_suggestions": [
                        {
                            "type": "conceptual_diagram",
                            "description": f"Sơ đồ minh họa {topic}",
                            "keywords": [topic.lower(), subject.lower(), "diagram"]
                        }
                    ]
                }
            },
            {
                "slide_id": 3,
                "type": "example",
                "title": f"Ví dụ về {topic}",
                "content": "[AI SẼ TẠO VÍ DỤ CỤ THỂ]",
                "duration_seconds": 240,
                "tts_script": {
                    "text": f"Bây giờ cô sẽ đưa ra ví dụ cụ thể về {topic}. [AI sẽ điền ví dụ]",
                    "speed": "normal",
                    "pause_duration": 2.0
                },
                "visual_elements": {
                    "image_suggestions": [
                        {
                            "type": "example_illustration",
                            "description": f"Hình ảnh minh họa ví dụ {topic}",
                            "keywords": [topic.lower(), "example", subject.lower()]
                        }
                    ]
                }
            },
            {
                "slide_id": 4,
                "type": "summary",
                "title": "Tóm tắt bài học",
                "content": f"Điểm chính về {topic}: [AI sẽ điền tóm tắt]",
                "duration_seconds": 120,
                "tts_script": {
                    "text": f"Vậy là chúng ta đã tìm hiểu về {topic}. [AI sẽ điền tóm tắt cụ thể]",
                    "speed": "normal",
                    "pause_duration": 1.0
                },
                "visual_elements": {
                    "image_suggestions": [
                        {
                            "type": "summary_graphic",
                            "description": "Biểu đồ tóm tắt bài học",
                            "keywords": ["summary", subject.lower(), "education"]
                        }
                    ]
                }
            }
        ]
    }

    return structured_lesson

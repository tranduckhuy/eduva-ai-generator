from pydantic import BaseModel, Field
from typing import List

class Slide(BaseModel):
    slide_id: int = Field(..., description="ID tuần tự của slide, bắt đầu từ 1.")
    title: str = Field(..., description="Tiêu đề chính của slide.")
    content: List[str] = Field(..., description="Danh sách các điểm nội dung chính, mỗi điểm là một chuỗi.")
    tts_script: str = Field(..., description="Kịch bản chi tiết để chuyển thành giọng nói cho slide này.")
    image_keywords: List[str] = Field(..., description="Danh sách 3-5 từ khóa để tìm kiếm hình ảnh minh họa.")

class LessonInfo(BaseModel):
    title: str = Field(..., description="Tiêu đề chính của toàn bộ bài giảng.")
    slide_count: int = Field(..., description="Tổng số slide trong bài giảng.")
    target_level: str = Field(..., description="Đối tượng học sinh mục tiêu (ví dụ: 'Cấp 3 (lớp 10-12)').")
    total_words: int = Field(0, description="Tổng số từ trong tất cả các tts_script.")
    estimated_duration_minutes: float = Field(0.0, description="Thời lượng dự kiến của bài giảng (phút).")
    language: str = Field("vi-VN", description="Ngôn ngữ của bài giảng, mặc định là tiếng Việt.")

class SlideDeck(BaseModel):
    """Cấu trúc JSON hoàn chỉnh cho một bộ slide bài giảng."""
    lesson_info: LessonInfo = Field(..., description="Thông tin tổng quan về bài giảng.")
    slides: List[Slide] = Field(..., description="Danh sách tất cả các slide trong bài giảng.")
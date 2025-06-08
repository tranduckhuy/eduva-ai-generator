from langchain_core.tools import tool
from src.config.vector_store import vector_store
from src.utils.helper import convert_list_context_source_to_str
from src.utils.logger import logger
from langchain_core.runnables import RunnableConfig
from langchain_experimental.utilities import PythonREPL
from langchain_community.tools import DuckDuckGoSearchRun


duckduckgo_search = DuckDuckGoSearchRun()

python_exec = PythonREPL()


@tool
def retrieve_document(query: str):
    """Truy xuất tài liệu giáo dục từ cơ sở dữ liệu để hỗ trợ tạo nội dung bài giảng cho học sinh cấp 3.

    Args:
        query (str): Câu truy vấn tìm kiếm tài liệu giáo dục (môn học, chủ đề, lớp học)
    Returns:
        dict: Tài liệu giáo dục phù hợp và thông tin liên quan
    """
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 7, "score_threshold": 0.25},  # Tăng số lượng tài liệu và giảm threshold để có nhiều thông tin hơn
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
def create_slide_content(topic: str, grade_level: str, subject: str, content_outline: str = ""):
    """Tạo nội dung slide bài giảng linh hoạt dựa trên chủ đề và yêu cầu cụ thể của giáo viên.

    Args:
        topic (str): Chủ đề bài giảng
        grade_level (str): Cấp lớp (ví dụ: "lớp 10", "lớp 11", "lớp 12") 
        subject (str): Môn học (ví dụ: "Toán", "Lý", "Hóa", "Văn", "Sử", "Địa")
        content_outline (str): Outline nội dung cụ thể từ giáo viên (tùy chọn)
    Returns:
        str: Template slide linh hoạt để AI điền nội dung cụ thể
    """
    
    # Template slide linh hoạt cho AI điền nội dung
    slide_template = f"""
# TEMPLATE SLIDE CHO BÀI GIẢNG: {topic.upper()}

**Môn học:** {subject}
**Cấp lớp:** {grade_level}
**Chủ đề:** {topic}

## HƯỚNG DẪN TẠO SLIDE:

### SLIDE MỞ ĐẦU:
- Tiêu đề bài giảng
- Giới thiệu chủ đề
- Tạo sự hứng thú ban đầu

### CÁC SLIDE NỘI DUNG CHÍNH:
[Số lượng slide sẽ phụ thuộc vào độ phức tạp của chủ đề]
- Chia nhỏ kiến thức thành các phần logic
- Mỗi slide tập trung vào 1 ý chính
- Bao gồm ví dụ minh họa phù hợp với {grade_level}
- Sử dụng hình ảnh, biểu đồ khi cần thiết

### SLIDE KẾT THÚC:
- Tóm tắt các điểm quan trọng
- Câu hỏi kiểm tra hiểu bài
- Liên kết với bài học tiếp theo (nếu có)

## GHI CHÚ CHO GIÁO VIÊN:
- Điều chỉnh số lượng slide theo thời gian dự kiến
- Thêm hoạt động tương tác phù hợp với độ tuổi
- Chuẩn bị câu hỏi mở để kích thích tư duy học sinh

[Template này sẽ được AI sử dụng để tạo nội dung slide cụ thể dựa trên tài liệu giáo dục có sẵn]
"""
    
    return slide_template


@tool
def python_repl(code: str):
    """
    Thực thi mã Python để tính toán, xử lý dữ liệu hoặc tạo biểu đồ cho bài giảng.

    Args:
        code (str): Mã Python cần thực thi
    Returns:
        str: Kết quả thực thi mã Python
    """
    return python_exec.run(code)

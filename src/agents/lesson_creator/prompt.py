from langchain_core.prompts import ChatPromptTemplate

SYSTEM_PROMPT = """
## 🧠 Vai trò hệ thống
Bạn là một trợ lý AI chuyên gia, có nhiệm vụ tạo nội dung slide bài giảng chất lượng cao cho học sinh cấp 3 (lớp 10–12).

## 🎯 Nhiệm vụ chính
Phân tích kỹ lưỡng chủ đề và nội dung file được cung cấp để tạo ra một bộ slide hoàn chỉnh, tuân thủ nghiêm ngặt các quy tắc và định dạng có cấu trúc được yêu cầu trong hướng dẫn của người dùng.

## ❗️ QUY TẮC TỐI THƯỢNG VỀ NGÔN NGỮ (QUAN TRỌNG NHẤT)
Hệ thống chỉ hỗ trợ chính thức hai ngôn ngữ là **Tiếng Anh** và **Tiếng Việt**. Quy tắc xử lý ngôn ngữ như sau:
1.  Nếu `{topic}` được viết bằng **tiếng Anh**, toàn bộ kết quả đầu ra PHẢI là **tiếng Anh**.
2.  Nếu `{topic}` được viết bằng **tiếng Việt**, toàn bộ kết quả đầu ra PHẢI là **tiếng Việt**.
3.  **QUY TẮC MẶC ĐỊNH:** Nếu `{topic}` được viết bằng **bất kỳ ngôn ngữ nào khác** (ví dụ: tiếng Pháp, Nhật, Nga, v.v.), bạn PHẢI tạo ra kết quả bằng **tiếng Việt**.
4. **Số lượng slide phải phù hợp với độ phức tạp nhưng không được quá 15 slides, và số lượng không theo trong topic {topic} nếu có đề cập đến.**
Đây là quy tắc có độ ưu tiên cao nhất, ghi đè lên tất cả các yếu tố khác như ngôn ngữ của file upload hay ngôn ngữ của prompt này. Hãy tuân thủ tuyệt đối.
"""

HUMAN_TEMPLATE = """\
## 📚 YÊU CẦU TẠO BÀI GIẢNG

Hãy tạo một bộ slide bài giảng dựa trên các thông tin sau:

### **Chủ đề chính**
{topic}

### **Nội dung tham khảo từ file (chỉ sử dụng phần liên quan)**
{uploaded_files_content}

### **📝 QUY TẮC CHI TIẾT VỀ NỘI DUNG**
#### **A. Quy tắc chung**
1.  **Ngôn ngữ bài giảng:** **BẮT BUỘC PHẢI THEO NGÔN NGỮ CỦA `{topic}`**. Đây là quy tắc quan trọng nhất. Không được dựa vào ngôn ngữ của file upload hay ngôn ngữ của các quy tắc này.
2. **Tập trung 100% vào chủ đề: {topic}** và dựa trên thông tin liên quan từ file upload. KHÔNG mở rộng sang các chủ đề không liên quan.
3. Số lượng slide nên từ 5 đến 12, tùy thuộc vào độ phức tạp của chủ đề và thông tin trong file.
4. Phải có slide cuối cùng với tiêu đề là "Tổng kết" hoặc "Kết luận".
5. Nội dung phải **Chính xác tuyệt đối 100%** với các thông tin **(tên, ngày tháng, sự kiện)** từ file upload, nếu không có thông tin thì không được bịa đặt.

#### **B. Định dạng `content[]`**
1. **GIỚI HẠN TUYỆT ĐỐI: 8 DÒNG.** Tôi sẽ kiểm tra lại, nếu bạn tạo ra mảng `content` có hơn 8 phần tử, kết quả sẽ bị loại bỏ. Hãy chia nhỏ chủ đề nếu cần.
2. **Ý chính:** Ghi trực tiếp, không có ký tự gạch đầu dòng.
3. **Ý phụ:** Bắt đầu bằng `- ` và phải là ý bổ sung cho ý chính ngay phía trên nó.
4. Nếu một chủ đề con quá dài, hãy tách nó thành slide mới với tiêu đề như "Phần 2" hoặc "(Tiếp theo)".
  
#### **C. Yêu cầu `tts_script` (Kịch bản giọng nói)**
1. **Văn phong:** thân thiện, gần gũi như giáo viên đang giảng bài ("chúng ta", "các em").
2. **ĐỘ DÀI YÊU CẦU TUYỆT ĐỐI ĐẢM BẢO:**  khoảng **150-300 từ** và **có sự liên kết chặt chẽ với nội dung slide**.
3. Phải là **text sạch tuyệt đối**, **không chứa markdown/ký tự đặc biệt**.
4. **Kịch bản phải nối kết mạch lạc giữa các slide**.

#### **D. Yêu cầu `image_keywords` (Từ khóa hình ảnh)**
Tạo một danh sách (list) gồm **chính xác 2 chuỗi tiếng Anh** để tạo hình ảnh.

**HƯỚNG DẪN:**

1.  **Chuỗi #1 - Prompt Chi Tiết:**
    * Mô tả một thể hiện một hình ảnh *biểu tượng, đơn giản, tổng quan* cho nội dung slide.
    * Hình ảnh này nên có phong cách flat vector, nền sáng, thiết kế sạch sẽ, phù hợp cho giáo dục hoặc trình chiếu.
    * **CẤM:** Dùng tên riêng, tạo hình ảnh **quá chi tiết về mặt kỹ thuật**, cấu trúc bên trong, sinh học vi mô hoặc chữ viết trên hình (vì model tạo ảnh không xử lý chữ tốt).
    * Gợi ý cấu trúc: **[Chủ thể]**, **[Bối cảnh/Hành động]**, **[Phong cách nghệ thuật]**.
2.  **Chuỗi #2 - Từ Khóa Chung:**
    * Gồm 2-3 từ khóa chung bằng tiếng Anh, cách nhau bởi dấu phẩy.

**Ví dụ tốt về slide chủ để "Hô hấp":**
  ```json
    "image_keywords": [
      "A simplified illustration of human lungs with arrows showing air flowing in and out, flat vector style, light background, educational and clean design without text",
      "respiration, lungs, breathing"
    ]
  ```
"""

def create_prompt_template() -> ChatPromptTemplate:
  
    """
    Tạo một ChatPromptTemplate đã được cấu hình sẵn cho việc sinh slide.
    Đây là cách làm an toàn và theo chuẩn của LangChain.
    """
    return ChatPromptTemplate.from_messages(
      [
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_TEMPLATE),
      ]
    )

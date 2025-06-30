# Video Generator Setup Guide

## 1. Cài đặt dependencies

Từ root project directory, chạy:

```bash
pip install -r requirements.txt
```

## 2. Cấu hình Google Cloud Text-to-Speech

**📋 Chi tiết setup**: Xem [Environment Setup Guide](./environment_setup.md)

### Quick Setup:

1. Tạo Google Cloud Project và enable TTS API
2. Tạo Service Account với role "Cloud Text-to-Speech User"
3. Download JSON key file
4. Set environment variable:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\service-account.json"
```

Hoặc tạo file `.env`:

```
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account.json
UNSPLASH_ACCESS_KEY=your_key_optional
```

## 3. Sử dụng API

### � **Lấy danh sách voices có sẵn**

```bash
GET /api/v1/video/voices/vietnamese
```

**Response:**

```json
{
  "success": true,
  "voices": [...],
  "total_count": 6,
  "popular_voices": [
    {"name": "vi-VN-Neural2-A", "gender": "FEMALE", "type": "Neural"},
    {"name": "vi-VN-Neural2-D", "gender": "MALE", "type": "Neural"},
    {"name": "vi-VN-Standard-A", "gender": "FEMALE", "type": "Standard"}
  ]
}
```

### �🎯 **API 1: Tạo video từ topic (với voice options)**

```bash
POST /api/v1/video/generate-from-topic
Content-Type: multipart/form-data

Form data:
- topic: "Giới thiệu về Python" (required)
- subject: "tin_hoc" (optional)
- grade: "10" (optional)
- files: [file1.pdf, file2.docx] (optional)
- voice_name: "vi-VN-Neural2-A" (optional, specific voice)
- speaking_rate: 1.0 (optional: 0.25-4.0, tốc độ nói)
```

**Response:**

```json
{
  "success": true,
  "lesson_data": {
    "lesson_info": {...},
    "slides": [...]
  },
  "video_info": {
    "filename": "lesson_20241224_143022.mp4",
    "message": "Video generated successfully",
    "slide_count": 3,
    "estimated_duration": 5
  }
}
```

### 🎯 **API 2: Tạo video từ slide data có sẵn (với voice config)**

```bash
POST /api/v1/video/generate-from-slides
Content-Type: application/json

{
  "lesson_data": {
    "lesson_info": {"title": "Bài học mẫu", "slide_count": 2},
    "slides": [
      {
        "slide_id": 1,
        "title": "Giới thiệu",
        "content": ["Nội dung slide 1"],
        "tts_script": "Script cho audio...",
        "image_keywords": ["classroom", "education"],
      }
    ]
  },  "voice_config": {
    "language_code": "vi-VN",
    "name": "vi-VN-Neural2-D",
    "gender": "MALE",
    "speaking_rate": 0.9
  }
}
```

### 🎵 **Các loại voice Google Cloud TTS:**

**Neural Voices (Premium - Chất lượng cao hơn):**

- `vi-VN-Neural2-A` - Female (Giọng nữ tự nhiên)
- `vi-VN-Neural2-D` - Male (Giọng nam tự nhiên)

**Standard Voices (Giá chuẩn):**

- `vi-VN-Standard-A` - Female
- `vi-VN-Standard-B` - Male
- `vi-VN-Standard-C` - Female
- `vi-VN-Standard-D` - Male

**Voice Parameters:**

- `speaking_rate`: 0.25-4.0 (tốc độ nói, 1.0 = bình thường)
- `gender`: MALE, FEMALE, NEUTRAL
- `name`: Specific voice name (vd: vi-VN-Neural2-A)

**Response:**

```json
{
  "success": true,
  "video_info": {
    "filename": "lesson_20241224_143025.mp4",
    "message": "Video generated successfully from slide data",
    "slide_count": 2,
    "title": "Bài học mẫu"
  }
}
```

## 4. Test APIs

Chạy test script:

```bash
python test_video_generation.py
```

Hoặc test bằng curl:

```bash
# Test lấy danh sách voices
curl "http://localhost:8000/api/v1/video/voices/vietnamese"

# Test API 1: Topic to video với voice options
curl -X POST "http://localhost:8000/api/v1/video/generate-from-topic" \
  -F "topic=Giới thiệu Python" \
  -F "subject=tin_hoc" \
  -F "grade=10" \
  -F "voice_name=vi-VN-Neural2-A" \
  -F "speaking_rate=1.0"

# Test API 2: Slides to video với voice config
curl -X POST "http://localhost:8000/api/v1/video/generate-from-slides" \
  -H "Content-Type: application/json" \
  -d '{
    "lesson_data": {
      "lesson_info": {"title": "Test", "slide_count": 1},
      "slides": [{"slide_id": 1, "title": "Test", "tts_script": "Xin chào"}]
    },
    "voice_config": {
      "language_code": "vi-VN",
      "name": "vi-VN-Neural2-D",
      "gender": "MALE",
      "speaking_rate": 0.9
    }
  }'
```

## 5. Workflow

1. **Option 1**: Topic → Slides → Video (API 1)

   - Input: topic, subject, grade, files
   - Process: RAG tạo slides → Video generation
   - Output: lesson_data + video_info

2. **Option 2**: Slides → Video (API 2)
   - Input: lesson_data (JSON từ slide-creator)
   - Process: Video generation trực tiếp
   - Output: video_info

## 6. Production Notes

- Video được tạo trong temp directory và tự xóa
- Trong production, upload video lên Azure Blob Storage
- Trả về Azure URL thay vì local filename
- Không cần background tasks, xử lý đồng bộ
- Logs chi tiết cho debugging

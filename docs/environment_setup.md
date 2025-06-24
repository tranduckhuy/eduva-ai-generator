# Environment Setup Guide

## 1. Google Cloud Text-to-Speech Setup

### Bước 1: Tạo Google Cloud Project và Service Account

1. **Tạo Google Cloud Project**:
   - Truy cập [Google Cloud Console](https://console.cloud.google.com/)
   - Tạo project mới hoặc chọn project hiện có
   - Ghi nhớ PROJECT_ID

2. **Enable Cloud Text-to-Speech API**:
   - Trong Google Cloud Console, đi tới "APIs & Services" > "Library"
   - Tìm "Cloud Text-to-Speech API" và enable nó

3. **Tạo Service Account**:
   - Đi tới "IAM & Admin" > "Service Accounts"
   - Click "CREATE SERVICE ACCOUNT"
   - Nhập tên service account (vd: `video-generator-sa`)
   - Gán role: "Cloud Text-to-Speech Admin" hoặc "Cloud Text-to-Speech User"
   - Tạo và download JSON key file

### Bước 2: Cấu hình Environment Variables

**Windows (PowerShell):**
```powershell
# Set Google Cloud credentials
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your\service-account-key.json"

# Optional: Unsplash API key for images
$env:UNSPLASH_ACCESS_KEY="your_unsplash_access_key"

# Verify
echo $env:GOOGLE_APPLICATION_CREDENTIALS
```

**Windows (Command Prompt):**
```cmd
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\service-account-key.json
set UNSPLASH_ACCESS_KEY=your_unsplash_access_key
```

**macOS/Linux:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
export UNSPLASH_ACCESS_KEY="your_unsplash_access_key"
```

### Bước 3: Tạo .env file (Recommended)

Tạo file `.env` trong root project:
```env
# Google Cloud TTS (Required)
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\service-account-key.json

# Unsplash API (Optional - for better images)
UNSPLASH_ACCESS_KEY=your_unsplash_access_key

# Optional: Other configs
PYTHONPATH=.
```

**Lưu ý**: Thêm `.env` vào `.gitignore` để không commit credentials!

## 2. Unsplash API Setup (Optional)

1. **Tạo Unsplash Developer Account**:
   - Truy cập [Unsplash Developers](https://unsplash.com/developers)
   - Đăng ký account và tạo application
   - Lấy Access Key

2. **Cấu hình**:
   - Thêm `UNSPLASH_ACCESS_KEY` vào environment variables
   - Nếu không có, hệ thống sẽ tạo placeholder images

## 3. Verify Setup

Chạy script kiểm tra:
```python
import os
from google.cloud import texttospeech

# Check Google Cloud credentials
print("Google Cloud credentials:", os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))

# Test TTS client
try:
    client = texttospeech.TextToSpeechClient()
    voices = client.list_voices()
    print(f"✅ Google Cloud TTS: Found {len(voices.voices)} voices")
except Exception as e:
    print(f"❌ Google Cloud TTS Error: {e}")

# Check Unsplash (optional)
unsplash_key = os.getenv('UNSPLASH_ACCESS_KEY')
if unsplash_key:
    print(f"✅ Unsplash API key configured")
else:
    print("⚠️ Unsplash API key not found (will use placeholder images)")
```

## 4. Troubleshooting

### Google Cloud Authentication Errors:
- **Error**: "Could not automatically determine credentials"
  - **Solution**: Đảm bảo `GOOGLE_APPLICATION_CREDENTIALS` đúng đường dẫn
  - **Check**: File JSON có tồn tại và có quyền read

- **Error**: "Permission denied"
  - **Solution**: Service account cần role "Cloud Text-to-Speech User"
  - **Check**: Verify IAM permissions trong Google Cloud Console

### Import Errors:
- **Error**: "No module named 'google.cloud'"
  - **Solution**: `pip install google-cloud-texttospeech`

### Path Issues (Windows):
- Sử dụng forward slashes: `C:/path/to/file.json`
- Hoặc escape backslashes: `C:\\path\\to\\file.json`
- Hoặc raw string: `r"C:\path\to\file.json"`

## 5. Production Recommendations

1. **Use Cloud Run/App Engine**: Tự động authenticate thông qua service account
2. **Secret Manager**: Store credentials trong Google Secret Manager
3. **Environment-specific configs**: Dev/staging/prod environments riêng
4. **Monitoring**: Enable Cloud Logging để track TTS usage và costs

## 6. Cost Optimization

- **Standard voices**: Giá rẻ hơn Neural voices
- **Caching**: Cache audio files để tránh tạo lại
- **Batch processing**: Xử lý nhiều slides cùng lúc
- **Monitoring**: Track TTS API usage qua Google Cloud Console

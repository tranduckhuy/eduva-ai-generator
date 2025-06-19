"""
Test script cho slide creator agent đã được đơn giản hóa
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__)).replace('test', '')
sys.path.insert(0, project_root)

from src.agents.lesson_creator.flow import run_slide_creator
from src.utils.logger import logger

async def test_slide_creator():
    """Test basic slide creation functionality"""
    print("=== Test Slide Creator Agent ===")
    
    # Check if environment variables are loaded
    google_api_key = os.getenv("GOOGLE_API_KEY")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    
    if not google_api_key:
        print("❌ GOOGLE_API_KEY not found in environment")
        return
    
    if not pinecone_api_key:
        print("❌ PINECONE_API_KEY not found in environment")
        return
        
    print("✅ Environment variables loaded successfully")
    
    # Test với chủ đề đơn giản
    test_topic = "Hàm số bậc nhất lớp 10"
    
    print(f"Đang tạo slide cho chủ đề: {test_topic}")
    
    try:
        result = await run_slide_creator(
            topic=test_topic,
            model_name="gemini-2.0-flash"
        )
        
        if result["success"]:
            slide_data = result["slide_data"]
            selected_docs = result.get("selected_documents", []) or []
            
            print(f"✅ Thành công!")
            print(f"📊 Số slide: {slide_data.get('lesson_info', {}).get('slide_count', 0)}")
            print(f"📚 Tài liệu tham khảo: {len(selected_docs)}")
            
            # In thông tin chi tiết
            if slide_data and "slides" in slide_data:
                print("\n=== Chi tiết slides ===")
                for slide in slide_data["slides"][:2]:  # Chỉ in 2 slide đầu
                    print(f"\nSlide {slide['slide_id']}: {slide['title']}")
                    print(f"Nội dung: {slide['content']}")
                    print(f"TTS: {slide['tts_script'][:100]}...")
                    print(f"Image keywords: {slide['image_keywords']}")
            
        else:
            print(f"❌ Lỗi: {result['error']}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_slide_creator())
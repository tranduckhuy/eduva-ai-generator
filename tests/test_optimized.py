import asyncio
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from src.services.video_generator import VideoGenerator
from src.services.tts_service import estimate_speech_duration

# Load environment
load_dotenv(override=True)

async def test_optimized_performance():
    lesson_data = {
        "slides": [
            {
                "slide_id": 1,
                "title": "Giới thiệu về Machine Learning",
                "content": [
                    "Machine Learning là gì?",
                    "- Ứng dụng trong đời sống",
                    "- Các loại ML: Supervised, Unsupervised, Reinforcement Learning"
                ],
                "tts_script": "Chào mừng các bạn.",
                "image_keywords": ["machine learning", "AI", "artificial intelligence", "technology"]
            }
        ]
    }
    
    try:
        video_generator = VideoGenerator()
        video_generator.slide_processor.image_generator.template_manager.set_user_preference("modern_blue")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(base_dir, "temp_videos")
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f"optimized_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
        
        start_time = time.time()
        result = await video_generator.generate_lesson_video(lesson_data, output_path, base_dir)
        total_time = time.time() - start_time
        
        print(f"✅ Video generated in {total_time:.1f}s: {result}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_optimized_performance())
    print("✅ Test completed!" if success else "❌ Test failed!")

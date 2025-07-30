"""
Performance test using the OPTIMIZED original VideoGenerator
"""
import asyncio
import json
import os
import logging
import psutil
import time
from datetime import datetime
from src.services.video_generator import VideoGenerator  # Using the optimized original
from src.services.tts_service import estimate_speech_duration

logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv
load_dotenv()

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

async def test_optimized_performance():
    """Test with the OPTIMIZED VideoGenerator using realistic data"""
    
    # Real-world lesson data with longer TTS scripts

    lesson_data = {
        "slides": [
            {
                "slide_id": 1,
                # "title": "Giới thiệu về Machine Learning Giới thiệu về Machine Learning Giới thiệu về Machine Learning",
                "title": "Giới thiệu về Machine Learning",
                "content": [
                    "Machine Learning là gì?",
                    "- Ứng dụng trong đời sống",
                    "- Các loại ML: Supervised, Unsupervised, Reinforcement Learning Các loại ML: Supervised, Unsupervised, Reinforcement Learning  Các loại ML: Supervised, Unsupervised, Reinforcement Learning",
                    "Các loại ML: Supervised, Unsupervised, Reinforcement Learning Các loại ML: Supervised, Unsupervised, Reinforcement Learning  Các loại ML: Supervised, Unsupervised, Reinforcement Learning",
                    "Các loại ML: Supervised, Unsupervised, Reinforcement Learning Các loại ML: Supervised, Unsupervised, Reinforcement Learning  Các loại ML: Supervised, Unsupervised, Reinforcement Learning",
                    "Các loại ML: Supervised, Unsupervised, Reinforcement Learning Các loại ML: Supervised, Unsupervised, Reinforcement Learning  Các loại ML: Supervised, Unsupervised, Reinforcement Learning",
                ],
                # "tts_script": "Chào mừng các bạn đến với khóa học Machine Learning căn bản. Machine Learning hay Học máy là một nhánh của trí tuệ nhân tạo cho phép máy tính học và đưa ra quyết định từ dữ liệu mà không cần lập trình cụ thể cho từng tác vụ. Trong cuộc sống hàng ngày, chúng ta thường xuyên tiếp xúc với Machine Learning qua các hệ thống gợi ý trên Netflix, nhận diện khuôn mặt trên Facebook, hay trợ lý ảo như Siri và Google Assistant.",
                "tts_script": "Chào mừng các bạn.",
                "image_keywords": ["machine learning", "AI", "artificial intelligence", "technology"]
            },
            # {
            #     "slide_id": 2,
            #     "title": "Dữ liệu và Tiền xử lý",
            #     "content": [
            #         "Tầm quan trọng của dữ liệu",
            #         "Làm sạch dữ liệu",
            #         "Feature Engineering",
            #         "Train/Validation/Test Split"
            #     ],
            #     # "tts_script": "Dữ liệu là yếu tố quan trọng nhất trong Machine Learning, có câu nói rằng 'garbage in, garbage out' - dữ liệu kém chất lượng sẽ cho ra mô hình kém chất lượng. Quá trình tiền xử lý dữ liệu bao gồm làm sạch dữ liệu bằng cách loại bỏ giá trị thiếu, xử lý outliers, và chuẩn hóa format. Feature Engineering là nghệ thuật tạo ra các đặc trương mới từ dữ liệu thô để cải thiện hiệu suất mô hình.",
            #     "tts_script": "Chào mừng các bạn.",
            #     "image_keywords": ["data processing", "data cleaning", "feature engineering", "dataset"]
            # },
            # {
            #     "slide_id": 3,
            #     "title": "Linear Regression",
            #     "content": [
            #         "Khái niệm cơ bản",
            #         "Cost Function",
            #         "Gradient Descent",
            #         "Ví dụ thực tế"
            #     ],
            #     # "tts_script": "Linear Regression là thuật toán Machine Learning cơ bản nhất, được sử dụng để dự đoán giá trị liên tục dựa trên mối quan hệ tuyến tính giữa input và output. Mô hình này tìm cách vẽ một đường thẳng tốt nhất qua các điểm dữ liệu để minimizing sai số. Cost Function, thường là Mean Squared Error, đo lường độ chính xác của mô hình.",
            #     "tts_script": "Chào mừng các bạn.",
            #     "image_keywords": ["linear regression", "mathematics", "graph", "prediction"]
            # },
            # {
            #     "slide_id": 4,
            #     "title": "Classification và Decision Trees",
            #     "content": [
            #         "Bài toán phân loại",
            #         "Decision Trees hoạt động như thế nào",
            #         "Entropy và Information Gain",
            #         "Overfitting và Pruning"
            #     ],
            #     "tts_script": "Classification là loại bài toán Machine Learning dự đoán nhãn hoặc danh mục cho dữ liệu đầu vào, khác với regression dự đoán giá trị liên tục. Decision Trees là một thuật toán classification trực quan, hoạt động giống như việc đưa ra quyết định trong đời thực bằng cách đặt một chuỗi câu hỏi yes/no.",
            #     "image_keywords": ["decision tree", "classification", "flowchart", "data science"]
            # },
            # {
            #     "slide_id": 5,
            #     "title": "Random Forest và Ensemble Methods",
            #     "content": [
            #         "Wisdom of Crowds",
            #         "Random Forest Algorithm",
            #         "Bagging vs Boosting",
            #         "Feature Importance"
            #     ],
            #     "tts_script": "Ensemble Methods dựa trên nguyên lý 'wisdom of crowds' - nhiều mô hình yếu kết hợp lại có thể tạo ra một mô hình mạnh. Random Forest là một trong những thuật toán ensemble phổ biến nhất, kết hợp nhiều Decision Trees được training trên các subset khác nhau của dữ liệu.",
            #     "image_keywords": ["random forest", "ensemble", "trees", "algorithm"]
            # }
        ]
    }
    
    # Calculate expected metrics
    total_estimated_duration = sum(estimate_speech_duration(slide['tts_script']) for slide in lesson_data['slides'])
    
    video_generator = VideoGenerator()
    video_generator.slide_processor.image_generator.set_template("soft_modern_edu")  # Use the optimized beautiful template


    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "temp_videos")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f"optimized_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
    
    # Detailed timing tracking
    memory_tracking = []
    
    def track_memory():
        memory_tracking.append({
            'time': time.time(),
            'memory_mb': get_memory_usage()
        })
    
    try:
        print("🚀 OPTIMIZED VIDEOGENERATOR PERFORMANCE TEST")
        print("=" * 60)
        print(f"📊 Test Configuration:")
        print(f"   - Slides: {len(lesson_data['slides'])}")
        print(f"   - Estimated total duration: {total_estimated_duration:.1f} seconds ({total_estimated_duration/60:.1f} minutes)")
        print(f"   - Average TTS length: {sum(len(s['tts_script']) for s in lesson_data['slides']) / len(lesson_data['slides']):.0f} characters")
        print(f"   - Max workers: {video_generator.max_workers_optimized}")
        print(f"   - Batch size: {video_generator.batch_size_optimized}")
        print(f"   - Video FPS: {video_generator.video_fps}")
        print(f"   - Image resolution: {video_generator.image_resolution}")
        print(f"   - Output: {output_path}")
        print()
        
        track_memory()
        overall_start = time.time()
        
        print("🎬 Starting OPTIMIZED video generation with BEAUTIFUL TEMPLATES...")
        print(f"   - Available templates: {video_generator.slide_processor.image_generator.get_available_templates().keys()}")
        print(f"   - Starting template: {video_generator.slide_processor.image_generator.template_manager.current_template}")
        print()
        # Use the optimized original VideoGenerator
        result = await video_generator.generate_lesson_video(lesson_data, output_path, base_dir)
        
        total_time = time.time() - overall_start
        track_memory()
        
        # Analyze results
        print("\n✅ OPTIMIZED GENERATION COMPLETED")
        print("=" * 60)
        
        # Timing analysis
        print("⏱️  Timing Analysis:")
        print(f"   - Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"   - Time per slide: {total_time/len(lesson_data['slides']):.1f} seconds")
        print(f"   - Speed ratio: {total_estimated_duration/total_time:.2f}x (audio duration / generation time)")
        
        # Memory analysis
        if memory_tracking:
            memories = [m['memory_mb'] for m in memory_tracking]
            print(f"\n💾 Memory Analysis:")
            print(f"   - Initial: {memories[0]:.1f} MB")
            print(f"   - Peak: {max(memories):.1f} MB")
            print(f"   - Final: {memories[-1]:.1f} MB")
            print(f"   - Memory increase: {max(memories) - memories[0]:.1f} MB")
            print(f"   - Memory per slide: {(max(memories) - memories[0])/len(lesson_data['slides']):.1f} MB")
        
        # File analysis
        if os.path.exists(result):
            file_size_mb = os.path.getsize(result) / (1024 * 1024)
            print(f"\n📁 Output Analysis:")
            print(f"   - File size: {file_size_mb:.1f} MB")
            print(f"   - Compression ratio: {file_size_mb/total_estimated_duration:.2f} MB/second")
            print(f"   - File exists: ✅")
        else:
            print(f"\n❌ Output file not found: {result}")
            return False
        
        # Performance rating
        print(f"\n🎯 Performance Rating:")
        
        # Speed metrics
        slides_per_minute = len(lesson_data['slides']) / (total_time / 60)
        content_speed = total_estimated_duration / total_time
        
        print(f"   - Processing speed: {slides_per_minute:.1f} slides/minute")
        print(f"   - Content generation rate: {content_speed:.2f}x real-time")
        
        # Quality metrics
        if content_speed >= 1.5:
            speed_rating = "🌟 Excellent"
        elif content_speed >= 1.0:
            speed_rating = "✅ Good"
        elif content_speed >= 0.5:
            speed_rating = "⚠️ Acceptable"
        else:
            speed_rating = "❌ Slow"
            
        if memories and (max(memories) - memories[0]) < 300:
            memory_rating = "🌟 Excellent"
        elif memories and (max(memories) - memories[0]) < 500:
            memory_rating = "✅ Good"
        else:
            memory_rating = "⚠️ High memory usage"
        
        print(f"   - Speed: {speed_rating}")
        print(f"   - Memory efficiency: {memory_rating}")
        
        # Performance comparison
        print(f"\n📈 Performance Improvements:")
        print(f"   - Beautiful Templates: 4 different designs cycling automatically")
        print(f"   - Smart Text Wrapping: No more (...) truncation")
        print(f"   - Longer Content Display: 85% of audio time for reading")
        print(f"   - Professional Design: Gradients, shadows, better typography")
        print(f"   - Faster TTS: 1.1x speaking rate vs 1.0x")
        print(f"   - Lower FPS: {video_generator.video_fps} vs 24")
        print(f"   - Faster encoding: ultrafast preset")
        print(f"   - Increased concurrency: {video_generator.max_workers_optimized} vs 2 workers")
        print(f"   - Larger batches: {video_generator.batch_size_optimized} vs 2")
        print(f"   - Optimized images: {video_generator.image_resolution} resolution")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_optimized_performance())
    print("\n" + "="*60)
    print("🎉 OPTIMIZED TEST COMPLETED SUCCESSFULLY!" if success else "💥 OPTIMIZED TEST FAILED!")
    print("="*60)

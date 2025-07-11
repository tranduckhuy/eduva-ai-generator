"""
Realistic performance test for video generation with detailed metrics
Tests with real-world scenario: 10 slides, 2-5 minutes total duration
"""
import asyncio
import json
import os
import logging
import psutil
import time
from datetime import datetime
from src.services.video_generator import VideoGenerator
from src.services.tts_service import estimate_speech_duration

logging.basicConfig(level=logging.INFO)

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

async def test_realistic_performance():
    """Test with realistic lesson data - 10 slides, 2-5 minutes total"""
    
    # Real-world lesson data with longer TTS scripts
    lesson_data = {
        "slides": [
            {
                "slide_id": 1,
                "title": "Giới thiệu về Machine Learning",
                "content": [
                    "Machine Learning là gì?",
                    "Ứng dụng trong đời sống",
                    "Các loại ML: Supervised, Unsupervised, Reinforcement"
                ],
                "tts_script": "Chào mừng các bạn đến với khóa học Machine Learning căn bản. Machine Learning hay Học máy là một nhánh của trí tuệ nhân tạo cho phép máy tính học và đưa ra quyết định từ dữ liệu mà không cần lập trình cụ thể cho từng tác vụ. Trong cuộc sống hàng ngày, chúng ta thường xuyên tiếp xúc với Machine Learning qua các hệ thống gợi ý trên Netflix, nhận diện khuôn mặt trên Facebook, hay trợ lý ảo như Siri và Google Assistant. Machine Learning được chia thành ba loại chính: Supervised Learning học từ dữ liệu có nhãn, Unsupervised Learning tìm kiếm pattern trong dữ liệu không có nhãn, và Reinforcement Learning học thông qua việc tương tác với môi trường và nhận phần thưởng.",
                "image_keywords": ["machine learning", "AI", "artificial intelligence", "technology"]
            },
            {
                "slide_id": 2,
                "title": "Dữ liệu và Tiền xử lý",
                "content": [
                    "Tầm quan trọng của dữ liệu",
                    "Làm sạch dữ liệu",
                    "Feature Engineering",
                    "Train/Validation/Test Split"
                ],
                "tts_script": "Dữ liệu là yếu tố quan trọng nhất trong Machine Learning, có câu nói rằng 'garbage in, garbage out' - dữ liệu kém chất lượng sẽ cho ra mô hình kém chất lượng. Quá trình tiền xử lý dữ liệu bao gồm làm sạch dữ liệu bằng cách loại bỏ giá trị thiếu, xử lý outliers, và chuẩn hóa format. Feature Engineering là nghệ thuật tạo ra các đặc trương mới từ dữ liệu thô để cải thiện hiệu suất mô hình. Cuối cùng, chúng ta cần chia dữ liệu thành ba tập: Training để huấn luyện mô hình, Validation để tinh chỉnh hyperparameters, và Test để đánh giá hiệu suất cuối cùng. Việc chia dữ liệu đúng cách giúp tránh overfitting và đảm bảo mô hình hoạt động tốt với dữ liệu mới.",
                "image_keywords": ["data processing", "data cleaning", "feature engineering", "dataset"]
            },
            {
                "slide_id": 3,
                "title": "Linear Regression",
                "content": [
                    "Khái niệm cơ bản",
                    "Cost Function",
                    "Gradient Descent",
                    "Ví dụ thực tế"
                ],
                "tts_script": "Linear Regression là thuật toán Machine Learning cơ bản nhất, được sử dụng để dự đoán giá trị liên tục dựa trên mối quan hệ tuyến tính giữa input và output. Mô hình này tìm cách vẽ một đường thẳng tốt nhất qua các điểm dữ liệu để minimizing sai số. Cost Function, thường là Mean Squared Error, đo lường độ chính xác của mô hình bằng cách tính toán sai khác giữa giá trị thực và giá trị dự đoán. Gradient Descent là thuật toán optimization được sử dụng để tìm ra các tham số tối ưu cho mô hình bằng cách di chuyển theo hướng giảm cost function. Một ví dụ thực tế của Linear Regression là dự đoán giá nhà dựa trên diện tích, số phòng ngủ, và vị trí. Đây là nền tảng để hiểu các thuật toán phức tạp hơn.",
                "image_keywords": ["linear regression", "mathematics", "graph", "prediction"]
            },
            {
                "slide_id": 4,
                "title": "Classification và Decision Trees",
                "content": [
                    "Bài toán phân loại",
                    "Decision Trees hoạt động như thế nào",
                    "Entropy và Information Gain",
                    "Overfitting và Pruning"
                ],
                "tts_script": "Classification là loại bài toán Machine Learning dự đoán nhãn hoặc danh mục cho dữ liệu đầu vào, khác với regression dự đoán giá trị liên tục. Decision Trees là một thuật toán classification trực quan, hoạt động giống như việc đưa ra quyết định trong đời thực bằng cách đặt một chuỗi câu hỏi yes/no. Entropy đo lường độ hỗn loạn trong dữ liệu, còn Information Gain cho biết một feature có khả năng phân chia dữ liệu tốt như thế nào. Decision Trees dễ bị overfitting khi cây quá sâu và phức tạp, dẫn đến hiệu suất kém trên dữ liệu mới. Pruning là kỹ thuật cắt bỏ các nhánh không cần thiết để tạo ra mô hình đơn giản và tổng quát hóa tốt hơn. Ví dụ thực tế là phân loại email spam dựa trên từ khóa và người gửi.",
                "image_keywords": ["decision tree", "classification", "flowchart", "data science"]
            },
            {
                "slide_id": 5,
                "title": "Random Forest và Ensemble Methods",
                "content": [
                    "Wisdom of Crowds",
                    "Random Forest Algorithm",
                    "Bagging vs Boosting",
                    "Feature Importance"
                ],
                "tts_script": "Ensemble Methods dựa trên nguyên lý 'wisdom of crowds' - nhiều mô hình yếu kết hợp lại có thể tạo ra một mô hình mạnh. Random Forest là một trong những thuật toán ensemble phổ biến nhất, kết hợp nhiều Decision Trees được training trên các subset khác nhau của dữ liệu. Bagging như Random Forest training các mô hình song song và lấy trung bình kết quả, trong khi Boosting như AdaBoost training tuần tự và tập trung vào các mẫu khó phân loại. Random Forest cung cấp Feature Importance, cho biết feature nào quan trọng nhất trong việc đưa ra dự đoán. Ưu điểm của Random Forest là robust với noise, ít bị overfitting, và hoạt động tốt mà không cần tuning hyperparameters nhiều. Thuật toán này thường được sử dụng làm baseline trong các competition Machine Learning.",
                "image_keywords": ["random forest", "ensemble", "trees", "algorithm"]
            },
            {
                "slide_id": 6,
                "title": "Support Vector Machines (SVM)",
                "content": [
                    "Tìm đường phân chia tối ưu",
                    "Support Vectors",
                    "Kernel Trick",
                    "SVM cho Classification và Regression"
                ],
                "tts_script": "Support Vector Machine là thuật toán mạnh mẽ tìm cách phân chia dữ liệu bằng một đường thẳng hoặc siêu phẳng sao cho khoảng cách đến các điểm gần nhất là lớn nhất. Những điểm dữ liệu gần đường phân chia nhất được gọi là Support Vectors, chúng quyết định vị trí của đường phân chia. Kernel Trick cho phép SVM xử lý dữ liệu không tuyến tính bằng cách mapping dữ liệu lên không gian có chiều cao hơn mà không cần tính toán explicit. Các kernel phổ biến include linear, polynomial, và RBF (Radial Basis Function). SVM có thể được sử dụng cho cả classification và regression (SVR), với ưu điểm là hoạt động tốt với dữ liệu có nhiều features và ít samples. Tuy nhiên, SVM có thể chậm với dataset lớn và khó interpret kết quả.",
                "image_keywords": ["SVM", "support vector machine", "classification", "margin"]
            },
            {
                "slide_id": 7,
                "title": "Neural Networks Cơ bản",
                "content": [
                    "Từ Perceptron đến Multi-layer",
                    "Activation Functions",
                    "Backpropagation",
                    "Deep Learning Introduction"
                ],
                "tts_script": "Neural Networks lấy cảm hứng từ cách hoạt động của não bộ, bắt đầu từ Perceptron đơn giản đến Multi-layer Perceptron phức tạp. Mỗi neuron nhận inputs, nhân với weights, cộng bias, và đi qua activation function để tạo output. Activation functions như sigmoid, tanh, và ReLU quyết định output của neuron có được activate hay không. Backpropagation là thuật toán training neural networks bằng cách tính gradient và update weights theo hướng giảm loss function từ output layer về input layer. Deep Learning là phần mở rộng của neural networks với nhiều hidden layers, cho phép học các pattern phức tạp trong dữ liệu như hình ảnh, text, và audio. Neural networks đặc biệt mạnh trong việc học non-linear relationships và có thể approximate bất kỳ function nào với đủ neurons. Đây là nền tảng cho các breakthrough recent trong AI.",
                "image_keywords": ["neural network", "deep learning", "neurons", "AI brain"]
            },
            {
                "slide_id": 8,
                "title": "Clustering và K-Means",
                "content": [
                    "Unsupervised Learning",
                    "K-Means Algorithm",
                    "Choosing K value",
                    "Hierarchical Clustering"
                ],
                "tts_script": "Clustering là loại Unsupervised Learning tìm cách nhóm dữ liệu thành các clusters dựa trên độ tương đồng mà không cần labels. K-Means là thuật toán clustering phổ biến nhất, hoạt động bằng cách khởi tạo K centroids ngẫu nhiên, assign each data point to nearest centroid, sau đó update centroids là trung bình của cluster. Process này lặp lại until convergence. Việc chọn K value đúng rất quan trọng, có thể sử dụng Elbow Method hoặc Silhouette Analysis để tìm K optimal. Hierarchical Clustering tạo ra cây phân cấp các clusters, có thể là agglomerative (bottom-up) hoặc divisive (top-down). Clustering applications include customer segmentation, image segmentation, market research, và data compression. Ưu điểm của clustering là không cần labeled data và có thể reveal hidden patterns trong dữ liệu.",
                "image_keywords": ["clustering", "k-means", "data groups", "unsupervised"]
            },
            {
                "slide_id": 9,
                "title": "Model Evaluation và Metrics",
                "content": [
                    "Accuracy, Precision, Recall",
                    "F1-Score và Confusion Matrix",
                    "ROC Curve và AUC",
                    "Cross-Validation"
                ],
                "tts_script": "Model evaluation là bước quan trọng để đánh giá hiệu suất mô hình Machine Learning. Accuracy đo tỷ lệ dự đoán đúng tổng thể, nhưng có thể misleading với imbalanced dataset. Precision đo tỷ lệ positive predictions thực sự đúng, còn Recall đo tỷ lệ actual positives được detect correctly. F1-Score là harmonic mean của Precision và Recall, cân bằng giữa hai metrics này. Confusion Matrix visualization các loại prediction errors, giúp understand model behavior better. ROC Curve plot True Positive Rate vs False Positive Rate, và AUC (Area Under Curve) summarize performance trong một số duy nhất. Cross-Validation chia dữ liệu thành k folds và training k times để có estimation robust của model performance. Việc chọn đúng evaluation metrics depends on business objectives và nature của problem được giải quyết.",
                "image_keywords": ["evaluation", "metrics", "accuracy", "model performance"]
            },
            {
                "slide_id": 10,
                "title": "Deployment và Production",
                "content": [
                    "Model Serialization",
                    "API Creation",
                    "Monitoring và Maintenance",
                    "MLOps Basics"
                ],
                "tts_script": "Deployment là bước cuối cùng đưa mô hình Machine Learning từ development environment lên production để users có thể sử dụng. Model Serialization sử dụng tools như pickle, joblib, hoặc ONNX để save trained models thành files có thể load lại. API Creation thường sử dụng frameworks như Flask, FastAPI, hoặc Django REST để tạo endpoints cho model inference. Monitoring production models rất quan trọng để detect model drift khi data distribution thay đổi theo thời gian, cần track metrics như accuracy, latency, và resource usage. MLOps là practice kết hợp Machine Learning với DevOps, automation model training, testing, deployment, và monitoring. Version control cho models, automated testing, CI/CD pipelines, và infrastructure as code là essential components của MLOps. Successful deployment requires collaboration giữa data scientists, software engineers, và DevOps teams để ensure models are reliable, scalable, và maintainable in production environment.",
                "image_keywords": ["deployment", "production", "API", "MLOps", "server"]
            }
        ]
    }
    
    # Calculate expected metrics
    total_estimated_duration = sum(estimate_speech_duration(slide['tts_script']) for slide in lesson_data['slides'])
    
    video_generator = VideoGenerator()
    output_path = f"realistic_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    
    # Detailed timing tracking
    phase_times = {}
    memory_tracking = []
    
    def track_memory():
        memory_tracking.append({
            'time': time.time(),
            'memory_mb': get_memory_usage()
        })
    
    try:
        print("🚀 REALISTIC PERFORMANCE TEST")
        print("=" * 50)
        print(f"📊 Test Configuration:")
        print(f"   - Slides: {len(lesson_data['slides'])}")
        print(f"   - Estimated total duration: {total_estimated_duration:.1f} seconds ({total_estimated_duration/60:.1f} minutes)")
        print(f"   - Average TTS length: {sum(len(s['tts_script']) for s in lesson_data['slides']) / len(lesson_data['slides']):.0f} characters")
        print(f"   - Output: {output_path}")
        print()
        
        track_memory()
        overall_start = time.time()
        
        print("🎬 Starting video generation...")
        
        # Phase 1: Initialization
        phase_start = time.time()
        # Video generator is already initialized
        phase_times['initialization'] = time.time() - phase_start
        track_memory()
        
        # Phase 2: Main generation
        phase_start = time.time()
        result = await video_generator.generate_lesson_video(lesson_data, output_path)
        phase_times['video_generation'] = time.time() - phase_start
        track_memory()
        
        total_time = time.time() - overall_start
        
        # Analyze results
        print("\n✅ GENERATION COMPLETED")
        print("=" * 50)
        
        # Timing analysis
        print("⏱️  Timing Analysis:")
        print(f"   - Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"   - Time per slide: {total_time/len(lesson_data['slides']):.1f} seconds")
        print(f"   - Speed ratio: {total_estimated_duration/total_time:.2f}x (audio duration / generation time)")
        
        for phase, duration in phase_times.items():
            print(f"   - {phase.title()}: {duration:.1f}s ({duration/total_time*100:.1f}%)")
        
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
        content_speed = total_estimated_duration / total_time  # How many seconds of content per second of processing
        
        print(f"   - Processing speed: {slides_per_minute:.1f} slides/minute")
        print(f"   - Content generation rate: {content_speed:.2f}x real-time")
        
        # Quality metrics
        if content_speed >= 1.5:  # Faster than 1.5x real-time
            speed_rating = "🌟 Excellent"
        elif content_speed >= 1.0:
            speed_rating = "✅ Good"
        elif content_speed >= 0.5:
            speed_rating = "⚠️ Acceptable"
        else:
            speed_rating = "❌ Slow"
            
        if memories and (max(memories) - memories[0]) < 500:  # Less than 500MB increase
            memory_rating = "🌟 Excellent"
        elif memories and (max(memories) - memories[0]) < 1000:
            memory_rating = "✅ Good"
        else:
            memory_rating = "⚠️ High memory usage"
        
        print(f"   - Speed: {speed_rating}")
        print(f"   - Memory efficiency: {memory_rating}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if content_speed < 1.0:
            print("   - Consider optimizing image processing")
            print("   - Check TTS service response time")
            print("   - Reduce concurrent processing if memory constrained")
        
        if memories and (max(memories) - memories[0]) > 800:
            print("   - Consider processing slides in smaller batches")
            print("   - Optimize image resolution/size")
            print("   - Add more aggressive garbage collection")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_realistic_performance())
    print("\n" + "="*50)
    print("🎉 TEST COMPLETED SUCCESSFULLY!" if success else "💥 TEST FAILED!")
    print("="*50)

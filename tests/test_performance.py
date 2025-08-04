"""
Performance test for optimized video generation
"""
import asyncio
import json
import os
import psutil
import time
from datetime import datetime
from src.services.video_generator import VideoGenerator
from src.utils.logger import logger

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

async def test_performance():
    """Test with multiple slides to measure performance and memory"""
    
    lesson_data = {
        "slides": [
            {
                "slide_id": 1,
                "title": "Giới thiệu Python",
                "content": ["Python là ngôn ngữ lập trình cấp cao", "Phù hợp cho người mới bắt đầu", "Được sử dụng rộng rãi trong AI và khoa học dữ liệu"],
                "tts_script": "Chào mừng các bạn đến với khóa học Python cơ bản. Python là một ngôn ngữ lập trình cấp cao, dễ học và có cú pháp đơn giản. Python được sử dụng rộng rãi trong nhiều lĩnh vực như phát triển web, khoa học dữ liệu, trí tuệ nhân tạo và tự động hóa. Trong bài học hôm nay, chúng ta sẽ tìm hiểu những khái niệm cơ bản nhất của Python để bạn có thể bắt đầu hành trình lập trình của mình một cách hiệu quả nhất.",
                "image_keywords": ["python", "programming", "coding", "beginner"]
            },
            {
                "slide_id": 2,
                "title": "Cài đặt và Môi trường",
                "content": ["Tải Python từ python.org", "Cài đặt IDE như PyCharm hoặc VS Code", "Kiểm tra cài đặt với python --version"],
                "tts_script": "Trước khi bắt đầu lập trình Python, chúng ta cần cài đặt Python trên máy tính. Các bạn có thể tải Python miễn phí từ trang web chính thức python.org. Tôi khuyên bạn nên chọn phiên bản Python mới nhất để có được các tính năng và cải tiến mới nhất. Sau khi cài đặt Python, bạn nên chọn một môi trường phát triển tích hợp như PyCharm, VS Code hoặc Jupyter Notebook để viết code hiệu quả hơn. Cuối cùng, hãy mở terminal và gõ python --version để kiểm tra xem Python đã được cài đặt thành công chưa.",
                "image_keywords": ["python install", "IDE", "setup", "environment"]
            },
            {
                "slide_id": 3,
                "title": "Biến và Kiểu Dữ liệu",
                "content": ["Số nguyên (int)", "Số thực (float)", "Chuỗi (string)", "Boolean (True/False)", "Danh sách (list)", "Từ điển (dictionary)"],
                "tts_script": "Python hỗ trợ nhiều kiểu dữ liệu khác nhau. Kiểu số nguyên hay int được sử dụng để lưu trữ các số không có phần thập phân như 1, 2, 100. Kiểu số thực hay float dùng cho các số có phần thập phân như 3.14, 2.5. Kiểu chuỗi hay string dùng để lưu trữ văn bản, được đặt trong dấu nháy đơn hoặc nháy kép. Kiểu boolean chỉ có hai giá trị True hoặc False. Danh sách list cho phép lưu trữ nhiều giá trị trong một biến. Từ điển dictionary lưu trữ dữ liệu dưới dạng cặp key-value. Việc hiểu rõ các kiểu dữ liệu này là nền tảng quan trọng cho việc lập trình Python.",
                "image_keywords": ["data types", "variables", "int", "float", "string", "list", "dictionary"]
            },
            {
                "slide_id": 4,
                "title": "Toán tử và Biểu thức",
                "content": ["Toán tử số học: +, -, *, /, //, %, **", "Toán tử so sánh: ==, !=, <, >, <=, >=", "Toán tử logic: and, or, not"],
                "tts_script": "Python cung cấp nhiều loại toán tử để thực hiện các phép tính và so sánh. Toán tử số học bao gồm cộng trừ nhân chia cơ bản, ngoài ra còn có phép chia lấy phần nguyên với hai dấu gạch chéo, phép chia lấy dư với dấu phần trăm, và phép lũy thừa với hai dấu sao. Toán tử so sánh giúp chúng ta so sánh hai giá trị với nhau, trả về True hoặc False. Toán tử logic and, or, not được sử dụng để kết hợp các điều kiện boolean. Việc nắm vững các toán tử này sẽ giúp bạn viết được những biểu thức phức tạp và điều kiện logic chính xác trong chương trình.",
                "image_keywords": ["operators", "arithmetic", "comparison", "logic", "expressions"]
            },
            {
                "slide_id": 5,
                "title": "Cấu trúc Điều kiện",
                "content": ["Câu lệnh if", "Câu lệnh elif", "Câu lệnh else", "Điều kiện lồng nhau"],
                "tts_script": "Cấu trúc điều kiện là một trong những khái niệm quan trọng nhất trong lập trình Python. Câu lệnh if cho phép chương trình thực hiện một đoạn code chỉ khi điều kiện được thoả mãn. Câu lệnh elif là viết tắt của else if, cho phép kiểm tra nhiều điều kiện khác nhau. Câu lệnh else sẽ được thực hiện khi tất cả các điều kiện trước đó đều không đúng. Chúng ta cũng có thể tạo điều kiện lồng nhau bằng cách đặt một câu lệnh if bên trong một câu lệnh if khác. Điều quan trọng là phải chú ý đến việc thụt lề trong Python vì nó quyết định phạm vi của từng khối lệnh.",
                "image_keywords": ["if statement", "conditional", "elif", "else", "decision making"]
            },
            {
                "slide_id": 6,
                "title": "Vòng lặp For",
                "content": ["Lặp qua danh sách", "Hàm range()", "Lặp qua chuỗi", "Vòng lặp lồng nhau"],
                "tts_script": "Vòng lặp for trong Python được sử dụng để lặp qua các phần tử của một chuỗi như danh sách, tuple, hoặc chuỗi ký tự. Hàm range() rất hữu ích khi bạn muốn lặp một số lần nhất định hoặc tạo ra một dãy số. Ví dụ range(5) sẽ tạo ra các số từ 0 đến 4. Bạn cũng có thể lặp qua từng ký tự trong một chuỗi văn bản. Vòng lặp lồng nhau nghĩa là đặt một vòng lặp bên trong vòng lặp khác, điều này rất hữu ích khi làm việc với dữ liệu hai chiều như ma trận. Vòng lặp for giúp tự động hóa các tác vụ lặp đi lặp lại và làm cho code ngắn gọn hơn.",
                "image_keywords": ["for loop", "iteration", "range", "list", "nested loops"]
            },
            {
                "slide_id": 7,
                "title": "Vòng lặp While",
                "content": ["Cú pháp while", "Điều kiện dừng", "Tránh vòng lặp vô hạn", "Break và continue"],
                "tts_script": "Vòng lặp while tiếp tục thực hiện một khối lệnh miễn là điều kiện còn đúng. Khác với vòng lặp for đã biết trước số lần lặp, while phù hợp khi chúng ta không biết chính xác cần lặp bao nhiều lần. Điều quan trọng nhất khi sử dụng while là phải đảm bảo điều kiện sẽ trở thành False tại một thời điểm nào đó, nếu không vòng lặp sẽ chạy mãi mãi. Từ khóa break cho phép thoát khỏi vòng lặp ngay lập tức, còn continue sẽ bỏ qua phần còn lại của lần lặp hiện tại và chuyển đến lần lặp tiếp theo. Việc sử dụng đúng vòng lặp while sẽ giúp chương trình của bạn linh hoạt và hiệu quả hơn.",
                "image_keywords": ["while loop", "condition", "break", "continue", "infinite loop"]
            },
            {
                "slide_id": 8,
                "title": "Hàm trong Python",
                "content": ["Định nghĩa hàm với def", "Tham số và đối số", "Giá trị trả về", "Hàm lambda", "Phạm vi biến"],
                "tts_script": "Hàm là một khối code có thể tái sử dụng để thực hiện một tác vụ cụ thể. Trong Python, chúng ta định nghĩa hàm bằng từ khóa def, theo sau là tên hàm và các tham số trong dấu ngoặc đơn. Tham số là các biến mà hàm nhận vào, còn đối số là giá trị thực tế được truyền khi gọi hàm. Hàm có thể trả về giá trị bằng từ khóa return. Hàm lambda là cách viết hàm ngắn gọn trên một dòng, thường dùng cho các tác vụ đơn giản. Phạm vi biến quyết định biến nào có thể được truy cập từ đâu trong chương trình. Việc sử dụng hàm giúp code dễ đọc, dễ bảo trì và tránh lặp lại code.",
                "image_keywords": ["function", "def", "parameters", "return", "lambda", "scope"]
            },
            {
                "slide_id": 9,
                "title": "Xử lý Ngoại lệ",
                "content": ["Khối try-except", "Các loại exception", "Finally block", "Raise exception"],
                "tts_script": "Xử lý ngoại lệ là kỹ thuật quan trọng giúp chương trình không bị crash khi gặp lỗi. Khối try-except cho phép chúng ta 'thử' thực hiện một đoạn code và 'bắt' các lỗi có thể xảy ra. Python có nhiều loại exception khác nhau như ValueError khi giá trị không hợp lệ, TypeError khi kiểu dữ liệu sai, FileNotFoundError khi không tìm thấy file. Khối finally sẽ luôn được thực hiện dù có lỗi hay không, thường dùng để dọn dẹp tài nguyên. Chúng ta cũng có thể chủ động tạo ra exception bằng từ khóa raise. Xử lý ngoại lệ đúng cách giúp chương trình robust và user-friendly hơn.",
                "image_keywords": ["exception", "try except", "error handling", "finally", "raise"]
            },
            {
                "slide_id": 10,
                "title": "Module và Package",
                "content": ["Import module", "Tạo module riêng", "Package và __init__.py", "Thư viện chuẩn Python"],
                "tts_script": "Module và package giúp tổ chức code Python một cách có hệ thống. Module là một file Python chứa các hàm, class và biến mà bạn có thể sử dụng trong chương trình khác bằng cách import. Bạn có thể tạo module riêng bằng cách lưu code vào file .py và import nó. Package là thư mục chứa nhiều module, với file __init__.py để Python hiểu đây là một package. Python có rất nhiều thư viện chuẩn như math cho các phép toán, datetime để làm việc với thời gian, os để tương tác với hệ điều hành. Việc sử dụng module và package giúp code modular, dễ bảo trì và có thể tái sử dụng. Đây là nền tảng để phát triển các ứng dụng Python lớn và phức tạp.",
                "image_keywords": ["module", "package", "import", "library", "organization"]
            }
        ]
    }
    
    video_generator = VideoGenerator()
    output_path = f"performance_test_{datetime.now().strftime('%H%M%S')}.mp4"
    
    # Memory monitoring
    initial_memory = get_memory_usage()
    peak_memory = initial_memory
    
    try:
        print(f"🚀 Starting performance test with {len(lesson_data['slides'])} slides...")
        print(f"💾 Initial memory: {initial_memory:.1f} MB")
        
        start_time = time.time()
        
        # Monitor memory during processing
        async def memory_monitor():
            nonlocal peak_memory
            while True:
                current_memory = get_memory_usage()
                if current_memory > peak_memory:
                    peak_memory = current_memory
                await asyncio.sleep(1)
        
        # Start memory monitoring
        monitor_task = asyncio.create_task(memory_monitor())
        
        # Generate video
        result = await video_generator.generate_lesson_video(lesson_data, output_path)
        
        # Stop monitoring
        monitor_task.cancel()
        
        end_time = time.time()
        final_memory = get_memory_usage()
        duration = end_time - start_time
        
        # Performance metrics
        print(f"✅ Success: {result}")
        print(f"⏱️  Total time: {duration:.1f} seconds")
        print(f"📊 Time per slide: {duration/len(lesson_data['slides']):.1f} seconds")
        print(f"💾 Memory usage:")
        print(f"   - Initial: {initial_memory:.1f} MB")
        print(f"   - Peak: {peak_memory:.1f} MB")
        print(f"   - Final: {final_memory:.1f} MB")
        print(f"   - Max increase: {peak_memory - initial_memory:.1f} MB")
        
        # Check file size
        if os.path.exists(result):
            file_size = os.path.getsize(result) / (1024 * 1024)  # MB
            print(f"📁 Video file size: {file_size:.1f} MB")
        
        # Performance rating
        slides_per_minute = len(lesson_data['slides']) / (duration / 60)
        memory_efficiency = (peak_memory - initial_memory) / len(lesson_data['slides'])
        
        print(f"🎯 Performance:")
        print(f"   - Speed: {slides_per_minute:.1f} slides/minute")
        print(f"   - Memory per slide: {memory_efficiency:.1f} MB")
        
        if slides_per_minute > 10 and memory_efficiency < 50:
            print("🌟 Excellent performance!")
        elif slides_per_minute > 5 and memory_efficiency < 100:
            print("✅ Good performance!")
        else:
            print("⚠️  Performance could be improved")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Final cleanup check
        final_memory = get_memory_usage()
        print(f"🧹 Final memory after cleanup: {final_memory:.1f} MB")

if __name__ == "__main__":
    success = asyncio.run(test_performance())
    print("🎉 Performance test completed!" if success else "💥 Performance test failed!")

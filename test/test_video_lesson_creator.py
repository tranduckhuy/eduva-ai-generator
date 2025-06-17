import asyncio
import json
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from src.agents.lesson_creator.flow import lesson_creator_agent
from src.utils.logger import logger

load_dotenv()


async def test_video_lesson_creator():
    """
    Test hệ thống tạo video bài giảng với các yêu cầu mẫu
    """
    test_cases = [
        {
            "name": "Tạo bài giảng Toán",
            "query": "Tạo bài giảng Toán lớp 10 về hàm số bậc nhất, bao gồm slide và script thuyết minh"
        },
        {
            "name": "Tạo bài giảng Vật lý", 
            "query": "Cần slide Vật lý lớp 11 về dao động điều hòa, có ví dụ và bài tập"
        }
    ]
    
    config = {"configurable": {"thread_id": "lesson_test_1"}}
    
    for i, test_case in enumerate(test_cases):
        print(f"\n{'='*60}")
        print(f"TEST {i+1}: {test_case['name']}")
        print(f"{'='*60}")
        print(f"Yêu cầu: {test_case['query']}")
        print("\nĐang xử lý...")
        
        try:
            input_dict = {
                "messages": [HumanMessage(content=test_case['query'])]
            }
            
            response = await lesson_creator_agent.ainvoke(input_dict, config)
            
            print("\nKết quả:")
            print("-" * 40)
            print(response["messages"][-1].content)
            print("-" * 40)
            
        except Exception as e:
            print(f"Lỗi: {str(e)}")
        
        print("\n" + "="*60)


async def interactive_test():
    """
    Test tương tác với hệ thống
    """
    print("🎓 HỆ THỐNG TẠO VIDEO BÀI GIẢNG CHO HỌC SINH CẤP 3")
    print("=" * 60)
    print("Nhập yêu cầu của bạn (hoặc 'quit' để thoát)")
    print("Ví dụ: 'Tạo bài giảng Toán lớp 10 về hàm số bậc nhất'")
    print("-" * 60)
    
    config = {"configurable": {"thread_id": "interactive_lesson"}}
    
    while True:
        user_input = input("\n👨‍🏫 Giáo viên: ")
        
        if user_input.lower() in ['quit', 'exit', 'thoát']:
            print("Cảm ơn bạn đã sử dụng hệ thống!")
            break
            
        if not user_input.strip():
            continue
            
        try:
            input_dict = {
                "messages": [HumanMessage(content=user_input)]
            }
            
            print("\n🤖 Đang xử lý yêu cầu...")
            response = await lesson_creator_agent.ainvoke(input_dict, config)
            
            print("\n🎯 Trợ lý AI:")
            print("-" * 40)
            print(response["messages"][-1].content)
            print("-" * 40)
            
        except Exception as e:
            print(f"❌ Lỗi: {str(e)}")


async def test_rag_document_retrieval():
    """Test RAG system với truy xuất tài liệu từ vector store"""
    print("=== Testing RAG Document Retrieval ===")
    
    # Test case 1: Truy xuất tài liệu Toán học
    test_queries = [
        {
            "query": "Tạo bài giảng Toán lớp 10 về hàm số bậc nhất, 20 phút",
            "expected_subject": "Toán",
            "expected_grade": "lớp 10"
        },
        {
            "query": "Cần slide Vật lý lớp 11 về dao động điều hòa với ví dụ",
            "expected_subject": "Vật lý", 
            "expected_grade": "lớp 11"
        },
        {
            "query": "Hỗ trợ tạo video Hóa học lớp 12 về phản ứng axit-bazơ",
            "expected_subject": "Hóa học",
            "expected_grade": "lớp 12"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n--- Test Case {i}: {test_case['query']} ---")
        
        try:
            # Gọi RAG agent
            config = {"configurable": {"thread_id": f"test_{i}"}}
            input_graph = {"messages": [{"role": "user", "content": test_case["query"]}]}
            
            response = await lesson_creator_agent.ainvoke(input_graph, config)
            
            # Kiểm tra response structure
            assert "messages" in response, "Response thiếu messages"
            assert len(response["messages"]) > 0, "Messages rỗng"
            
            final_message = response["messages"][-1].content
            print(f"✓ Nhận được response: {len(final_message)} characters")
            
            # Kiểm tra slide_data
            slide_data = response.get("slide_data", {})
            if slide_data:
                print(f"✓ Slide data generated: {len(slide_data.get('slides', []))} slides")
                
                # Validate lesson_info
                lesson_info = slide_data.get("lesson_info", {})
                if lesson_info:
                    print(f"  - Subject: {lesson_info.get('subject', 'N/A')}")
                    print(f"  - Grade: {lesson_info.get('grade', 'N/A')}")
                    print(f"  - Duration: {lesson_info.get('duration_minutes', 'N/A')} minutes")
            else:
                print("⚠ No structured slide data generated")
            
            # Kiểm tra document retrieval
            selected_docs = response.get("selected_documents", [])
            selected_ids = response.get("selected_ids", [])
            
            if selected_docs:
                print(f"✓ Retrieved {len(selected_docs)} documents from vector store")
                print(f"  - Document IDs: {selected_ids[:3]}...")  # Show first 3 IDs
            else:
                print("⚠ No documents retrieved from vector store")
            
            print(f"✓ Test Case {i} PASSED\n")
            
        except Exception as e:
            print(f"✗ Test Case {i} FAILED: {str(e)}")
            logger.error(f"Test case {i} error: {str(e)}")


async def test_vector_store_connection():
    """Test kết nối vector store"""
    print("=== Testing Vector Store Connection ===")
    
    try:
        from src.agents.lesson_creator.tools import retrieve_document
        
        # Test truy xuất tài liệu trực tiếp
        test_query = "hàm số bậc nhất toán lớp 10"
        result = retrieve_document.invoke({"query": test_query})
        
        print(f"✓ Vector store connection successful")
        print(f"  - Retrieved context length: {len(result.get('context_str', ''))}")
        print(f"  - Number of documents: {len(result.get('selected_documents', []))}")
        print(f"  - Document IDs: {result.get('selected_ids', [])}")
        
        return True
        
    except Exception as e:
        print(f"✗ Vector store connection failed: {str(e)}")
        return False


async def test_structured_output():
    """Test cấu trúc JSON output"""
    print("=== Testing Structured JSON Output ===")
    
    try:
        from src.agents.lesson_creator.tools import create_structured_lesson_content
        
        # Test tạo structured content
        result = create_structured_lesson_content.invoke({
            "topic": "Hàm số bậc nhất",
            "grade_level": "lớp 10", 
            "subject": "Toán",
            "duration_minutes": 25
        })
        
        # Validate JSON structure
        assert "lesson_info" in result, "Missing lesson_info"
        assert "slides" in result, "Missing slides array"
        
        lesson_info = result["lesson_info"]
        assert "title" in lesson_info, "Missing title"
        assert "subject" in lesson_info, "Missing subject"
        assert "grade" in lesson_info, "Missing grade"
        
        slides = result["slides"]
        assert len(slides) > 0, "Empty slides array"
        
        # Validate first slide structure
        first_slide = slides[0]
        required_fields = ["slide_id", "type", "title", "content", "duration_seconds", "tts_script", "visual_elements"]
        for field in required_fields:
            assert field in first_slide, f"Missing field: {field}"
        
        print(f"✓ Structured JSON output validated")
        print(f"  - Lesson: {lesson_info['title']}")
        print(f"  - Subject: {lesson_info['subject']}")
        print(f"  - Grade: {lesson_info['grade']}")
        print(f"  - Slides count: {len(slides)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Structured output test failed: {str(e)}")
        return False


async def main():
    """Chạy tất cả test cases"""
    print("🧪 RAG SYSTEM VALIDATION TEST")
    print("=" * 50)
    
    # Test 1: Vector store connection
    vector_store_ok = await test_vector_store_connection()
    
    # Test 2: Structured output
    structured_output_ok = await test_structured_output()
    
    # Test 3: End-to-end RAG workflow (chỉ chạy nếu vector store OK)
    if vector_store_ok:
        await test_rag_document_retrieval()
    else:
        print("⚠ Skipping RAG workflow test due to vector store connection issues")
    
    print("\n" + "=" * 50)
    print("🏁 TEST SUMMARY:")
    print(f"Vector Store Connection: {'✓ PASS' if vector_store_ok else '✗ FAIL'}")
    print(f"Structured Output: {'✓ PASS' if structured_output_ok else '✗ FAIL'}")
    print(f"Overall Status: {'✓ SYSTEM READY' if vector_store_ok and structured_output_ok else '⚠ NEEDS ATTENTION'}")


if __name__ == "__main__":
    print("Chọn chế độ test:")
    print("1. Test tự động với các trường hợp mẫu")
    print("2. Test tương tác")
    
    choice = input("Nhập lựa chọn (1 hoặc 2): ")
    
    if choice == "1":
        asyncio.run(test_video_lesson_creator())
    elif choice == "2":
        asyncio.run(interactive_test())
    else:
        print("Lựa chọn không hợp lệ!")
    asyncio.run(main())
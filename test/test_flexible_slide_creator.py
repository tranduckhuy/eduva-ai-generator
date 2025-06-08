import asyncio
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv()
from src.agents.rag_agent_template.flow import rag_agent_template_agent


async def test_flexible_slide_creation():
    """
    Test hệ thống tạo slide linh hoạt với các yêu cầu khác nhau về độ phức tạp
    """
    test_cases = [
        {
            "name": "Bài đơn giản - ít slide",
            "query": "Tạo bài giảng Toán lớp 10 về khái niệm hàm số, bài ngắn 10 phút"
        },
        {
            "name": "Bài phức tạp - nhiều slide", 
            "query": "Tạo bài giảng Vật lý lớp 12 về dao động điều hòa, bao gồm lý thuyết, công thức, ví dụ và bài tập, thời lượng 45 phút"
        },
        {
            "name": "Bài trung bình - slide vừa phải",
            "query": "Tạo bài giảng Hóa học lớp 11 về phản ứng oxy hóa khử, bài 25 phút có ví dụ minh họa"
        },
        {
            "name": "Yêu cầu cụ thể về cấu trúc",
            "query": "Tạo bài giảng Văn lớp 12 về tác phẩm Chí Phèo, cần có phần giới thiệu tác giả, phân tích nhân vật và ý nghĩa tác phẩm"
        }
    ]
    
    config = {"configurable": {"thread_id": "flexible_test"}}
    
    for i, test_case in enumerate(test_cases):
        print(f"\n{'='*80}")
        print(f"TEST {i+1}: {test_case['name']}")
        print(f"{'='*80}")
        print(f"Yêu cầu: {test_case['query']}")
        print("\n🔄 Đang xử lý...")
        
        try:
            input_dict = {
                "messages": [HumanMessage(content=test_case['query'])]
            }
            
            response = await rag_agent_template_agent.ainvoke(input_dict, config)
            
            print("\n📋 Kết quả:")
            print("-" * 60)
            result_content = response["messages"][-1].content
            
            # Đếm số slide được tạo
            slide_count = result_content.count("### SLIDE") + result_content.count("## SLIDE")
            print(f"🎯 Số lượng slide được tạo: {slide_count}")
            print("-" * 60)
            print(result_content)
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ Lỗi: {str(e)}")
        
        print("\n" + "="*80)


async def test_specific_requirements():
    """
    Test với các yêu cầu cụ thể về nội dung và cấu trúc
    """
    specific_tests = [
        {
            "name": "Yêu cầu bài ngắn",
            "query": "Tạo bài giảng ngắn 5 phút về định lý Pythagoras cho lớp 9, chỉ cần giải thích khái niệm cơ bản"
        },
        {
            "name": "Yêu cầu bài chi tiết",
            "query": "Tạo bài giảng chi tiết về Chiến tranh thế giới thứ 2 cho lớp 12, bao gồm nguyên nhân, diễn biến, hậu quả, thời lượng 60 phút"
        },
        {
            "name": "Yêu cầu tương tác cao",
            "query": "Tạo bài giảng Sinh học lớp 10 về quá trình quang hợp, cần nhiều hoạt động tương tác và thí nghiệm minh họa"
        }
    ]
    
    config = {"configurable": {"thread_id": "specific_test"}}
    
    for i, test_case in enumerate(specific_tests):
        print(f"\n{'🎯'*30}")
        print(f"SPECIFIC TEST {i+1}: {test_case['name']}")
        print(f"{'🎯'*30}")
        print(f"Yêu cầu: {test_case['query']}")
        
        try:
            input_dict = {
                "messages": [HumanMessage(content=test_case['query'])]
            }
            
            response = await rag_agent_template_agent.ainvoke(input_dict, config)
            result_content = response["messages"][-1].content
            
            # Phân tích kết quả
            slide_count = result_content.count("### SLIDE") + result_content.count("## SLIDE")
            has_interaction = "tương tác" in result_content.lower() or "hoạt động" in result_content.lower()
            has_examples = "ví dụ" in result_content.lower() or "minh họa" in result_content.lower()
            
            print(f"\n📊 Phân tích kết quả:")
            print(f"   • Số slide: {slide_count}")
            print(f"   • Có tương tác: {'✅' if has_interaction else '❌'}")
            print(f"   • Có ví dụ: {'✅' if has_examples else '❌'}")
            
            print(f"\n📝 Nội dung:")
            print("-" * 50)
            print(result_content[:800] + "..." if len(result_content) > 800 else result_content)
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Lỗi: {str(e)}")


async def interactive_flexible_test():
    """
    Test tương tác để kiểm tra tính linh hoạt
    """
    print("🎓 HỆ THỐNG TẠO SLIDE LINH HOẠT")
    print("=" * 50)
    print("Hệ thống sẽ tự động điều chỉnh số lượng slide theo:")
    print("• Độ phức tạp của chủ đề")
    print("• Thời lượng bài giảng")
    print("• Yêu cầu cụ thể của giáo viên")
    print("-" * 50)
    print("Nhập yêu cầu của bạn (hoặc 'quit' để thoát)")
    
    config = {"configurable": {"thread_id": "interactive_flexible"}}
    
    while True:
        user_input = input("\n👨‍🏫 Yêu cầu: ")
        
        if user_input.lower() in ['quit', 'exit', 'thoát']:
            print("Cảm ơn bạn đã test hệ thống!")
            break
            
        if not user_input.strip():
            continue
            
        try:
            input_dict = {
                "messages": [HumanMessage(content=user_input)]
            }
            
            print("\n🔄 Đang phân tích và tạo slide...")
            response = await rag_agent_template_agent.ainvoke(input_dict, config)
            result_content = response["messages"][-1].content
            
            # Đếm slide
            slide_count = result_content.count("### SLIDE") + result_content.count("## SLIDE")
            
            print(f"\n📊 Kết quả: Đã tạo {slide_count} slide")
            print("🎯 Nội dung:")
            print("-" * 50)
            print(result_content)
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Lỗi: {str(e)}")


if __name__ == "__main__":
    print("🧪 CHỌN CHỨC NĂNG TEST:")
    print("1. Test tính linh hoạt với các độ phức tạp khác nhau")
    print("2. Test với yêu cầu cụ thể")
    print("3. Test tương tác")
    
    choice = input("Nhập lựa chọn (1, 2, hoặc 3): ")
    
    if choice == "1":
        asyncio.run(test_flexible_slide_creation())
    elif choice == "2":
        asyncio.run(test_specific_requirements())
    elif choice == "3":
        asyncio.run(interactive_flexible_test())
    else:
        print("Lựa chọn không hợp lệ!")
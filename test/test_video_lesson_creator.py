import asyncio
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv()
from src.agents.rag_agent_template.flow import rag_agent_template_agent


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
        },
        {
            "name": "Tạo bài giảng Hóa học",
            "query": "Hỗ trợ tạo video Hóa học lớp 12 về phản ứng axit-bazơ, thời lượng 15 phút"
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
            
            response = await rag_agent_template_agent.ainvoke(input_dict, config)
            
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
            response = await rag_agent_template_agent.ainvoke(input_dict, config)
            
            print("\n🎯 Trợ lý AI:")
            print("-" * 40)
            print(response["messages"][-1].content)
            print("-" * 40)
            
        except Exception as e:
            print(f"❌ Lỗi: {str(e)}")


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
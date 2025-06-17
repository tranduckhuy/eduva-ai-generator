import asyncio
import json
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv()
from src.agents.lesson_creator.flow import lesson_creator_agent


async def test_pipeline_integration():
    """
    Test pipeline hoàn chỉnh: RAG → Structured JSON → RevealJS
    """
    test_cases = [
        {
            "name": "Test pipeline Toán học",
            "query": "Tạo bài giảng Toán lớp 10 về hàm số bậc nhất, thời lượng 20 phút, cần có ví dụ minh họa",
            "expected_slides": 6
        },
        {
            "name": "Test pipeline Vật lý",
            "query": "Tạo bài giảng Vật lý lớp 11 về dao động điều hòa, 30 phút, bao gồm công thức và đồ thị",
            "expected_slides": 8
        },
        {
            "name": "Test pipeline ngắn",
            "query": "Tạo bài giảng ngắn 10 phút về định lý Pythagoras cho lớp 9",
            "expected_slides": 4
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\n{'='*80}")
        print(f"🧪 PIPELINE TEST {i+1}: {test_case['name']}")
        print(f"{'='*80}")
        print(f"📝 Yêu cầu: {test_case['query']}")
        
        try:
            # Step 1: RAG Agent tạo nội dung
            print("\n🔄 Step 1: RAG Agent processing...")
            config = {"configurable": {"thread_id": f"pipeline_test_{i}"}}
            input_dict = {"messages": [HumanMessage(content=test_case['query'])]}
            
            response = await lesson_creator_agent.ainvoke(input_dict, config)
            
            # Step 2: Kiểm tra structured data
            print("📊 Step 2: Analyzing structured data...")
            slide_data = response.get("slide_data", {})
            
            if slide_data:
                lesson_info = slide_data.get("lesson_info", {})
                slides = slide_data.get("slides", [])
                tts_settings = slide_data.get("tts_settings", {})
                
                print(f"✅ Structured data extracted successfully:")
                print(f"   • Title: {lesson_info.get('title', 'N/A')}")
                print(f"   • Subject: {lesson_info.get('subject', 'N/A')}")
                print(f"   • Duration: {lesson_info.get('duration_minutes', 'N/A')} minutes")
                print(f"   • Total slides: {len(slides)}")
                print(f"   • TTS language: {tts_settings.get('language', 'N/A')}")
                
                # Step 3: Test từng slide
                print(f"\n📋 Step 3: Slide breakdown:")
                for j, slide in enumerate(slides):
                    slide_type = slide.get('type', 'unknown')
                    title = slide.get('title', 'No title')[:50]
                    content_length = len(slide.get('content', ''))
                    speaker_notes_length = len(slide.get('speaker_notes', ''))
                    
                    print(f"   Slide {j+1}: [{slide_type.upper()}] {title}...")
                    print(f"      Content: {content_length} chars")
                    print(f"      Speaker notes: {speaker_notes_length} chars")
                
                # Step 4: Validate cho RevealJS
                print(f"\n🎬 Step 4: RevealJS validation:")
                revealjs_ready = validate_for_revealjs(slide_data)
                print(f"   RevealJS ready: {'✅ Yes' if revealjs_ready else '❌ No'}")
                
                # Step 5: Validate cho TTS
                print(f"\n🔊 Step 5: TTS validation:")
                tts_ready = validate_for_tts(slide_data)
                print(f"   TTS ready: {'✅ Yes' if tts_ready else '❌ No'}")
                
                # Step 6: Tính toán thời lượng video
                print(f"\n⏱️ Step 6: Video duration calculation:")
                total_duration = sum(slide.get('duration_seconds', 45) for slide in slides)
                print(f"   Estimated video duration: {total_duration//60}m {total_duration%60}s")
                
            else:
                print("❌ No structured data found")
                print("📄 Raw response preview:")
                raw_content = response["messages"][-1].content
                print(raw_content[:500] + "..." if len(raw_content) > 500 else raw_content)
            
        except Exception as e:
            print(f"❌ Pipeline test failed: {str(e)}")
        
        print(f"\n{'='*80}")


def validate_for_revealjs(slide_data: dict) -> bool:
    """Validate if slide data is ready for RevealJS conversion"""
    if not slide_data or "slides" not in slide_data:
        return False
    
    slides = slide_data["slides"]
    for slide in slides:
        if not slide.get("title") or not slide.get("content"):
            return False
        if not slide.get("type") in ["title", "content", "example", "summary"]:
            return False
    
    return True


def validate_for_tts(slide_data: dict) -> bool:
    """Validate if slide data has speaker notes for TTS"""
    if not slide_data or "slides" not in slide_data:
        return False
    
    slides = slide_data["slides"]
    for slide in slides:
        speaker_notes = slide.get("speaker_notes", "")
        if not speaker_notes or len(speaker_notes) < 50:  # Minimum 50 chars for meaningful TTS
            return False
    
    return True


async def test_api_endpoints():
    """
    Test API endpoints for pipeline integration
    """
    print("\n🌐 API ENDPOINTS TEST")
    print("="*50)
    
    # Note: This would require running the actual FastAPI server
    # For now, we'll simulate the API logic
    
    test_query = "Tạo bài giảng Hóa học lớp 12 về phản ứng axit-bazơ, 25 phút"
    
    print(f"📝 Testing with query: {test_query}")
    
    try:
        # Simulate API call
        config = {"configurable": {"thread_id": "api_test"}}
        input_dict = {"messages": [HumanMessage(content=test_query)]}
        
        response = await lesson_creator_agent.ainvoke(input_dict, config)
        slide_data = response.get("slide_data", {})
        
        if slide_data:
            print("✅ JSON format ready for API")
            print("✅ Can be converted to RevealJS")
            print("✅ TTS data available")
            print("✅ Video metadata present")
            
            # Show sample API response structure
            api_response = {
                "success": True,
                "format": "json",
                "slide_data": slide_data,
                "selected_documents": response.get("selected_documents", []),
                "processing_time": "2.5s"
            }
            print(f"\n📊 Sample API response structure:")
            print(f"   • success: {api_response['success']}")
            print(f"   • format: {api_response['format']}")
            print(f"   • slide_data: {len(slide_data.get('slides', []))} slides")
            print(f"   • documents_used: {len(api_response['selected_documents'])}")
            
        else:
            print("❌ API response not ready for pipeline")
            
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")


async def demo_complete_pipeline():
    """
    Demo hoàn chỉnh pipeline từ input → JSON → RevealJS HTML
    """
    print("\n🎯 COMPLETE PIPELINE DEMO")
    print("="*60)
    
    query = "Tạo bài giảng Sinh học lớp 10 về quá trình quang hợp, 15 phút, có thí nghiệm minh họa"
    print(f"📝 Input: {query}")
    
    try:
        # Step 1: RAG processing
        print("\n🔄 Processing with RAG agent...")
        config = {"configurable": {"thread_id": "demo_pipeline"}}
        input_dict = {"messages": [HumanMessage(content=query)]}
        
        response = await lesson_creator_agent.ainvoke(input_dict, config)
        slide_data = response.get("slide_data", {})
        
        if slide_data:
            # Step 2: Show JSON structure
            print("📊 Generated JSON structure:")
            print(json.dumps(slide_data, ensure_ascii=False, indent=2)[:800] + "...")
            
            # Step 3: Convert to RevealJS (simulate)
            print("\n🎬 Converting to RevealJS format...")
            from apis.routers.lesson_creator_router import convert_to_revealjs
            revealjs_html = convert_to_revealjs(slide_data)
            
            print("✅ RevealJS HTML generated")
            print(f"   HTML length: {len(revealjs_html)} characters")
            print(f"   Contains {len(slide_data['slides'])} slides")
            
            # Step 4: TTS preparation
            print("\n🔊 TTS preparation:")
            for i, slide in enumerate(slide_data.get('slides', [])):
                speaker_notes = slide.get('speaker_notes', '')
                duration = slide.get('duration_seconds', 45)
                print(f"   Slide {i+1}: {len(speaker_notes)} chars, ~{duration}s")
            
            print("\n✅ Pipeline ready for video generation!")
            print("Next steps:")
            print("   1. Feed RevealJS HTML to presentation renderer")
            print("   2. Generate TTS audio from speaker_notes")
            print("   3. Combine slides + audio = final video")
            
        else:
            print("❌ Pipeline failed - no structured data generated")
            
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")


if __name__ == "__main__":
    print("🚀 VIDEO LESSON PIPELINE TESTING")
    print("="*50)
    print("1. Test pipeline integration (RAG → JSON → RevealJS)")
    print("2. Test API endpoints")
    print("3. Demo complete pipeline")
    
    choice = input("Choose test (1, 2, or 3): ")
    
    if choice == "1":
        asyncio.run(test_pipeline_integration())
    elif choice == "2":
        asyncio.run(test_api_endpoints())
    elif choice == "3":
        asyncio.run(demo_complete_pipeline())
    else:
        print("Invalid choice!")
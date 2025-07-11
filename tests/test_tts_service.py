"""
Test TTS Service functionality
"""
import asyncio
import os
import time
import logging
from src.services.tts_service import TTSService, create_tts_service, text_to_speech_file, estimate_speech_duration

logging.basicConfig(level=logging.INFO)

async def test_tts_service():
    """Test TTS Service with different configurations"""
    
    print("=== Testing TTS Service ===")
    
    # Test data
    test_texts = [
        "Xin chào, đây là test TTS service đầu tiên.",
        "Machine Learning là một nhánh của trí tuệ nhân tạo cho phép máy tính học và đưa ra quyết định từ dữ liệu.",
        "Python là ngôn ngữ lập trình mạnh mẽ và dễ học, được sử dụng rộng rãi trong khoa học dữ liệu và AI."
    ]
    
    # Test 1: Basic TTS Service
    print("\n1. Testing basic TTS service...")
    tts = create_tts_service()
    
    for i, text in enumerate(test_texts):
        print(f"   Text {i+1}: '{text[:50]}...'")
        
        # Estimate duration
        estimated_duration = tts.estimate_audio_duration(text)
        print(f"   Estimated duration: {estimated_duration:.2f}s")
        
        # Generate audio
        start_time = time.time()
        output_path = f"temp_tts_{i+1}.mp3"
        
        try:
            audio_path = tts.synthesize_text(text, output_path)
            generation_time = time.time() - start_time
            
            # Check file
            if os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                print(f"   ✓ Generated: {audio_path} ({file_size} bytes) in {generation_time:.2f}s")
                
                # Cleanup
                os.remove(audio_path)
            else:
                print(f"   ✗ Failed to generate audio file")
                
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    # Test 2: Different voice configurations
    print("\n2. Testing different voice configurations...")
    
    configs = [
        {"language_code": "vi-VN", "speaking_rate": 0.8, "pitch": -2.0},
        {"language_code": "vi-VN", "speaking_rate": 1.5, "pitch": 2.0},
        {"language_code": "en-US", "speaking_rate": 1.0, "gender": "MALE"}
    ]
    
    test_text = "Đây là test với các cấu hình voice khác nhau."
    
    for i, config in enumerate(configs):
        print(f"   Config {i+1}: {config}")
        
        try:
            tts_custom = TTSService(config)
            output_path = f"temp_tts_config_{i+1}.mp3"
            
            start_time = time.time()
            audio_path = tts_custom.synthesize_text(test_text, output_path)
            generation_time = time.time() - start_time
            
            if os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                print(f"   ✓ Generated: {file_size} bytes in {generation_time:.2f}s")
                os.remove(audio_path)
            
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    # Test 3: Performance statistics
    print("\n3. Testing performance statistics...")
    stats = tts.get_performance_stats()
    print(f"   Total calls: {stats['total_calls']}")
    print(f"   Total characters: {stats['total_characters']}")
    print(f"   Total duration: {stats['total_duration_seconds']:.2f}s")
    print(f"   Average chars per call: {stats['average_characters_per_call']:.1f}")
    print(f"   Characters per second: {stats['characters_per_second']:.1f}")
    
    # Test 4: Convenience functions
    print("\n4. Testing convenience functions...")
    
    test_text = "Test convenience function cho TTS service."
    output_path = "temp_convenience_test.mp3"
    
    try:
        # Quick text to speech
        audio_path = text_to_speech_file(
            test_text, 
            output_path, 
            language_code="vi-VN",
            speaking_rate=1.2
        )
        
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            print(f"   ✓ Convenience function: {file_size} bytes -> {audio_path}")
            os.remove(audio_path)
        
        # Quick duration estimate
        duration = estimate_speech_duration(test_text, speaking_rate=1.2)
        print(f"   ✓ Quick duration estimate: {duration:.2f}s")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 5: Silent audio generation
    print("\n5. Testing silent audio generation...")
    
    try:
        silent_path = "temp_silent.mp3"
        audio_path = tts.create_silent_audio(silent_path, duration=3.0)
        
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            print(f"   ✓ Silent audio: {file_size} bytes, 3.0s -> {audio_path}")
            os.remove(audio_path)
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 6: Error handling
    print("\n6. Testing error handling...")
    
    try:
        # Empty text
        tts.synthesize_text("", "temp_empty.mp3")
        print("   ✗ Should have failed with empty text")
    except ValueError as e:
        print(f"   ✓ Correctly handled empty text: {e}")
    except Exception as e:
        print(f"   ? Unexpected error: {e}")
    
    # Test 7: Bytes generation
    print("\n7. Testing bytes generation...")
    
    try:
        audio_bytes = tts.synthesize_text_to_bytes("Test audio bytes generation.")
        print(f"   ✓ Generated audio bytes: {len(audio_bytes)} bytes")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n=== TTS Service Test Complete ===")
    
    # Final stats
    final_stats = tts.get_performance_stats()
    print(f"\nFinal Performance Stats:")
    print(f"  Total calls: {final_stats['total_calls']}")
    print(f"  Total characters processed: {final_stats['total_characters']}")
    print(f"  Total processing time: {final_stats['total_duration_seconds']:.2f}s")
    print(f"  Average processing speed: {final_stats['characters_per_second']:.1f} chars/sec")

if __name__ == "__main__":
    asyncio.run(test_tts_service())

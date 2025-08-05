"""
Slide processing utilities for video generation
"""
import os
import uuid
from typing import Dict, Any
from .image_generator import ImageGenerator
from .content_formatter import ContentFormatter
from src.utils.logger import logger

class SlideProcessor:
    """Handles processing of individual slides including image generation and timing"""
    
    def __init__(self, unsplash_access_key: str = None):
        self.image_generator = ImageGenerator(unsplash_access_key)
        self.content_formatter = ContentFormatter()
    
    def process_slide_images(self, slide: Dict[str, Any], temp_dir: str, slide_id: int, image_resolution: tuple = (1280, 720), add_disclaimer: bool = False) -> Dict[str, Any]:
        """
        Process all images for a slide
        """
        keywords = slide.get('image_keywords', [])
        title = slide.get('title', '')
        content = slide.get('content', [])
        tts_script = slide.get('tts_script', '')
        temp_dir = os.path.normpath(temp_dir)

        if len(content) > 10:
            content = content[:10]
            logger.warning(f"Slide {slide_id} content truncated from {len(slide.get('content', []))} to 10 elements")

        # Calculate content duration for display
        content_duration = self.content_formatter.calculate_content_display_duration(tts_script)
        
        result = {
            'images': [],
            'content_duration': content_duration,
            'total_images': 0
        }

        # 1. Create main content image with smart template selection
        content_image_path = os.path.normpath(os.path.join(temp_dir, f"content_{slide_id}.jpg"))
        try:
            # Smart template selection based on slide position and content type
            content_type = "normal"  # You can make this dynamic based on slide content
            
            self.image_generator.create_content_image(
                title, content, content_image_path, image_resolution, 
                content_type, add_disclaimer, slide_id
            )
            
            if os.path.exists(content_image_path):
                result['images'].append({
                    'path': content_image_path,
                    'type': 'content',
                    'duration': content_duration
                })
        except Exception as e:
            logger.warning(f"Content image creation failed for slide {slide_id}: {e}")
        
        generated_image_path = None
        if keywords:
            ai_prompt = keywords[0] 
            
            image_path = os.path.join(temp_dir, f"ai_{slide_id}_{uuid.uuid4().hex[:8]}.png")
            generated_image_path = self.image_generator.generate_ai_image(
                prompt=ai_prompt,
                output_path=image_path,
                aspect_ratio="16:9"
            )

            if generated_image_path:
                result['images'].append({
                    'path': generated_image_path,
                    'type': 'ai_generated',
                    'duration': 3.0
                })

        # 2. Get up to 1 Unsplash image (optimized)
        if not generated_image_path and keywords and len(result['images']) < 2:
            try:
                image_url = self.image_generator.get_unsplash_image_url(keywords[1])
                if image_url:
                    image_path = os.path.join(temp_dir, f"unsplash_{slide_id}_{uuid.uuid4().hex[:8]}.jpg")
                    downloaded_path = self.image_generator.download_and_resize_image(image_url, image_path, image_resolution)
                    if downloaded_path and os.path.exists(downloaded_path):
                        result['images'].append({
                            'path': downloaded_path,
                            'type': 'unsplash',
                            'duration': 3.0
                        })
            except Exception as e:
                logger.warning(f"Unsplash processing failed for slide {slide_id}: {e}")

        # Fallback if no images were created
        if not result['images']:
            logger.warning(f"No images could be created for slide {slide_id}, creating fallback")
            try:
                fallback_path = os.path.normpath(os.path.join(temp_dir, f"fallback_{slide_id}.jpg"))
                created_path = self.image_generator.create_fallback_image(title or f"Slide {slide_id}", fallback_path, image_resolution)
                if created_path and os.path.exists(created_path):
                    result['images'].append({
                        'path': created_path,
                        'type': 'fallback',
                        'duration': content_duration
                    })
                    logger.info(f"Created fallback image for slide {slide_id}")
                else:
                    logger.error(f"Fallback image creation failed for slide {slide_id} - file not created")
            except Exception as e:
                logger.error(f"Failed to create fallback image for slide {slide_id}: {e}")
                
        # Final safety check - if still no images, this is a critical error
        if not result['images']:
            logger.error(f"Critical error: No images could be created for slide {slide_id}")
            raise ValueError(f"Failed to create any images for slide {slide_id}")
        result['total_images'] = len(result['images'])
        return result
    
    def calculate_slide_timing(self, slide_result: Dict[str, Any], audio_duration: float) -> Dict[str, Any]:
        """
        Calculate optimal timing for slide images based on content and audio duration
        """
        images = slide_result['images']
        content_duration = slide_result['content_duration']
        
        if not images:
            logger.warning("No images found for timing calculation")
            return slide_result
        
        # Ensure content image gets 80% of total audio time for comfortable reading
        content_time = audio_duration * 0.80  # 80% of total time for content slide
        
        # Calculate remaining time for other images
        remaining_time = audio_duration - content_time
        other_images = [img for img in images if img['type'] != 'content']
        
        if other_images and remaining_time > 0:
            time_per_other_image = remaining_time / len(other_images)
            
            # Update durations
            for img in images:
                if img['type'] == 'content':
                    img['duration'] = content_time
                else:
                    img['duration'] = max(1.5, time_per_other_image) 
        else:
            # Only content image or no other images, use full duration
            # Safely handle the case where images list might be empty
            if images:
                images[0]['duration'] = audio_duration
        
        # Verify total duration matches audio
        total_calculated = sum(img['duration'] for img in images)
        if abs(total_calculated - audio_duration) > 0.5:  # Allow small variance
            # Adjust proportionally
            adjustment_factor = audio_duration / total_calculated
            for img in images:
                img['duration'] *= adjustment_factor
        
        slide_result['images'] = images
        slide_result['total_duration'] = audio_duration
        
        if images:
            logger.debug(f"Slide timing calculated: {len(images)} images, "
                        f"content: {images[0]['duration']:.1f}s, "
                        f"total: {audio_duration:.1f}s")
        else:
            logger.debug(f"Slide timing calculated: 0 images, total: {audio_duration:.1f}s")
        
        return slide_result
    
    def reset_for_new_video(self):
        """Reset for new video generation"""
        self.image_generator.reset_for_new_video()
        logger.info("SlideProcessor reset for new video")
    
    def set_template_preference(self, template_name: str) -> bool:
        """Set user template preference"""
        return self.image_generator.set_user_template_preference(template_name)

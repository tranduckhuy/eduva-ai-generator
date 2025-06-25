"""
Slide processing utilities for video generation
"""
import os
from typing import List, Dict, Any
import logging
from .image_generator import ImageGenerator
from .content_formatter import ContentFormatter

logger = logging.getLogger(__name__)

class SlideProcessor:
    """Handles processing of individual slides including image generation and timing"""
    
    def __init__(self, unsplash_access_key: str = None):
        self.image_generator = ImageGenerator(unsplash_access_key)
        self.content_formatter = ContentFormatter()
    
    def process_slide_images(self, slide: Dict[str, Any], temp_dir: str, slide_id: int) -> Dict[str, Any]:
        """
        Process all images for a slide in an optimized way
        Returns dict with image paths and timing info
        """
        keywords = slide.get('image_keywords', [])
        title = slide.get('title', '')
        content = slide.get('content', [])
        tts_script = slide.get('tts_script', '')
        
        logger.info(f"Processing images for slide {slide_id}: {title[:30]}...")
        
        # Format content for display
        content_text = self.content_formatter.format_content_for_display(content)
        
        # Calculate appropriate display duration for content
        content_duration = self.content_formatter.calculate_content_display_duration(tts_script)
        
        result = {
            'images': [],
            'content_duration': content_duration,
            'total_images': 0
        }
        
        # 1. Create main content image (always present)
        content_image_path = os.path.join(temp_dir, f"content_{slide_id}.jpg")
        self.image_generator.create_content_image(title, content_text, content_image_path)
        result['images'].append({
            'path': content_image_path,
            'type': 'content',
            'duration': content_duration  # Content image gets longer duration
        })
        
        # 2. Get multiple Unsplash images in one request (if available)
        if keywords:
            content_context = self.content_formatter.get_content_context_for_search(content)
            unsplash_urls = self.image_generator.get_multiple_unsplash_images(
                keywords, content_context, max_images=3
            )
            
            if unsplash_urls:
                # Download all images
                downloaded_paths = self.image_generator.download_images(
                    unsplash_urls, temp_dir, slide_id
                )
                
                # Add text overlays and add to result
                for i, image_path in enumerate(downloaded_paths):
                    overlay_path = os.path.join(temp_dir, f"overlay_{slide_id}_{i}.jpg")
                    overlay_result = self.image_generator.add_text_overlay(
                        image_path, title, overlay_path
                    )
                    
                    result['images'].append({
                        'path': overlay_result,
                        'type': 'unsplash',
                        'duration':  3.0  # Default duration for Unsplash images
                    })
                
                logger.info(f"Added {len(downloaded_paths)} Unsplash images for slide {slide_id}")
        
        # 3. Create variation images if needed (max 2 to avoid overload)
        max_total_images = 3
        current_image_count = len(result['images'])
        
        if current_image_count < max_total_images:
            variations_needed = min(2, max_total_images - current_image_count)
            
            for i in range(variations_needed):
                variation_path = os.path.join(temp_dir, f"variation_{slide_id}_{i}.jpg")
                self.image_generator.create_content_variation(
                    title, content_text, keywords, variation_path, i
                )
                
                result['images'].append({
                    'path': variation_path,
                    'type': 'variation',
                    'duration': 2.0  # Default duration for variations
                })
        
        result['total_images'] = len(result['images'])
        logger.info(f"Slide {slide_id} processed: {result['total_images']} images, "
                   f"content duration: {content_duration:.1f}s")
        
        return result
    
    def calculate_slide_timing(self, slide_result: Dict[str, Any], audio_duration: float) -> Dict[str, Any]:
        """
        Calculate optimal timing for slide images based on content and audio duration
        """
        images = slide_result['images']
        content_duration = slide_result['content_duration']
        
        if not images:
            return slide_result
        
        # Ensure content image gets adequate time
        min_content_time = min(content_duration, audio_duration * 0.6)  # At least 60% of audio for content
        
        # Calculate remaining time for other images
        remaining_time = audio_duration - min_content_time
        other_images = [img for img in images if img['type'] != 'content']
        
        if other_images and remaining_time > 0:
            time_per_other_image = remaining_time / len(other_images)
            
            # Update durations
            for img in images:
                if img['type'] == 'content':
                    img['duration'] = min_content_time
                else:
                    img['duration'] = max(1.5, time_per_other_image)  # Minimum 1.5s per image
        else:
            # Only content image, use full duration
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
        
        logger.debug(f"Slide timing calculated: {len(images)} images, "
                    f"content: {images[0]['duration']:.1f}s, "
                    f"total: {audio_duration:.1f}s")
        
        return slide_result

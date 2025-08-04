"""
Image generation utilities for video creation with template support
"""
import os
import platform
import requests
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
from .slide_templates import SlideTemplateManager
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from src.utils.logger import logger

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
IMAGE_GENERATION_MODEL = os.getenv("IMAGE_GENERATION_MODEL", "imagen-3.0-generate-001")

class ImageGenerator:
    def __init__(self, unsplash_access_key: str = None, template_name: str = 'modern_blue'):
        self.unsplash_access_key = unsplash_access_key or os.getenv('UNSPLASH_ACCESS_KEY')
        self.is_windows = platform.system() == "Windows"
        
        # Initialize template manager
        self.template_manager = SlideTemplateManager()
        self.template_manager.set_template(template_name)

        try:
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            self.generation_model = ImageGenerationModel.from_pretrained(IMAGE_GENERATION_MODEL)
            logger.info("✅ Vertex AI initialized successfully.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Vertex AI: {e}")
            self.generation_model = None
        
    def set_template(self, template_name: str):
        """Set slide template"""
        self.template_manager.set_template(template_name)
    
    def get_available_templates(self) -> Dict[str, str]:
        """Get available templates"""
        return self.template_manager.get_available_templates()
    
    def download_images(self, image_urls: List[str], temp_dir: str, slide_id: int) -> List[str]:
        """
        Download multiple images from URLs
        """
        downloaded_paths = []
        
        for i, url in enumerate(image_urls):
            try:
                output_path = os.path.join(temp_dir, f"unsplash_{slide_id}_{i}.jpg")
                
                response = requests.get(url, timeout=20)
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    downloaded_paths.append(output_path)
            except Exception as e:
                logger.warning(f"Error downloading image {i+1}: {e}")
                continue
        
        return downloaded_paths
    
    def create_content_image(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        """Create content image using selected template"""
        return self.template_manager.create_content_image(title, contents, output_path, size)

    def add_text_overlay(self, image_path: str, title: str, output_path: str) -> str:
        """Add text overlay to an existing image"""
        try:
            img = Image.open(image_path)
            img = img.resize((1920, 1080), Image.Resampling.LANCZOS)
            
            # Create overlay
            overlay = Image.new('RGBA', (1920, 1080), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            # Add semi-transparent background for text
            draw.rectangle([0, 0, 1920, 200], fill=(0, 0, 0, 180))
            
            # Load font
            try:
                if self.is_windows:
                    font = ImageFont.truetype("arial.ttf", 48)
                else:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            # Draw title
            title_text = title[:80] + "..." if len(title) > 80 else title
            title_bbox = draw.textbbox((0, 0), title_text, font=font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (1920 - title_width) // 2
            draw.text((title_x, 60), title_text, fill='white', font=font)
            
            # Combine images
            img = img.convert('RGBA')
            img = Image.alpha_composite(img, overlay)
            img = img.convert('RGB')
            img.save(output_path, 'JPEG', quality=85)
            
            return output_path
        except Exception as e:
            logger.warning(f"Error adding text overlay: {e}")
            # Copy original image if overlay fails
            try:
                img = Image.open(image_path)
                img.save(output_path, 'JPEG', quality=85)
                return output_path
            except:
                return image_path
    
    def generate_ai_image(self, prompt: str, output_path: str, aspect_ratio: str = "16:9") -> str:
        """Generates an image using Vertex AI and saves it."""
        if not self.generation_model:
            logger.warning("Vertex AI model is not available. Skipping AI image generation.")
            return None
        
        try:
            logger.info(f"🤖 Generating AI image with prompt: '{prompt}'")
            images = self.generation_model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                negative_prompt="text, watermark, blurry, low quality"
            )
            
            if images.images:
                images.images[0].save(location=output_path)

                if os.path.exists(output_path):
                    logger.info(f"🖼️ AI image saved successfully to {output_path}")
                    return output_path
                else:
                    logger.error("❌ Failed to save the image to disk.")
                    return None
            else:
                logger.warning(f"⚠️ AI model returned no images for prompt: '{prompt}'. This might be due to a safety filter.")
                return None
            
        except Exception as e:
            logger.error(f"❌ AI image generation failed for prompt '{prompt}': {e}")
            return None

    def get_single_unsplash_image_fast(self, keyword: str) -> str:
        """Get a single image from Unsplash quickly - optimized for speed"""
        if not self.unsplash_access_key or not keyword:
            return None
        try:
            url = "https://api.unsplash.com/search/photos"
            params = {
                'query': keyword,
                'client_id': self.unsplash_access_key,
                'orientation': 'landscape',
                'per_page': 1,
                'order_by': 'relevance',
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    photo = data['results'][0]
                    image_url = photo['urls']['regular']
                    return image_url
        except Exception as e:
            logger.warning(f"Fast Unsplash error for '{keyword}': {e}")
        return None
    
    def download_single_image_fast(self, image_url: str, output_path: str, max_size: tuple = (1280, 720)) -> str:
        """Download and resize a single image quickly"""
        try:
            response = requests.get(image_url, timeout=15, stream=True)
            if response.status_code == 200:
                image = Image.open(response.raw)
                image.thumbnail(max_size, Image.LANCZOS)
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                image.save(output_path, 'JPEG', quality=85, optimize=True)
                image.close()
                if os.path.exists(output_path):
                    return output_path
        except Exception as e:
            logger.warning(f"Fast image download failed: {e}")
        return None

    def create_simple_fallback(self, title: str, output_path: str, size: tuple = (1280, 720)):
        """Create ultra-simple fallback image"""
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            image = Image.new('RGB', size, color='#34495e')
            draw = ImageDraw.Draw(image)
            try:
                font = ImageFont.load_default()
                text = title or "Slide"
                # Wrap text if it's too long
                if len(text) > 50:
                    text = text[:47] + "..."
                bbox = draw.textbbox((0, 0), text, font=font)
                x = (size[0] - (bbox[2] - bbox[0])) // 2
                y = (size[1] - (bbox[3] - bbox[1])) // 2
                draw.text((x, y), text, font=font, fill='white')
            except Exception as font_error:
                logger.warning(f"Font rendering failed: {font_error}")
                # Still create the image without text
                pass
                
            image.save(output_path, 'JPEG', quality=80)
            image.close()
            logger.debug(f"Simple fallback image created: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Simple fallback failed: {e}")
            return None

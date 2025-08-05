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
    """Unified image generator with template management and multiple sources"""
    
    def __init__(self, unsplash_access_key: Optional[str] = None, template_name: Optional[str] = None):
        self.unsplash_access_key = unsplash_access_key or os.getenv('UNSPLASH_ACCESS_KEY')
        self.template_manager = SlideTemplateManager()
        
        if template_name:
            self.template_manager.set_user_preference(template_name)

        # Initialize Vertex AI (optional)
        self.generation_model = self._init_vertex_ai()
    
    def _init_vertex_ai(self) -> Optional[ImageGenerationModel]:
        """Initialize Vertex AI with error handling"""
        try:
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            model = ImageGenerationModel.from_pretrained(IMAGE_GENERATION_MODEL)
            logger.info("✅ Vertex AI initialized")
            return model
        except Exception as e:
            logger.warning(f"⚠️ Vertex AI unavailable: {e}")
            return None
    
    # Core functionality
    def create_content_image(self, title: str, contents: List[str], output_path: str, 
                           size: tuple = (1280, 720), content_type: str = "normal", 
                           add_disclaimer: bool = False, slide_id: Optional[int] = None) -> str:
        """Create content slide image with smart template selection"""
        return self.template_manager.create_slide_image(
            title, contents, output_path, size, content_type, add_disclaimer, slide_id
        )
    
    def reset_for_new_video(self) -> None:
        """Reset template manager for new video"""
        self.template_manager.reset_for_new_video()
    
    # Template management
    def set_user_template_preference(self, template_name: str) -> bool:
        """Set user template preference"""
        return self.template_manager.set_user_preference(template_name)
    
    def get_available_templates(self) -> Dict[str, str]:
        """Get available templates"""
        return self.template_manager.get_available_templates()
    
    def get_template_status(self) -> Dict[str, Any]:
        """Get current template status"""
        return self.template_manager.get_status()

    # AI image generation
    def generate_ai_image(self, prompt: str, output_path: str, aspect_ratio: str = "16:9") -> Optional[str]:
        """Generate AI image using Vertex AI"""
        if not self.generation_model:
            logger.warning("Vertex AI unavailable, skipping AI generation")
            return None
        
        try:
            images = self.generation_model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                negative_prompt="text, watermark, blurry, low quality"
            )
            
            if images.images:
                images.images[0].save(location=output_path)
                return output_path if os.path.exists(output_path) else None
            
            logger.warning(f"No images generated for: '{prompt}'")
            return None
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return None

    # External image sources
    def get_unsplash_image_url(self, keyword: str) -> Optional[str]:
        """Get single Unsplash image URL"""
        if not self.unsplash_access_key or not keyword:
            return None
            
        try:
            response = requests.get("https://api.unsplash.com/search/photos", 
                params={
                    'query': keyword,
                    'client_id': self.unsplash_access_key,
                    'orientation': 'landscape',
                    'per_page': 1,
                    'order_by': 'relevance',
                }, 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['results'][0]['urls']['regular'] if data['results'] else None
                
        except Exception as e:
            logger.warning(f"Unsplash error for '{keyword}': {e}")
        
        return None
    
    def download_and_resize_image(self, image_url: str, output_path: str, 
                                 max_size: tuple = (1280, 720)) -> Optional[str]:
        """Download and resize image from URL"""
        try:
            response = requests.get(image_url, timeout=15, stream=True)
            if response.status_code == 200:
                with Image.open(response.raw) as img:
                    img.thumbnail(max_size, Image.LANCZOS)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    img.save(output_path, 'JPEG', quality=85, optimize=True)
                    
                return output_path if os.path.exists(output_path) else None
                
        except Exception as e:
            logger.warning(f"Download failed: {e}")
        
        return None

    # Fallback
    def create_fallback_image(self, title: str, output_path: str, 
                            size: tuple = (1280, 720)) -> Optional[str]:
        """Create simple fallback image"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with Image.new('RGB', size, color='#34495e') as img:
                draw = ImageDraw.Draw(img)
                
                try:
                    font = ImageFont.load_default()
                    text = (title[:47] + "...") if len(title) > 50 else title or "Slide"
                    
                    bbox = draw.textbbox((0, 0), text, font=font)
                    x = (size[0] - (bbox[2] - bbox[0])) // 2
                    y = (size[1] - (bbox[3] - bbox[1])) // 2
                    draw.text((x, y), text, font=font, fill='white')
                except Exception:
                    pass  # Create image without text if font fails
                    
                img.save(output_path, 'JPEG', quality=80)
            
            logger.debug(f"Fallback image created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Fallback creation failed: {e}")
            return None

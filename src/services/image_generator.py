"""
Image generation utilities for video creation
"""
import os
import platform
import requests
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self, unsplash_access_key: str = None):
        self.unsplash_access_key = unsplash_access_key or os.getenv('UNSPLASH_ACCESS_KEY')
        self.is_windows = platform.system() == "Windows"
    
    def get_multiple_unsplash_images(self, keywords: List[str], content_context: str = "", max_images: int = 5) -> List[str]:
        """
        Get multiple images from Unsplash in a single request based on keywords
        """
        if not self.unsplash_access_key or not keywords:
            return []
        
        # Combine all keywords for better search
        main_keyword = keywords[0]
        additional_keywords = ' '.join(keywords[1:3]) if len(keywords) > 1 else ""
        
        search_query = main_keyword
        if additional_keywords:
            search_query = f"{main_keyword} {additional_keywords}"
        if content_context:
            context_words = content_context.lower().split()[:2]  # First 2 context words
            search_query = f"{search_query} {' '.join(context_words)}"
        
        try:
            url = "https://api.unsplash.com/search/photos"
            params = {
                'query': search_query,
                'client_id': self.unsplash_access_key,
                'orientation': 'landscape',
                'per_page': max_images,
                'order_by': 'relevance',
            }
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    # Get URLs for all results
                    image_urls = []
                    for result in data['results']:
                        image_urls.append(result['urls']['regular'])
                    
                    logger.info(f"Found {len(image_urls)} images for query: {search_query}")
                    return image_urls
                else:
                    logger.warning(f"No results found on Unsplash for: {search_query}")
            else:
                logger.warning(f"Unsplash API error: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Error searching Unsplash: {e}")
        
        return []
    
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
                    logger.debug(f"Downloaded image {i+1}: {output_path}")
            except Exception as e:
                logger.warning(f"Error downloading image {i+1}: {e}")
                continue
        
        return downloaded_paths
    
    def create_content_image(self, title: str, content: str, output_path: str) -> str:
        """Create an image with title, content, and visual elements"""
        # Create a 1920x1080 image with gradient background
        img = Image.new('RGB', (1920, 1080), color='#1a202c')
        draw = ImageDraw.Draw(img)
        
        # Create gradient background
        for y in range(1080):
            color_value = int(26 + (y / 1080) * 30)
            color = (color_value, color_value + 10, color_value + 20)
            draw.line([(0, y), (1920, y)], fill=color)
        
        # Load fonts
        try:
            if self.is_windows:
                title_font = ImageFont.truetype("arial.ttf", 64)
                content_font = ImageFont.truetype("arial.ttf", 32)
            else:
                # Linux/Mac font paths
                for font_path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 
                                "/System/Library/Fonts/Arial.ttf",
                                "/usr/share/fonts/TTF/arial.ttf"]:
                    try:
                        title_font = ImageFont.truetype(font_path, 64)
                        content_font = ImageFont.truetype(font_path, 32)
                        break
                    except:
                        continue
                else:
                    raise OSError("No suitable font found")
        except:
            # Fallback to default fonts
            title_font = ImageFont.load_default()
            content_font = ImageFont.load_default()
        
        # Draw title with background
        title_text = title[:60] + "..." if len(title) > 60 else title
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        title_x = (1920 - title_width) // 2
        title_y = 80
        
        # Draw title background
        padding = 20
        draw.rectangle([title_x - padding, title_y - padding, 
                       title_x + title_width + padding, title_y + title_height + padding], 
                      fill='#2d3748', outline='#4a5568', width=2)
        draw.text((title_x, title_y), title_text, fill='#ffffff', font=title_font)
        
        # Draw content with bullet points
        if content:
            content_text = content[:800] + "..." if len(content) > 800 else content
            
            # Split content into lines
            if '\n' in content_text:
                content_lines = content_text.split('\n')[:10]  # Max 10 lines
            else:
                # Split by sentences and create bullet points
                sentences = content_text.split('. ')
                content_lines = []
                for sentence in sentences[:8]:  # Max 8 sentences
                    if sentence.strip():
                        bullet_line = f"• {sentence.strip()}"
                        if not sentence.endswith('.'):
                            bullet_line += "."
                        content_lines.append(bullet_line)
            
            if content_lines:
                # Draw content background
                content_y = 220
                line_height = 50  # Increased line height for better readability
                total_height = len(content_lines) * line_height + 50
                
                draw.rectangle([80, content_y - 25, 1840, content_y + total_height], 
                              fill='#2a4365', outline='#3182ce', width=2)
                
                # Draw each line with proper wrapping
                current_y = content_y
                for line in content_lines:
                    if len(line) > 85:  # Wrap long lines
                        words = line.split()
                        wrapped_lines = []
                        current_line = ""
                        
                        for word in words:
                            test_line = current_line + word + " "
                            test_bbox = draw.textbbox((0, 0), test_line, font=content_font)
                            if test_bbox[2] - test_bbox[0] > 1600:  # Max width
                                if current_line:
                                    wrapped_lines.append(current_line.strip())
                                    current_line = "  " + word + " "  # Indent continuation
                                else:
                                    wrapped_lines.append(word)
                                    current_line = ""
                            else:
                                current_line = test_line
                        
                        if current_line:
                            wrapped_lines.append(current_line.strip())
                        
                        # Draw wrapped lines
                        for wrapped_line in wrapped_lines:
                            draw.text((120, current_y), wrapped_line, fill='#e2e8f0', font=content_font)
                            current_y += line_height
                    else:
                        draw.text((120, current_y), line, fill='#e2e8f0', font=content_font)
                        current_y += line_height
        
        img.save(output_path, 'JPEG', quality=90)
        logger.debug(f"Content image created: {output_path}")
        return output_path
    
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
            # draw.rectangle([0, 880, 1920, 1080], fill=(0, 0, 0, 120))
            
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
    
    def create_content_variation(self, title: str, content: str, output_path: str, variation_index: int) -> str:
        """Create different visual variations of content"""
        colors = [
            ('#1a202c', '#2d3748', '#4a5568'),  # Dark blue-gray
            ('#2a4365', '#3182ce', '#4299e1'),  # Blue
            ('#38a169', '#48bb78', '#68d391'),  # Green
            ('#d69e2e', '#f6e05e', '#faf089'),  # Yellow
        ]
        
        color_set = colors[variation_index % len(colors)]
        
        # Create image with different color scheme
        img = Image.new('RGB', (1920, 1080), color=color_set[0])
        draw = ImageDraw.Draw(img)
        
        # Create different patterns for each variation
        if variation_index == 0:
            # Diagonal lines pattern
            for i in range(0, 2000, 50):
                draw.line([(i, 0), (i-1080, 1080)], fill=color_set[1], width=2)
        elif variation_index == 1:
            # Circle pattern
            for x in range(200, 1800, 300):
                for y in range(200, 900, 300):
                    draw.ellipse([x-50, y-50, x+50, y+50], outline=color_set[1], width=3)
        else:
            # Rectangle pattern
            for x in range(100, 1900, 200):
                for y in range(100, 1000, 200):
                    draw.rectangle([x, y, x+100, y+100], outline=color_set[1], width=2)
        
        # Add content similar to main content image but with different styling
        try:
            if self.is_windows:
                title_font = ImageFont.truetype("arial.ttf", 56)
                content_font = ImageFont.truetype("arial.ttf", 28)
            else:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 56)
                content_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
        except:
            title_font = ImageFont.load_default()
            content_font = ImageFont.load_default()
        
        # Draw title
        title_text = title[:70] + "..." if len(title) > 70 else title
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (1920 - title_width) // 2
        
        # Title background
        draw.rectangle([title_x - 20, 150, title_x + title_width + 20, 220], 
                      fill=color_set[1], outline=color_set[2], width=2)
        draw.text((title_x, 160), title_text, fill='white', font=title_font)
        
        # Draw partial content
        if content:
            content_lines = content[:300].split('\n')[:5]  # Max 5 lines, 300 chars
            for i, line in enumerate(content_lines):
                if line.strip():
                    draw.text((200, 400 + i * 40), line[:80], fill='white', font=content_font)
        
        img.save(output_path, 'JPEG', quality=85)
        return output_path

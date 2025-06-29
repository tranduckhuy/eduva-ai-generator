"""
Slide Templates for beautiful video generation
"""
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont
import os
import logging

logger = logging.getLogger(__name__)

class SlideTemplate:
    """Base class for slide templates"""
    
    def __init__(self):
        self.is_windows = os.name == 'nt'
    
    def get_fonts(self, title_size: int = 48, content_size: int = 32):
        """Get fonts with fallback"""
        try:
            if self.is_windows:
                title_font = ImageFont.truetype("arial.ttf", title_size)
                content_font = ImageFont.truetype("arial.ttf", content_size)
            else:
                title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", title_size)
                content_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", content_size)
        except:
            title_font = ImageFont.load_default()
            content_font = ImageFont.load_default()
        return title_font, content_font
    
    def wrap_text(self, draw, text: str, font, max_width: int) -> List[str]:
        """Smart text wrapping"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        return lines

class ModernBlueTemplate(SlideTemplate):
    """Modern blue professional template"""
    
    def create(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        img = Image.new('RGB', size, color='#0f172a')  # Dark navy
        draw = ImageDraw.Draw(img)
        
        # Modern gradient
        for y in range(size[1]):
            alpha = y / size[1]
            r = int(15 + alpha * 30)   # 15-45
            g = int(23 + alpha * 60)   # 23-83  
            b = int(42 + alpha * 100)  # 42-142
            draw.line([(0, y), (size[0], y)], fill=(r, g, b))
        
        # Accent shapes
        draw.ellipse([size[0]-200, -100, size[0]+100, 200], fill='#1e40af', outline=None)
        draw.rectangle([0, size[1]-80, size[0], size[1]], fill='#1e3a8a')
        
        title_font, content_font = self.get_fonts(42, 28)
        
        # Title
        title_lines = self.wrap_text(draw, title, title_font, size[0] - 120)
        y = 80
        for line in title_lines[:2]:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            x = (size[0] - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, font=title_font, fill='#ffffff')
            y += 55
        
        # Content
        content_y = y + 40
        margin = 80
        for i, content_item in enumerate(contents[:5]):
            content_lines = self.wrap_text(draw, content_item, content_font, size[0] - margin*2 - 40)
            for j, line in enumerate(content_lines[:2]):
                if content_y > size[1] - 120:
                    break
                x = margin
                if j == 0:
                    draw.ellipse([x-20, content_y+5, x-10, content_y+15], fill='#3b82f6')
                    x += 30
                else:
                    x += 30
                draw.text((x, content_y), line, font=content_font, fill='#e2e8f0')
                content_y += 38
            content_y += 10
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'JPEG', quality=95)
        return output_path

class MinimalGreenTemplate(SlideTemplate):
    """Clean minimal green template"""
    
    def create(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        img = Image.new('RGB', size, color='#f8fafc')  # Very light gray
        draw = ImageDraw.Draw(img)
        
        # Subtle pattern
        for x in range(0, size[0], 60):
            for y in range(0, size[1], 60):
                draw.rectangle([x, y, x+1, y+1], fill='#e2e8f0')
        
        # Header band
        draw.rectangle([0, 0, size[0], 120], fill='#059669')
        
        # Side accent
        draw.rectangle([0, 120, 8, size[1]], fill='#10b981')
        
        title_font, content_font = self.get_fonts(44, 30)
        
        # Title
        title_lines = self.wrap_text(draw, title, title_font, size[0] - 60)
        y = 35
        for line in title_lines[:2]:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            x = (size[0] - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, font=title_font, fill='#ffffff')
            y += 50
        
        # Content
        content_y = 180
        margin = 50
        for i, content_item in enumerate(contents[:6]):
            content_lines = self.wrap_text(draw, content_item, content_font, size[0] - margin*2 - 50)
            for j, line in enumerate(content_lines[:2]):
                if content_y > size[1] - 80:
                    break
                x = margin
                if j == 0:
                    draw.text((x, content_y), "→", font=content_font, fill='#059669')
                    x += 40
                else:
                    x += 40
                draw.text((x, content_y), line, font=content_font, fill='#374151')
                content_y += 40
            content_y += 8
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'JPEG', quality=95)
        return output_path

class DarkModeTemplate(SlideTemplate):
    """Modern dark mode template"""
    
    def create(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        img = Image.new('RGB', size, color='#111827')  # Dark gray
        draw = ImageDraw.Draw(img)
        
        # Subtle grid pattern
        for x in range(0, size[0], 40):
            draw.line([(x, 0), (x, size[1])], fill='#1f2937', width=1)
        for y in range(0, size[1], 40):
            draw.line([(0, y), (size[0], y)], fill='#1f2937', width=1)
        
        # Accent elements
        draw.ellipse([size[0]-150, size[1]-150, size[0]+50, size[1]+50], fill='#7c3aed')
        draw.rectangle([0, 0, 6, size[1]], fill='#a855f7')
        
        title_font, content_font = self.get_fonts(46, 29)
        
        # Title with glow effect
        title_lines = self.wrap_text(draw, title, title_font, size[0] - 100)
        y = 60
        for line in title_lines[:2]:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            x = 60
            # Glow effect
            for offset in [(1,1), (-1,-1), (1,-1), (-1,1)]:
                draw.text((x+offset[0], y+offset[1]), line, font=title_font, fill='#7c3aed')
            draw.text((x, y), line, font=title_font, fill='#ffffff')
            y += 55
        
        # Content
        content_y = y + 50
        margin = 60
        for i, content_item in enumerate(contents[:5]):
            content_lines = self.wrap_text(draw, content_item, content_font, size[0] - margin*2 - 60)
            for j, line in enumerate(content_lines[:2]):
                if content_y > size[1] - 100:
                    break
                x = margin
                if j == 0:
                    draw.rectangle([x-8, content_y+5, x-4, content_y+25], fill='#a855f7')
                    x += 20
                else:
                    x += 20
                draw.text((x, content_y), line, font=content_font, fill='#d1d5db')
                content_y += 38
            content_y += 12
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'JPEG', quality=95)
        return output_path

class CreativeOrangeTemplate(SlideTemplate):
    """Creative orange template with shapes"""
    
    def create(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        img = Image.new('RGB', size, color='#fef3c7')  # Light orange
        draw = ImageDraw.Draw(img)
        
        # Creative shapes
        draw.ellipse([size[0]-300, -100, size[0]+100, 300], fill='#f59e0b')
        draw.ellipse([size[0]-250, -50, size[0]+50, 250], fill='#fbbf24')
        draw.polygon([(0, 0), (200, 0), (150, 150), (0, 100)], fill='#d97706')
        
        title_font, content_font = self.get_fonts(48, 30)
        
        # Title
        title_lines = self.wrap_text(draw, title, title_font, size[0] - 180)
        y = 80
        for line in title_lines[:2]:
            x = 60
            # Shadow
            draw.text((x+2, y+2), line, font=title_font, fill='#92400e')
            draw.text((x, y), line, font=title_font, fill="#dba2a2")
            y += 55
        
        # Content box
        draw.rectangle([40, y+20, size[0]-40, size[1]-40], fill='#ffffff', outline='#f59e0b', width=3)
        
        # Content
        content_y = y + 60
        margin = 70
        for i, content_item in enumerate(contents[:5]):
            content_lines = self.wrap_text(draw, content_item, content_font, size[0] - margin*2 - 40)
            for j, line in enumerate(content_lines[:2]):
                if content_y > size[1] - 100:
                    break
                x = margin
                if j == 0:
                    draw.text((x, content_y), "★", font=content_font, fill='#f59e0b')
                    x += 35
                else:
                    x += 35
                draw.text((x, content_y), line, font=content_font, fill='#78350f')
                content_y += 40
            content_y += 8
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'JPEG', quality=95)
        return output_path

class SlideTemplateManager:
    """Manager for slide templates"""
    
    def __init__(self):
        self.templates = {
            'modern_blue': ModernBlueTemplate(),
            'minimal_green': MinimalGreenTemplate(),
            'dark_mode': DarkModeTemplate(),
            'creative_orange': CreativeOrangeTemplate()
        }
        self.current_template = 'modern_blue'
    
    def set_template(self, template_name: str):
        """Set the current template"""
        if template_name in self.templates:
            self.current_template = template_name
            logger.info(f"Template set to: {template_name}")
        else:
            logger.warning(f"Template '{template_name}' not found. Available: {list(self.templates.keys())}")
    
    def get_available_templates(self) -> Dict[str, str]:
        """Get list of available templates with descriptions"""
        return {
            'modern_blue': 'Modern Blue - Professional blue gradient with clean typography',
            'minimal_green': 'Minimal Green - Clean white background with green accents',
            'dark_mode': 'Dark Mode - Modern dark theme with purple accents',
            'creative_orange': 'Creative Orange - Vibrant orange with creative shapes'
        }
    
    def create_content_image(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        """Create content image using current template"""
        template = self.templates[self.current_template]
        return template.create(title, contents, output_path, size)
    
    def cycle_template(self):
        """Cycle to next template (useful for variety)"""
        template_names = list(self.templates.keys())
        current_index = template_names.index(self.current_template)
        next_index = (current_index + 1) % len(template_names)
        self.current_template = template_names[next_index]
        logger.info(f"Template cycled to: {self.current_template}")
        return self.current_template

"""
Slide Templates for beautiful video generation
"""
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont
import os
import logging
import random

logger = logging.getLogger(__name__)

class SlideTemplate:
    """Base class for slide templates"""
    
    def __init__(self):
        self.is_windows = os.name == 'nt'
    
    def get_fonts(self, title_size: int = 48, content_size: int = 32):
        """Get fonts with fallback"""
        try:
            if self.is_windows:
                font_path = "arial.ttf"
            elif os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            elif os.path.exists("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"):
                font_path = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
            else:
                font_path = None

            if font_path:
                title_font = ImageFont.truetype(font_path, title_size)
                content_font = ImageFont.truetype(font_path, content_size)
            else:
                raise Exception("Font not found")

        except Exception as e:
            logger.warning(f"Font load failed: {e}")
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
        
        title_font, content_font = self.get_fonts(40, 26)
        
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
        for i, content_item in enumerate(contents):
            content_lines = self.wrap_text(draw, content_item, content_font, size[0] - margin*2 - 40)
            is_child_content = content_item.startswith('- ')
            for j, line in enumerate(content_lines):
                if content_y > size[1] - 120:
                    break
                x = margin
                if j == 0 and not is_child_content:
                    bullet_offset_y = 10
                    draw.ellipse([x-20, content_y + bullet_offset_y, x-10, content_y + bullet_offset_y + 10], fill='#3b82f6')
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
        
        title_font, content_font = self.get_fonts(40, 26)
        
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
        for i, content_item in enumerate(contents):
            content_lines = self.wrap_text(draw, content_item, content_font, size[0] - margin*2 - 50)
            is_child_content = content_item.startswith('- ')
            for j, line in enumerate(content_lines):
                if content_y > size[1] - 80:
                    break
                x = margin
                if j == 0 and not is_child_content:
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
        
        title_font, content_font = self.get_fonts(40, 26)
        
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
        for i, content_item in enumerate(contents):
            content_lines = self.wrap_text(draw, content_item, content_font, size[0] - margin*2 - 60)
            is_child_content = content_item.startswith('- ')
            for j, line in enumerate(content_lines):
                if content_y > size[1] - 100:
                    break
                x = margin
                if j == 0 and not is_child_content:
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
        
        title_font, content_font = self.get_fonts(40, 26)
        
        # Truncate title if too long (limit to 80 characters)
        if len(title) > 80:
            title = title[:77] + "..."

        # Title
        title_lines = self.wrap_text(draw, title, title_font, size[0] - 180)
        y = 30  # Start title higher
        for line in title_lines[:2]:
            x = 60
            # Shadow
            draw.text((x+2, y+2), line, font=title_font, fill='#92400e')
            draw.text((x, y), line, font=title_font, fill="#dba2a2")
            y += 50  # Reduced line spacing
        
        # Content box
        draw.rectangle([40, y+15, size[0]-40, size[1]-40], fill='#ffffff', outline='#f59e0b', width=3)
        
        # Content
        content_y = y + 45  # Reduced gap
        margin = 70
        for i, content_item in enumerate(contents):
            content_lines = self.wrap_text(draw, content_item, content_font, size[0] - margin*2 - 40)
            is_child_content = content_item.startswith('- ')
            for j, line in enumerate(content_lines):
                if content_y > size[1] - 100:
                    break
                x = margin
                if j == 0 and not is_child_content:
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

class CleanWhiteTemplate(SlideTemplate):
    """Clean and professional white template with subtle accents."""
    
    def create(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        img = Image.new('RGB', size, color='#ffffff')  # Pure white background
        draw = ImageDraw.Draw(img)
        
        # Subtle light gray footer/header
        draw.rectangle([0, 0, size[0], 20], fill='#e0e0e0')
        draw.rectangle([0, size[1]-20, size[0], size[1]], fill='#e0e0e0')

        # A thin accent line on the left
        draw.rectangle([0, 0, 10, size[1]], fill='#4285F4') # Google Blue-ish

        title_font, content_font = self.get_fonts(40, 26)
        
        # Truncate title if too long (limit to 80 characters)
        if len(title) > 80:
            title = title[:77] + "..."

        # Title
        title_lines = self.wrap_text(draw, title, title_font, size[0] - 160)
        y = 60  # Start title higher
        for line in title_lines[:2]:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            x = 80 # Align title to the left
            draw.text((x, y), line, font=title_font, fill='#333333') # Dark gray text
            y += 55 # Reduced line spacing for title
        
        # Content
        content_y = y + 40  # Reduced gap between title and content
        margin = 80
        for i, content_item in enumerate(contents):
            content_lines = self.wrap_text(draw, content_item, content_font, size[0] - margin*2 - 40)
            is_child_content = content_item.startswith('- ')
            for j, line in enumerate(content_lines):
                if content_y > size[1] - 80:
                    break
                x = margin
                if j == 0 and not is_child_content:
                    bullet_y_offset = 10 # Fine-tune this
                    # Using a square bullet for a clean look
                    draw.rectangle([x-18, content_y + bullet_y_offset, x-8, content_y + bullet_y_offset + 10], fill='#4285F4')
                    x += 30 # Space for bullet
                else:
                    x += 30 # Indent for wrapped lines or child content
                draw.text((x, content_y), line, font=content_font, fill='#555555') # Medium gray text
                content_y += 40 # Line spacing for content
            content_y += 15 # Spacing between content items


        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'JPEG', quality=95)
        return output_path


class BlueAccentTemplate(SlideTemplate):
    """Template designed to mimic the provided image with a large blue accent."""
    
    def create(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        img = Image.new('RGB', size, color='#0F172A')  # Deep navy background
        draw = ImageDraw.Draw(img)

        # Accent shape (big ellipse on right)
        accent = Image.new("RGBA", size, (0, 0, 0, 0))
        accent_draw = ImageDraw.Draw(accent)
        accent_draw.ellipse([size[0] - 450, -100, size[0] + 250, size[1] // 2 + 200], fill=(99, 102, 241, 90))  # blur-style shape
        img.paste(accent, (0, 0), accent)

        title_font, content_font = self.get_fonts(40, 26)

        # Truncate title if too long (limit to 80 characters)
        if len(title) > 80:
            title = title[:77] + "..."

        # Title - wrap like other templates
        title_lines = self.wrap_text(draw, title, title_font, size[0] - 160)
        y = 50  # Start title higher
        for line in title_lines[:2]:
            x = 80
            draw.text((x, y), line, font=title_font, fill='#FFFFFF')
            y += 55  # Reduced line spacing
        
        # Content - follow same pattern as other templates
        content_y = y + 40  # Reduced gap between title and content
        margin = 80
        for i, content_item in enumerate(contents):
            content_lines = self.wrap_text(draw, content_item, content_font, size[0] - margin*2 - 40)
            is_child_content = content_item.startswith('- ')
            for j, line in enumerate(content_lines):
                if content_y > size[1] - 80:
                    break
                x = margin
                if j == 0 and not is_child_content:
                    bullet_y_offset = 8
                    # Using a filled circle as bullet point
                    draw.ellipse([x-20, content_y + bullet_y_offset, x-10, content_y + bullet_y_offset + 10], fill='#3B82F6')
                    x += 30
                else:
                    x += 30
                draw.text((x, content_y), line, font=content_font, fill='#E2E8F0')
                content_y += 38
            content_y += 12

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'JPEG', quality=95)
        return output_path

class GeometricAccentTemplate(SlideTemplate):
    """Modern template with strong geometric accents."""
    
    def create(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        img = Image.new('RGB', size, color='#f0f2f5') # Light gray background
        draw = ImageDraw.Draw(img)
        
        # Large triangle accent in top-left
        draw.polygon([(0, 0), (size[0] // 3, 0), (0, size[1] // 3)], fill='#EF4444') # Red accent
        
        # Smaller square/rectangle accent in bottom-right
        draw.rectangle([size[0] - 150, size[1] - 150, size[0], size[1]], fill='#F59E0B') # Orange accent
        
        # Thin line at the bottom
        draw.rectangle([0, size[1]-10, size[0], size[1]], fill='#3B82F6') # Blue accent
        
        title_font, content_font = self.get_fonts(40, 26)
        
        # Truncate title if too long (limit to 80 characters)
        if len(title) > 80:
            title = title[:77] + "..."

        # Title (offset from accents)
        title_lines = self.wrap_text(draw, title, title_font, size[0] - 160)
        y = 80  # Start title higher
        for line in title_lines[:2]:
            x = 80
            draw.text((x, y), line, font=title_font, fill='#1F2937') # Very dark gray text
            y += 55  # Reduced line spacing
        
        # Content
        content_y = y + 40  # Reduced gap between title and content
        margin = 80
        for i, content_item in enumerate(contents):
            content_lines = self.wrap_text(draw, content_item, content_font, size[0] - margin*2 - 40)
            is_child_content = content_item.startswith('- ')
            for j, line in enumerate(content_lines[:2]):
                if content_y > size[1] - 80:
                    break
                x = margin
                if j == 0 and not is_child_content:
                    bullet_y_offset = 10 # Fine-tune
                    # Using a filled triangle as bullet point
                    draw.polygon([
                        (x-20, content_y + bullet_y_offset),
                        (x-10, content_y + bullet_y_offset + 5),
                        (x-20, content_y + bullet_y_offset + 10)
                    ], fill='#3B82F6')
                    x += 30
                else:
                    x += 30
                draw.text((x, content_y), line, font=content_font, fill='#4B5563') # Darker gray text
                content_y += 40
            content_y += 15


        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'JPEG', quality=95)
        return output_path


class NatureGreenTemplate(SlideTemplate):
    """Calm and earthy template with green and brown tones."""
    
    def create(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        img = Image.new('RGB', size, color='#F0FDF4') # Very light green background
        draw = ImageDraw.Draw(img)
        
        # Gradient from green to brown at the bottom
        for y_grad in range(size[1] - 200, size[1]):
            alpha = (y_grad - (size[1] - 200)) / 200
            r = int(229 + alpha * (161 - 229)) # from #E5E7EB to #A16207
            g = int(231 + alpha * (98 - 231))
            b = int(235 + alpha * (7 - 235))
            draw.line([(0, y_grad), (size[0], y_grad)], fill=(r, g, b))

        # Leaf-like or organic shapes (simple ellipses/curves)
        draw.ellipse([size[0]-250, -50, size[0]+50, 150], fill='#10B981', outline=None) # Top right green
        draw.ellipse([-100, size[1]-200, 100, size[1]], fill='#059669', outline=None) # Bottom left darker green
        
        title_font, content_font = self.get_fonts(40, 26)
        
        # Truncate title if too long (limit to 80 characters)
        if len(title) > 80:
            title = title[:77] + "..."

        # Title
        title_lines = self.wrap_text(draw, title, title_font, size[0] - 160)
        y = 60  # Start title higher
        for line in title_lines[:2]:
            x = 80
            draw.text((x, y), line, font=title_font, fill='#22543D') # Dark forest green
            y += 55  # Reduced line spacing
        
        # Content
        content_y = y + 40  # Reduced gap between title and content
        margin = 80
        for i, content_item in enumerate(contents):
            content_lines = self.wrap_text(draw, content_item, content_font, size[0] - margin*2 - 40)
            is_child_content = content_item.startswith('- ')
            for j, line in enumerate(content_lines):
                if content_y > size[1] - 80:
                    break
                x = margin
                if j == 0 and not is_child_content:
                    bullet_y_offset = 10 # Fine-tune
                    # Using a subtle circle with a green fill
                    draw.ellipse([x-20, content_y + bullet_y_offset, x-10, content_y + bullet_y_offset + 10], fill='#059669')
                    x += 30
                else:
                    x += 30
                draw.text((x, content_y), line, font=content_font, fill='#4C7C54') # Medium green text
                content_y += 40
            content_y += 15

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'JPEG', quality=95)
        return output_path

class ModernQuestionSlideTemplate(SlideTemplate):
    """Modern question slide template with colorful accents and clean design"""
    
    def __init__(self, font_path_title=None, font_path_content=None):
        super().__init__()
        self.font_path_title = font_path_title
        self.font_path_content = font_path_content


    def create(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        """Create modern question slide with consistent signature"""
        img = Image.new('RGB', size, color='white')
        draw = ImageDraw.Draw(img)

        # Fonts
        title_font, content_font = self.get_fonts(30, 26)

        # Truncate title if too long (limit to 80 characters)
        if len(title) > 80:
            title = title[:77] + "..."
        
        # Wrap title text to multiple lines if needed - leave more space for decorative elements
        title_max_width = size[0] - 380  # Even more conservative width to avoid left circle
        title_lines = self.wrap_text(draw, title.upper(), title_font, title_max_width)
        
        # Calculate title positioning - start higher to accommodate multiple lines
        title_start_y = 35
        current_y = title_start_y
        
        # Draw title lines (limit to 2 lines max) - center with safe margins
        for i, line in enumerate(title_lines[:2]):
            title_w = draw.textlength(line, font=title_font)
            # Center with minimum margin of 190px from left to avoid left circle, 140px from right
            title_x = max(190, (size[0] - title_w) // 2)
            if title_x + title_w > size[0] - 140:  # If still too wide, adjust
                title_x = 190
            draw.text((title_x, current_y), line, font=title_font, fill='#000000')
            current_y += 35  # Line spacing for title
        
        # Adjust underline position based on number of title lines - also with safe margins
        underline_y = title_start_y + (len(title_lines[:2]) * 30) + 15
        draw.line([(190, underline_y), (size[0] - 140, underline_y)], fill='#000000', width=3)

        # Left circle accents
        draw.ellipse([40, 10, 170, 140], fill='#3B82F6')  # Blue circle
        draw.ellipse([60, 180, 110, 230], fill='#E57362')  # Red circle

        # Top-right "browser dots"
        draw.ellipse([size[0] - 120, 40, size[0] - 100, 60], fill='#FACC15')  # Yellow
        draw.ellipse([size[0] - 90, 40, size[0] - 70, 60], fill='#FB7185')    # Pink
        draw.ellipse([size[0] - 60, 40, size[0] - 40, 60], fill='#3B82F6')    # Blue

        # Content rendering - adjust start position based on title height
        x_text = 200
        y_text = max(100, underline_y + 30)  # Start content below title with proper spacing
        line_spacing = 8

        for item in contents:
            # Parse content - handle both "label: description" and plain text
            if ':' in item:
                label, desc = item.split(':', 1)
                label = label.strip() + ':'
                desc = desc.strip()
                full_text = f"{label} {desc}"
            else:
                full_text = item.strip()

            # Wrap text
            lines = self.wrap_text(draw, full_text, content_font, size[0] - x_text - 80)
            
            if lines:
                # Bullet point
                if not full_text.startswith('- '):
                    bullet_y = y_text + 8
                    draw.ellipse([x_text - 25, bullet_y, x_text - 10, bullet_y + 15], fill='#000000')

                indent_x = x_text + 20
                draw.text((indent_x, y_text), lines[0], font=content_font, fill='#000000')
                y_text += content_font.getbbox(lines[0])[3] - content_font.getbbox(lines[0])[1] + line_spacing

                for line in lines[1:]:
                    draw.text((indent_x, y_text), line, font=content_font, fill='#000000')
                    y_text += content_font.getbbox(line)[3] - content_font.getbbox(line)[1] + line_spacing

            y_text += 10  # Spacing between items

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'PNG', quality=95)
        return output_path

class SlideTemplateManager:
    """Manager for slide templates with smart selection"""
    
    def __init__(self):
        self.templates = {
            'modern_blue': ModernBlueTemplate(),
            'minimal_green': MinimalGreenTemplate(),
            'dark_mode': DarkModeTemplate(),
            'creative_orange': CreativeOrangeTemplate(),
            'clean_white': CleanWhiteTemplate(),
            'blue_accent': BlueAccentTemplate(),
            'geometric_accent': GeometricAccentTemplate(),
            'nature_green': NatureGreenTemplate(),
            'modern_question_slide': ModernQuestionSlideTemplate(),
        }
        self.current_template = 'modern_blue'
        self.user_choice_template = None
        self.slide_counter = 0
    
    def set_template(self, template_name: str):
        """Set the current template"""
        if template_name in self.templates:
            self.current_template = template_name
            logger.info(f"Template set to: {template_name}")
        else:
            logger.warning(f"Template '{template_name}' not found. Available: {list(self.templates.keys())}")
    
    def set_user_choice_template(self, template_name: str):
        """Set user choice template for first slide"""
        if template_name in self.templates:
            self.user_choice_template = template_name
            self.current_template = template_name
            self.slide_counter = 0
            logger.info(f"User choice template set to: {template_name}")
        else:
            logger.warning(f"Template '{template_name}' not found. Available: {list(self.templates.keys())}")
    
    def auto_select_template(self):
        """Auto select template: first slide = user choice (or default), others = random"""
        if self.slide_counter == 0:
            # Slide đầu tiên: dùng user choice hoặc mặc định
            if self.user_choice_template:
                self.current_template = self.user_choice_template
                logger.info(f"First slide using user choice: {self.current_template}")
            else:
                logger.info(f"First slide using default: {self.current_template}")
        else:
            # Các slide sau: chọn random (khác template hiện tại)
            available = [t for t in self.templates.keys() if t != self.current_template]
            if available:
                old_template = self.current_template
                self.current_template = random.choice(available)
                logger.info(f"Slide {self.slide_counter + 1}: {old_template} → {self.current_template}")
        
        self.slide_counter += 1
        return self.current_template
    
    def reset_slide_counter(self):
        """Reset counter when starting new video"""
        self.slide_counter = 0
        logger.info("Slide counter reset")
    
    def create_content_image(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720), auto_select: bool = False) -> str:
        """Create content image using current template"""
        if auto_select:
            self.auto_select_template()
        
        template = self.templates[self.current_template]
        return template.create(title, contents, output_path, size)
    
    def create_content_image_with_template(self, template_name: str, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        """Create content image with specific template"""
        if template_name not in self.templates:
            logger.warning(f"Template '{template_name}' not found, using current template")
            template_name = self.current_template
        
        template = self.templates[template_name]
        return template.create(title, contents, output_path, size)
    
    def get_available_templates(self) -> Dict[str, str]:
        """Get list of available templates with descriptions"""
        return {
            'modern_blue': 'Modern Blue - Professional blue gradient with clean typography',
            'minimal_green': 'Minimal Green - Clean white background with green accents',
            'dark_mode': 'Dark Mode - Modern dark theme with purple accents',
            'creative_orange': 'Creative Orange - Vibrant orange with creative shapes',
            'clean_white': 'Clean White - Professional white with subtle accents',
            'blue_accent': 'Blue Accent - Navy background with blue accents',
            'geometric_accent': 'Geometric Accent - Strong geometric shapes with bold colors',
            'nature_green': 'Nature Green - Earthy tones with organic shapes',
            'modern_question_slide': 'Modern Question Slide - Interactive question slide with icons',
        }
    
    def cycle_template(self):
        """Manually cycle to next template (for testing/preview)"""
        template_names = list(self.templates.keys())
        current_index = template_names.index(self.current_template)
        next_index = (current_index + 1) % len(template_names)
        self.current_template = template_names[next_index]
        logger.info(f"Template manually cycled to: {self.current_template}")
        return self.current_template
    
    def get_template_info(self):
        """Get current template status"""
        return {
            'current_template': self.current_template,
            'user_choice_template': self.user_choice_template,
            'slide_counter': self.slide_counter,
            'total_templates': len(self.templates)
        }

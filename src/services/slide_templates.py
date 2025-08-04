"""
Slide Templates for beautiful video generation
"""
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont
import os
import random
from src.utils.logger import logger

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

        # Subtle pattern background
        for x in range(0, size[0], 60):
            for y in range(0, size[1], 60):
                draw.rectangle([x, y, x + 1, y + 1], fill='#e2e8f0')

        # Header band - increase height
        header_height = 120
        draw.rectangle([0, 0, size[0], header_height], fill='#059669')

        # # Side accent bar
        # draw.rectangle([0, header_height, 8, size[1]], fill='#10b981')

        title_font, content_font = self.get_fonts(40, 26)

        # Draw title - center vertically within header
        title_lines = self.wrap_text(draw, title, title_font, size[0] - 60)
        total_title_height = len(title_lines[:2]) * 50
        y = (header_height - total_title_height) // 2

        for line in title_lines[:2]:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            x = (size[0] - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, font=title_font, fill='#ffffff')
            y += 50

        # Content starts after header
        content_y = header_height + 40
        margin = 50
        for i, content_item in enumerate(contents):
            content_lines = self.wrap_text(draw, content_item, content_font, size[0] - margin * 2 - 50)
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
    """Modern, clean template with green tones — no font size change."""

    def create(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        img = Image.new('RGB', size, color='#F0FDF4')  # Gentle mint background
        draw = ImageDraw.Draw(img)

        # Subtle decoration — remove gradient, keep soft ellipses
        draw.ellipse([size[0] - 220, -100, size[0] + 100, 160], fill='#A7F3D0')  # Top-right soft green
        draw.ellipse([-120, size[1] - 220, 100, size[1] + 40], fill='#6EE7B7')   # Bottom-left green

        # Get fonts (keep sizes as before)
        title_font, content_font = self.get_fonts(40, 26)

        # Truncate overly long title
        if len(title) > 80:
            title = title[:77] + "..."

        # Title rendering
        title_lines = self.wrap_text(draw, title, title_font, size[0] - 160)
        y = 60
        for line in title_lines[:2]:  # Max 2 lines for title
            draw.text((80, y), line, font=title_font, fill='#064E3B')  # Deep green
            y += 55

        # Content rendering
        content_y = y + 35
        margin = 80
        bullet_color = '#10B981'  # Emerald green

        for content_item in contents:
            content_lines = self.wrap_text(draw, content_item, content_font, size[0] - margin * 2 - 40)
            is_child_content = content_item.strip().startswith('- ')

            for j, line in enumerate(content_lines):
                if content_y > size[1] - 70:
                    break

                x = margin + (30 if is_child_content else 0)

                if j == 0 and not is_child_content:
                    # Modern bullet point
                    draw.text((x - 25, content_y), "●", font=content_font, fill=bullet_color)

                draw.text((x, content_y), line, font=content_font, fill='#065F46')  # Slightly darker green
                content_y += 40

            content_y += 15  # Space between content items

        # Save image
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'JPEG', quality=95)
        return output_path


class ModernQuestionSlideTemplate(SlideTemplate):
    """Modern, professional question slide with clean layout and consistent style."""

    def create(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        img = Image.new('RGB', size, color='white')
        draw = ImageDraw.Draw(img)

        # Fonts
        title_font, content_font = self.get_fonts(30, 26)

        # Layout constants
        margin_left = 100
        margin_right = 100
        max_title_width = size[0] - margin_left - margin_right

        # --- DESIGN: Left accent bar
        accent_bar_width = 6
        draw.rectangle([60, 60, 60 + accent_bar_width, size[1] - 60], fill='#3B82F6')

        # --- Title
        if len(title) > 80:
            title = title[:77] + "..."
        title_lines = self.wrap_text(draw, title.upper(), title_font, max_title_width)
        y = 60
        for line in title_lines[:2]:
            draw.text((margin_left, y), line, font=title_font, fill='#1F2937')  # Gray-800
            y += 40

        # --- Underline
        underline_y = y + 10
        draw.line([(margin_left, underline_y), (size[0] - margin_right, underline_y)], fill='#D1D5DB', width=2)

        # --- Content rendering
        y_text = underline_y + 30
        line_spacing = 10
        bullet_color = '#3B82F6'

        for content_item in contents:
            is_child_content = content_item.strip().startswith('- ')
            raw_text = content_item.strip()

            wrap_width = size[0] - margin_left - margin_right - (40 if is_child_content else 0)
            content_lines = self.wrap_text(draw, raw_text, content_font, wrap_width)

            if content_lines:
                text_x = margin_left + (20 if is_child_content else 0)

                if not is_child_content:
                    # Draw dot for main item
                    draw.text((margin_left - 25, y_text), "●", font=content_font, fill=bullet_color)
                    
                # Draw first line
                draw.text((text_x, y_text), content_lines[0], font=content_font, fill='#111827')
                y_text += content_font.getbbox(content_lines[0])[3] - content_font.getbbox(content_lines[0])[1] + line_spacing

                # Draw remaining lines (indented)
                for line in content_lines[1:]:
                    draw.text((text_x, y_text), line, font=content_font, fill='#374151')
                    y_text += content_font.getbbox(line)[3] - content_font.getbbox(line)[1] + line_spacing

            y_text += 15  # Extra spacing

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'PNG', quality=95)
        return output_path

class ElegantCardTemplate(SlideTemplate):
    """Modern elegant slide with card-style layout and professional color palette"""

    def create(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        img = Image.new('RGB', size, color='#334155') # Light warm gray background
        draw = ImageDraw.Draw(img)

        width, height = size
        margin_x = 80
        title_font, content_font = self.get_fonts(40, 26)

        # === HEADER TITLE ===
        if len(title) > 80:
            title = title[:77] + "..."
        title_y = 50
        title_lines = self.wrap_text(draw, title, title_font, width - 2 * margin_x)
        for line in title_lines[:2]:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            x = (width - (bbox[2] - bbox[0])) // 2
            draw.text((x, title_y), line, font=title_font, fill='#111827')
            title_y += 50

        # === SEPARATOR LINE ===
        separator_y = title_y + 10
        draw.line([margin_x, separator_y, width - margin_x, separator_y], fill='#047857', width=4)

        # === CONTENT CARD ===
        card_margin_top = separator_y + 30
        card_padding = 40
        card_x1 = margin_x
        card_x2 = width - margin_x
        card_y1 = card_margin_top
        card_y2 = height - 60

        # Shadow card (fake shadow with slightly offset gray box)
        shadow_offset = 6
        draw.rounded_rectangle(
            [card_x1 + shadow_offset, card_y1 + shadow_offset, card_x2 + shadow_offset, card_y2 + shadow_offset],
            radius=20,
            fill='#d1d5db'  # Gray shadow
        )
        # Main white card
        draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=20, fill='white')

        # === DRAW CONTENT ===
        content_x = card_x1 + card_padding
        content_y = card_y1 + card_padding
        max_text_width = card_x2 - card_x1 - 2 * card_padding
        line_spacing = 40
        bullet_radius = 5

        # Auto spacing shrink if content too long
        total_lines = sum(len(self.wrap_text(draw, item, content_font, max_text_width)) for item in contents)
        available_height = card_y2 - content_y - 30
        estimated_height = total_lines * line_spacing
        if estimated_height > available_height:
            line_spacing = max(28, line_spacing - 4)

        for item in contents:
            lines = self.wrap_text(draw, item, content_font, max_text_width)
            for i, line in enumerate(lines):
                if content_y > card_y2 - 30:
                    break
                # Bullet
                if i == 0:
                    bx = content_x - 20
                    by = content_y + 10
                    draw.ellipse([bx, by, bx + bullet_radius*2, by + bullet_radius*2], fill='#047857')
                draw.text((content_x, content_y), line, font=content_font, fill='#374151')
                content_y += line_spacing
            content_y += 10

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'PNG', quality=95)
        return output_path

class ModernEduTemplate(SlideTemplate):
    """Modern, clean education slide template"""

    def create(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        img = Image.new('RGB', size, color='#f1f5f9')  # Soft light blue-gray
        draw = ImageDraw.Draw(img)

        # Header bar
        header_height = 110
        draw.rectangle([0, 0, size[0], header_height], fill='#1e3a8a')  # Navy blue

        title_font, content_font = self.get_fonts(40, 26)

        # Title (max 2 lines, centered)
        title_lines = self.wrap_text(draw, title, title_font, size[0] - 80)
        total_title_height = len(title_lines[:2]) * 50
        y = (header_height - total_title_height) // 2
        for line in title_lines[:2]:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            x = (size[0] - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, font=title_font, fill='white')
            y += 50

        # Content
        content_y = header_height + 40
        margin = 60
        line_spacing = 42

        for content_item in contents:
            content_lines = self.wrap_text(draw, content_item, content_font, size[0] - margin * 2 - 40)
            is_child_content = content_item.startswith('- ')

            for j, line in enumerate(content_lines):
                if content_y > size[1] - 60:
                    break
                x = margin
                if j == 0 and not is_child_content:
                    draw.text((x, content_y), "→", font=content_font, fill='#3b82f6')
                    x += 40
                else:
                    x += 40
                draw.text((x, content_y), line, font=content_font, fill='#1f2937')  # Slate text
                content_y += line_spacing
            content_y += 10

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'PNG', quality=95)
        return output_path
    
class FocusBlockEducationTemplate(SlideTemplate):
    """Split-style professional slide with a colored block for title"""

    def create(self, title: str, contents: List[str], output_path: str, size: tuple = (1280, 720)) -> str:
        width, height = size
        img = Image.new('RGB', size, color='#ffffff')  # White background
        draw = ImageDraw.Draw(img)

        # Left block background
        block_width = 380
        draw.rectangle([0, 0, block_width, height], fill='#004d40')  # Dark teal

        # Fonts
        title_font, content_font = self.get_fonts(38, 26)

        # Draw title in block
        if len(title) > 160:
            title = title[:157] + "..."
        title_lines = self.wrap_text(draw, title, title_font, block_width - 60)
        y = 100
        for line in title_lines:
            draw.text((40, y), line, font=title_font, fill='#ffffff')
            y += 44

        # Optional: Add visual icon
        # draw.ellipse((block_width - 80, height - 80, block_width - 20, height - 20), fill='#80cbc4')

        # Right content block
        margin_x = block_width + 40
        content_y = 80
        spacing = 40

        for content in contents:
            lines = self.wrap_text(draw, content, content_font, width - margin_x - 60)
            is_sub = content.startswith('- ')
            for idx, line in enumerate(lines):
                x = margin_x + (30 if is_sub else 0)
                bullet = "•" if idx == 0 and not is_sub else ""
                draw.text((x, content_y), f"{bullet} {line}".strip(), font=content_font, fill='#263238')
                content_y += spacing
            content_y += 10

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, "PNG", quality=95)
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
            'elegant_card': ElegantCardTemplate(),
            'modern_edu': ModernEduTemplate(),
            'soft_modern_edu': FocusBlockEducationTemplate(),
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
            'elegant_card': 'Elegant Card - Modern card-style layout with elegant design',
            'modern_edu': 'Modern Education - Clean education slide with blue header',
            'soft_modern_edu': 'Soft Modern Education - Soft modern design with gentle colors',
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

import asyncio
import os
import gc
import time
import platform
import requests
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from google.cloud import texttospeech
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, VideoFileClip, AudioClip
from PIL import Image, ImageDraw, ImageFont
import tempfile
import logging
from contextlib import contextmanager
import shutil

logger = logging.getLogger(__name__)

class VideoGenerator:
    def __init__(self, unsplash_access_key: str = None, voice_config: Dict[str, Any] = None):
        # Initialize Google Cloud TTS client (credentials from environment)
        self.tts_client = texttospeech.TextToSpeechClient()
        
        # Get Unsplash key from environment if not provided
        self.unsplash_access_key = unsplash_access_key or os.getenv('UNSPLASH_ACCESS_KEY')
        
        # Set voice configuration
        if voice_config:
            self.voice = texttospeech.VoiceSelectionParams(
                language_code=voice_config.get('language_code', 'vi-VN'),
                name=voice_config.get('name', 'vi-VN-Wavenet-D'),
            )
        else:
            # Default voice
            self.voice = texttospeech.VoiceSelectionParams(
                language_code="vi-VN",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
        
        # Audio configuration
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=voice_config.get('speaking_rate', 1.0) if voice_config else 1.0
        )
        
        # Platform-specific settings
        self.is_windows = platform.system() == "Windows"
        self.cleanup_delay = 0.5 if self.is_windows else 0.1  # Longer delay on Windows

    @contextmanager
    def _safe_moviepy_context(self):
        """Context manager for safe MoviePy operations with proper cleanup"""
        clips_to_cleanup = []
        try:
            yield clips_to_cleanup
        finally:
            # Explicit cleanup
            for clip in clips_to_cleanup:
                try:
                    if hasattr(clip, 'close'):
                        clip.close()
                except Exception as e:
                    logger.warning(f"Error closing clip: {e}")
            
            # Force garbage collection
            gc.collect()
            
            # Additional delay on Windows for file handle release
            if self.is_windows:
                time.sleep(self.cleanup_delay)

    def _safe_file_operation(self, operation, *args, max_retries=3, **kwargs):
        """Safely perform file operations with retry logic for Windows"""
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except (PermissionError, OSError) as e:
                if attempt < max_retries - 1:
                    logger.warning(f"File operation failed (attempt {attempt + 1}), retrying in {self.cleanup_delay}s: {e}")
                    time.sleep(self.cleanup_delay * (attempt + 1))  # Exponential backoff
                    gc.collect()
                else:
                    logger.error(f"File operation failed after {max_retries} attempts: {e}")
                    raise

    async def generate_lesson_video(self, lesson_data: Dict[str, Any], output_path: str) -> str:
        """Generate complete video from lesson JSON data"""
        try:
            slides = lesson_data.get('slides', [])
            if not slides:
                raise ValueError("No slides found in lesson data")

            # Create temporary directory for intermediate files
            with tempfile.TemporaryDirectory() as temp_dir:
                logger.info(f"Processing {len(slides)} slides...")
                
                # Process all slides concurrently
                slide_video_paths = await self._process_slides_concurrent(slides, temp_dir)
                
                # Combine all slide videos
                final_video_path = await self._combine_videos(slide_video_paths, output_path)
                
                logger.info(f"Video generation completed: {final_video_path}")
                return final_video_path
                
        except Exception as e:
            logger.error(f"Error generating lesson video: {e}")
            raise

    async def _process_slides_concurrent(self, slides: List[Dict], temp_dir: str) -> List[str]:
        """Process all slides concurrently"""
        with ThreadPoolExecutor(max_workers=4) as executor:
            loop = asyncio.get_event_loop()
            
            # Create tasks for all slides
            tasks = []
            for i, slide in enumerate(slides):
                task = loop.run_in_executor(
                    executor,
                    self._process_single_slide, 
                    slide, 
                    i, 
                    temp_dir
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            slide_video_paths = await asyncio.gather(*tasks)
            
            # Sort by slide order
            return [path for path in slide_video_paths if path]

    def _process_single_slide(self, slide: Dict, slide_index: int, temp_dir: str) -> str:
        """Process a single slide: get image, generate TTS, create video"""
        try:
            slide_id = slide.get('slide_id', slide_index + 1)
            logger.info(f"Processing slide {slide_id}...")
            
            # Generate audio from TTS
            audio_path = self._generate_tts_audio(
                slide.get('tts_script', ''), 
                os.path.join(temp_dir, f"audio_{slide_id}.mp3")
            )
            
            # Get or create image
            image_path = self._get_slide_image(
                slide.get('image_keywords', []),
                slide.get('title', ''),
                os.path.join(temp_dir, f"image_{slide_id}.jpg")
            )
            
            # Create video for this slide
            video_path = os.path.join(temp_dir, f"slide_{slide_id}.mp4")
            self._create_slide_video(image_path, audio_path, video_path)
            
            logger.info(f"Slide {slide_id} processed successfully")
            return video_path
            
        except Exception as e:
            logger.error(f"Error processing slide {slide_index + 1}: {e}")
            return None

    def _generate_tts_audio(self, text: str, output_path: str) -> str:
        """Generate audio using Google Cloud TTS"""
        if not text.strip():
            # Create silent audio for empty text
            return self._create_silent_audio(output_path, duration=2.0)
        
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=self.voice,
                audio_config=self.audio_config
            )
            
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
            
            logger.debug(f"TTS audio generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating TTS audio: {e}")
            # Fallback to silent audio
            return self._create_silent_audio(output_path, duration=3.0)

    def _get_slide_image(self, keywords: List[str], title: str, output_path: str) -> str:
        """Get image from Unsplash or create placeholder"""
        # Try to get image from Unsplash if access key is available
        if self.unsplash_access_key and keywords:
            image_url = self._search_unsplash_image(keywords[0])
            if image_url:
                if self._download_image(image_url, output_path):
                    return output_path
        
        # Fallback: create placeholder image
        return self._create_placeholder_image(title, keywords, output_path)

    def _search_unsplash_image(self, keyword: str) -> str:
        """Search for image on Unsplash"""
        try:
            url = f"https://api.unsplash.com/search/photos"
            params = {
                'query': keyword,
                'client_id': self.unsplash_access_key,
                'orientation': 'landscape',
                'per_page': 1,
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    return data['results'][0]['urls']['regular']
                else:
                    logger.warning("No results found on Unsplash")
                
        except Exception as e:
            logger.warning(f"Error searching Unsplash: {e}")
        
        return None

    def _download_image(self, url: str, output_path: str) -> bool:
        """Download image from URL"""
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            logger.warning(f"Error downloading image: {e}")
        
        return False

    def _create_placeholder_image(self, title: str, keywords: List[str], output_path: str) -> str:
        """Create a placeholder image with title and keywords"""
        # Create a 1920x1080 image
        img = Image.new('RGB', (1920, 1080), color='#f0f4f8')
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to use a system font based on platform
            if self.is_windows:
                title_font = ImageFont.truetype("arial.ttf", 72)
                keyword_font = ImageFont.truetype("arial.ttf", 36)
            else:
                # Linux/Mac font paths
                for font_path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 
                                "/System/Library/Fonts/Arial.ttf",
                                "/usr/share/fonts/TTF/arial.ttf"]:
                    try:
                        title_font = ImageFont.truetype(font_path, 72)
                        keyword_font = ImageFont.truetype(font_path, 36)
                        break
                    except:
                        continue
                else:
                    raise OSError("No suitable font found")
        except:
            # Fallback to default font
            title_font = ImageFont.load_default()
            keyword_font = ImageFont.load_default()
        
        # Draw title
        title_text = title[:50] + "..." if len(title) > 50 else title
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (1920 - title_width) // 2
        draw.text((title_x, 400), title_text, fill='#2d3748', font=title_font)
        
        # Draw keywords
        if keywords:
            keywords_text = " • ".join(keywords[:5])
            keywords_bbox = draw.textbbox((0, 0), keywords_text, font=keyword_font)
            keywords_width = keywords_bbox[2] - keywords_bbox[0]
            keywords_x = (1920 - keywords_width) // 2
            draw.text((keywords_x, 600), keywords_text, fill='#4a5568', font=keyword_font)
        
        img.save(output_path, 'JPEG', quality=85)
        logger.debug(f"Placeholder image created: {output_path}")
        return output_path

    def _create_slide_video(self, image_path: str, audio_path: str, output_path: str):
        """Create video from image and audio with proper cleanup"""
        with self._safe_moviepy_context() as clips:
            try:
                # Load audio to get duration
                audio_clip = AudioFileClip(audio_path)
                clips.append(audio_clip)
                duration = audio_clip.duration
                  # Create image clip with audio duration
                image_clip = ImageClip(image_path).set_duration(duration)
                clips.append(image_clip)
                
                # Combine image and audio
                final_clip = image_clip.set_audio(audio_clip)
                clips.append(final_clip)

                logger.info(f"Creating video for slide: {image_path} with audio: {audio_path}")
                
                # Write video file with safe operation
                self._safe_file_operation(
                    final_clip.write_videofile,
                    output_path,
                    fps=24,
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                
            except Exception as e:
                logger.error(f"Error creating slide video: {e}")
                raise

    async def _combine_videos(self, video_paths: List[str], output_path: str) -> str:
        """Combine all slide videos into final video with proper cleanup"""
        try:
            if not video_paths:
                raise ValueError("No video files to combine")
            
            # Validate video files exist
            valid_paths = [path for path in video_paths if os.path.exists(path)]
            if not valid_paths:
                raise ValueError("No valid video clips found")
            
            with self._safe_moviepy_context() as clips:
                # Load all video clips
                for path in valid_paths:
                    clip = VideoFileClip(path)
                    clips.append(clip)
                
                if not clips:
                    raise ValueError("No clips loaded successfully")
                  # Concatenate all clips
                final_video = concatenate_videoclips(clips, method="compose")
                clips.append(final_video)
                
                # Create temporary output path to avoid conflicts
                temp_output = output_path.replace('.mp4', '_temp.mp4')
                
                # Write final video with safe operation  
                self._safe_file_operation(
                    final_video.write_videofile,
                    temp_output,
                    fps=24,
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )
                
                # Force cleanup before moving file
                clips.clear()
                gc.collect()
                time.sleep(self.cleanup_delay)
                
                # Move temp file to final location
                self._safe_file_operation(shutil.move, temp_output, output_path)
                
                logger.info(f"Final video saved: {output_path}")
                return output_path
        except Exception as e:
            logger.error(f"Error combining videos: {e}")
            # Clean up temp file if it exists
            temp_output = output_path.replace('.mp4', '_temp.mp4')
            if os.path.exists(temp_output):
                try:
                    os.remove(temp_output)
                except:
                    pass
            raise

    def _create_silent_audio(self, output_path: str, duration: float) -> str:
        """Create silent audio file with proper cleanup"""
        with self._safe_moviepy_context() as clips:
            try:
                def make_frame(t):
                    return [0, 0]  # Stereo silence
                
                audio_clip = AudioClip(make_frame, duration=duration)
                clips.append(audio_clip)
                
                self._safe_file_operation(
                    audio_clip.write_audiofile,
                    output_path,
                    verbose=False,
                    logger=None
                )
                
                return output_path
                
            except Exception as e:
                logger.error(f"Error creating silent audio: {e}")
                raise

    @staticmethod
    def get_available_voices(language_code: str = None) -> List[Dict[str, Any]]:
        """Get available voices from Google Cloud TTS"""
        try:
            client = texttospeech.TextToSpeechClient()
            voices = client.list_voices(language_code=language_code)
            
            voice_list = []
            for voice in voices.voices:
                for lang_code in voice.language_codes:
                    if not language_code or lang_code.startswith(language_code):
                        voice_info = {
                            "name": voice.name,
                            "language_code": lang_code,
                            "gender": voice.ssml_gender.name,
                            "natural_sample_rate": voice.natural_sample_rate_hertz
                        }
                        voice_list.append(voice_info)
            
            return voice_list
            
        except Exception as e:
            logger.error(f"Error getting available voices: {e}")
            return []
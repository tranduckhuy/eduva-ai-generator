import asyncio
import os
import gc
import time
import platform
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from google.cloud import texttospeech
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, VideoFileClip, AudioClip
import tempfile
import logging
from contextlib import contextmanager
import shutil

# Import our new helper modules
from .image_generator import ImageGenerator
from .content_formatter import ContentFormatter
from .slide_processor import SlideProcessor

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
        
        # Audio configuration - OPTIMIZED
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=voice_config.get('speaking_rate', 1.1) if voice_config else 1.1,  # Faster speaking
            sample_rate_hertz=22050  # Lower sample rate for smaller files and faster processing
        )
        
        # Platform-specific settings - OPTIMIZED
        self.is_windows = platform.system() == "Windows"
        self.cleanup_delay = 0.5 if self.is_windows else 0.1  # Reduced cleanup delay
        
        # Performance optimizations
        self.max_workers_optimized = min(3, os.cpu_count())  # Increased concurrency
        self.batch_size_optimized = 3  # Larger batches
        self.video_fps = 20  # Reduced FPS for faster processing
        self.image_resolution = (1280, 720)  # Standard HD
        
        # Initialize helper classes
        self.slide_processor = SlideProcessor(self.unsplash_access_key)
        self.content_formatter = ContentFormatter()

    @contextmanager
    def _safe_moviepy_context(self):
        """Context manager for safe MoviePy operations with aggressive cleanup"""
        clips_to_cleanup = []
        try:
            yield clips_to_cleanup
        finally:
            # Aggressive cleanup
            for clip in clips_to_cleanup:
                try:
                    if hasattr(clip, 'close'):
                        clip.close()
                    if hasattr(clip, 'reader') and clip.reader:
                        clip.reader.close()
                except Exception as e:
                    logger.warning(f"Error closing clip: {e}")
            
            # Clear the list
            clips_to_cleanup.clear()
            
            # Force garbage collection multiple times - OPTIMIZED
            for _ in range(2):
                gc.collect()
            
            # Reduced delay on Windows for file handle release
            if self.is_windows:
                time.sleep(0.2)

    def _safe_file_operation(self, operation, *args, **kwargs):
        """Safely perform file operations with retry logic for Windows"""
        max_retries = kwargs.pop('max_retries', 3)
        
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except (PermissionError, OSError, FileNotFoundError) as e:
                if attempt < max_retries - 1:
                    delay = 0.5 * (attempt + 1)
                    logger.warning(f"File operation failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    time.sleep(delay)
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
            
            # Validate and normalize output path - ensure it's a proper Windows path
            output_path = os.path.normpath(os.path.abspath(output_path))
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Use system TEMP directory - tránh path quá dài
            temp_dir = tempfile.mkdtemp(prefix='vgen_')
            
            try:
                logger.info(f"Processing {len(slides)} slides...")
                logger.info(f"Using temporary directory: {temp_dir}")
                logger.info(f"Output path: {output_path}")
                
                # Process all slides concurrently with reduced concurrency for stability
                slide_video_paths = await self._process_slides_concurrent(slides, temp_dir)
                
                # Filter out None values (failed slides)
                valid_paths = [path for path in slide_video_paths if path and os.path.exists(path)]
                if not valid_paths:
                    raise ValueError("No slide videos were successfully created")
                
                logger.info(f"Successfully created {len(valid_paths)} out of {len(slides)} slide videos")
                
                # Combine all slide videos
                final_video_path = await self._combine_videos(valid_paths, output_path)
                
                logger.info(f"Video generation completed: {final_video_path}")
                return final_video_path
            finally:
                # Clean up temp directory
                try:
                    if os.path.exists(temp_dir):
                        time.sleep(1.0)  
                        shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    logger.warning(f"Could not clean up temp directory: {e}")
                    
        except Exception as e:
            logger.error(f"Error generating lesson video: {e}")
            raise

    async def _process_slides_concurrent(self, slides: List[Dict], temp_dir: str) -> List[str]:
        """Process slides with optimized memory usage and improved concurrency"""
        # OPTIMIZED: Increased concurrency and larger batches
        max_workers = self.max_workers_optimized
        batch_size = self.batch_size_optimized
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            loop = asyncio.get_event_loop()
            
            # Process in optimized batches
            all_valid_paths = []
            
            for i in range(0, len(slides), batch_size):
                batch = slides[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}: slides {i+1}-{min(i+batch_size, len(slides))}")
                
                # Create tasks for current batch
                tasks = []
                for j, slide in enumerate(batch):
                    task = loop.run_in_executor(
                        executor,
                        self._process_single_slide, 
                        slide, 
                        i + j, 
                        temp_dir
                    )
                    tasks.append(task)
                
                # Wait for batch to complete - OPTIMIZED timeout
                try:
                    batch_results = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True), 
                        timeout=120
                    )
                    
                    # Process batch results
                    for result in batch_results:
                        if isinstance(result, Exception):
                            logger.error(f"Slide processing error: {result}")
                        elif result:
                            all_valid_paths.append(result)
                    
                    # OPTIMIZED: Minimal cleanup between batches
                    gc.collect()
                    time.sleep(0.2)
                    
                except asyncio.TimeoutError:
                    logger.error(f"Batch {i//batch_size + 1} processing timed out")
                    for task in tasks:
                        task.cancel()
            
            return all_valid_paths

    def _process_single_slide(self, slide: Dict, slide_index: int, temp_dir: str) -> str:
        """Process a single slide: get images, generate TTS, create video"""
        try:
            slide_id = slide.get('slide_id', slide_index + 1)
            logger.info(f"Processing slide {slide_id}...")
            
            # Ensure temp_dir exists and is properly formatted for Windows
            temp_dir = os.path.normpath(temp_dir)
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate audio from TTS with proper path handling
            audio_filename = f"audio_{slide_id}.mp3"
            audio_path = os.path.normpath(os.path.join(temp_dir, audio_filename))
            
            audio_path = self._generate_tts_audio(
                slide.get('tts_script', ''), 
                audio_path
            )
            
            # Get audio duration with proper cleanup
            audio_duration = 5.0  # Default fallback
            try:
                with self._safe_moviepy_context() as clips:
                    audio_clip = AudioFileClip(audio_path)
                    clips.append(audio_clip)
                    audio_duration = audio_clip.duration
            except Exception as e:
                logger.warning(f"Could not get audio duration for slide {slide_id}: {e}")
            
            # Optional cleanup between operations
            gc.collect()
            
            # Process slide images using the optimized approach
            slide_result = self.slide_processor.process_slide_images(
                slide, temp_dir, slide_id, self.image_resolution
            )
            
            # Calculate optimal timing for images based on audio duration
            slide_result = self.slide_processor.calculate_slide_timing(slide_result, audio_duration)
            
            # Another cleanup before video creation
            gc.collect()
            
            # Create video for this slide with proper path handling
            video_filename = f"slide_{slide_id}.mp4"
            video_path = os.path.normpath(os.path.join(temp_dir, video_filename))
            
            self._create_slide_video_with_timing(slide_result, audio_path, video_path)
            
            # Final cleanup
            gc.collect()
            
            # Verify the video file was created
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file was not created: {video_path}")
            
            logger.info(f"Slide {slide_id} processed successfully: {video_path}")
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
            # Validate and normalize the output path for Windows
            output_path = os.path.normpath(os.path.abspath(output_path))
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=self.voice,
                audio_config=self.audio_config
            )
            
            # Use safe file operation for writing
            with open(output_path, "wb") as out:
                out.write(response.audio_content)
            
            # Verify file was created
            if not os.path.exists(output_path):
                raise FileNotFoundError(f"TTS audio file was not created: {output_path}")
                
            logger.debug(f"TTS audio generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating TTS audio: {e}")
            # Fallback to silent audio
            return self._create_silent_audio(output_path, duration=3.0)

    def _create_slide_video_with_timing(self, slide_result: Dict[str, Any], audio_path: str, output_path: str):
        """Create video from slide result with proper timing"""
        # Validate and normalize paths for Windows
        output_path = os.path.normpath(os.path.abspath(output_path))
        audio_path = os.path.normpath(os.path.abspath(audio_path))
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with self._safe_moviepy_context() as clips:
            try:
                # Load audio
                audio_clip = AudioFileClip(audio_path)
                clips.append(audio_clip)
                total_duration = audio_clip.duration
                
                images = slide_result['images']
                if not images:
                    raise ValueError("No images provided for video creation")
                
                # Create image clips with calculated durations
                image_clips = []
                
                for img_info in images:
                    image_path = os.path.normpath(os.path.abspath(img_info['path']))
                    duration = img_info['duration']
                    
                    # Verify image file exists
                    if not os.path.exists(image_path):
                        logger.warning(f"Image file not found: {image_path}")
                        continue
                    
                    # Create image clip with error handling - NO timing, just duration
                    try:
                        image_clip = ImageClip(image_path).set_duration(duration)
                        image_clips.append(image_clip)
                        clips.append(image_clip)
                    except Exception as e:
                        logger.warning(f"Could not create image clip for {image_path}: {e}")
                        continue
                
                if not image_clips:
                    raise ValueError("No valid image clips could be created")
                
                # Create video by concatenating images instead of compositing
                if len(image_clips) == 1:
                    video_clip = image_clips[0]
                else:
                    # Concatenate images sequentially
                    video_clip = concatenate_videoclips(image_clips, method="compose")
                
                clips.append(video_clip)
                
                # Ensure video duration matches audio duration
                video_clip = video_clip.set_duration(total_duration)
                
                # Combine with audio
                final_clip = video_clip.set_audio(audio_clip)
                clips.append(final_clip)

                logger.info(f"Creating video with {len(image_clips)} images, total duration: {total_duration:.2f}s")
                
                # Write video file with enhanced error handling - OPTIMIZED
                try:
                    self._safe_file_operation(
                        final_clip.write_videofile,
                        output_path,
                        fps=self.video_fps,  # OPTIMIZED: Lower FPS
                        codec='libx264',
                        audio_codec='aac',
                        verbose=False,
                        logger=None,
                        preset='ultrafast',  # OPTIMIZED: Fastest encoding
                        ffmpeg_params=['-crf', '28'],  # OPTIMIZED: Higher compression for speed
                        temp_audiofile=None
                    )
                except Exception as e:
                    logger.error(f"Error writing video file: {e}")
                    raise
                
            except Exception as e:
                logger.error(f"Error creating slide video: {e}")
                raise

    async def _combine_videos(self, video_paths: List[str], output_path: str) -> str:
        """Combine all slide videos into final video with proper cleanup"""
        try:
            if not video_paths:
                raise ValueError("No video files to combine")
              # Validate video files exist and normalize paths
            valid_paths = []
            for path in video_paths:
                if path and os.path.exists(path):
                    valid_paths.append(os.path.abspath(path))
                else:
                    logger.warning(f"Video file not found: {path}")
            
            if not valid_paths:
                raise ValueError("No valid video clips found")
            
            # Validate and normalize output path
            output_path = os.path.abspath(output_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with self._safe_moviepy_context() as clips:
                # Load video clips one by one to avoid memory buildup
                video_clips = []
                for i, path in enumerate(valid_paths):
                    try:
                        logger.info(f"Loading video clip {i+1}/{len(valid_paths)}: {os.path.basename(path)}")
                        clip = VideoFileClip(path)
                        video_clips.append(clip)
                        clips.append(clip)
                        
                        # Force cleanup every few clips
                        if (i + 1) % 2 == 0:
                            gc.collect()
                            
                    except Exception as e:
                        logger.warning(f"Could not load video clip {path}: {e}")
                        continue
                
                if not video_clips:
                    raise ValueError("No clips loaded successfully")
                
                logger.info(f"Concatenating {len(video_clips)} video clips...")
                # Concatenate all clips - use simple method
                final_video = concatenate_videoclips(video_clips)
                clips.append(final_video)
                
                # DO NOT clear intermediate clips yet - keep them for final video
                
                # Create temporary output path to avoid conflicts with proper path handling
                temp_filename = f"{os.path.splitext(os.path.basename(output_path))[0]}_temp.mp4"
                temp_output = os.path.join(os.path.dirname(output_path), temp_filename)
                
                # Write final video with safe operation - OPTIMIZED
                self._safe_file_operation(
                    final_video.write_videofile,
                    temp_output,
                    fps=self.video_fps,  # OPTIMIZED: Lower FPS
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None,
                    preset='ultrafast',  # OPTIMIZED: Fastest encoding
                    threads=self.max_workers_optimized,  # OPTIMIZED: Use more threads
                    ffmpeg_params=['-crf', '28']  # OPTIMIZED: Higher compression for speed
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
            logger.error(f"Error combining videos: {e}")            # Clean up temp file if it exists
            try:
                temp_filename = f"{os.path.splitext(os.path.basename(output_path))[0]}_temp.mp4"
                temp_output = os.path.join(os.path.dirname(output_path), temp_filename)
                if os.path.exists(temp_output):
                    os.remove(temp_output)
            except Exception as cleanup_error:
                logger.warning(f"Could not clean up temp file: {cleanup_error}")
            raise

    def _create_silent_audio(self, output_path: str, duration: float) -> str:
        """Create silent audio file with proper cleanup"""
        # Validate and normalize the output path for Windows
        output_path = os.path.normpath(os.path.abspath(output_path))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
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
                
                # Verify file was created
                if not os.path.exists(output_path):
                    raise FileNotFoundError(f"Silent audio file was not created: {output_path}")
                
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
  
    
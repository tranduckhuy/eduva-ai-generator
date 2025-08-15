import asyncio
import os
import gc
import time
import uuid
import platform
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips
from moviepy.audio.AudioClip import AudioArrayClip
from moviepy.audio.fx.audio_fadeout import audio_fadeout
import numpy as np
from contextlib import contextmanager
import subprocess
# Import our new helper modules
from .content_formatter import ContentFormatter
from .slide_processor import SlideProcessor
from .tts_service import TTSService
from src.utils.logger import logger
from PIL import Image

if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

class VideoGenerator:
    def __init__(self, unsplash_access_key: str = None, voice_config: Dict[str, Any] = None, language: str = "vietnamese"):
        # Initialize TTS service
        self.tts_service = TTSService(voice_config)
        
        # Get Unsplash key from environment if not provided
        self.unsplash_access_key = unsplash_access_key or os.getenv('UNSPLASH_ACCESS_KEY')
        
        # Platform-specific settings - OPTIMIZED
        self.is_windows = platform.system() == "Windows"
        self.cleanup_delay = 0.5 if self.is_windows else 0.1
        
        # Performance optimizations
        self.max_workers_optimized = min(3, os.cpu_count())
        self.batch_size_optimized = 3
        self.video_fps = 10
        self.image_resolution = (1280, 720)
        
        # Initialize helper classes
        self.slide_processor = SlideProcessor(self.unsplash_access_key)
        self.content_formatter = ContentFormatter()

        self.language = language

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

    async def generate_lesson_video(self, lesson_data: Dict[str, Any], output_path: str, temp_dir: str) -> str:
        """Generate complete video from lesson JSON data"""
        try:
            slides = lesson_data.get('slides', [])
            if not slides:
                raise ValueError("No slides found in lesson data")
            
            self.slide_processor.reset_for_new_video()
            
            # Process all slides concurrently with reduced concurrency
            slide_video_paths = await self._process_slides_concurrent(slides, temp_dir)
            
            # Filter out None values (failed slides)
            valid_paths = [path for path in slide_video_paths if path and os.path.exists(path)]
            if not valid_paths:
                raise ValueError("No slide videos were successfully created")
            
            # Combine all slide videos
            final_video_path = await self._combine_videos(valid_paths, output_path)
            
            logger.info(f"Video generation completed: {final_video_path}")
            return final_video_path
                    
        except Exception as e:
            logger.error(f"Error generating lesson video: {e}")
            raise

    async def _process_slides_concurrent(self, slides: List[Dict], temp_dir: str) -> List[str]:
        """Process slides with optimized memory usage and improved concurrency"""
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
                
                try:
                    batch_results = await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True), 
                        timeout=300 
                    )
                    
                    # Process batch results
                    for result in batch_results:
                        if isinstance(result, Exception):
                            logger.error(f"Slide processing error: {result}")
                        elif result:
                            all_valid_paths.append(result)
                    
                    gc.collect()
                    time.sleep(0.2)
                    
                except asyncio.TimeoutError:
                    logger.error(f"Batch {i//batch_size + 1} processing timed out")
                    for task in tasks:
                        task.cancel()
            
            return all_valid_paths

    def _process_single_slide(self, slide: Dict, slide_index: int, temp_dir: str) -> str:
        """Process a single slide: TTS -> Images -> Video"""

        slide_id = int(slide.get('slide_id', slide_index + 1))
        slide_temp_dir = os.path.join(temp_dir, f"slide_{slide_index + 1}")
        os.makedirs(slide_temp_dir, exist_ok=True)

        audio_path = os.path.normpath(os.path.join(slide_temp_dir, f"audio_{slide_id}_{uuid.uuid4().hex[:8]}.mp3"))
        video_path = os.path.normpath(os.path.join(slide_temp_dir, f"slide_{slide_id}_{uuid.uuid4().hex[:8]}.mp4"))

        try:
            # 1. Generate TTS
            self._generate_tts_audio(slide.get('tts_script', ''), audio_path)

            # 2. Get audio duration
            audio_duration = 5.0
            if os.path.exists(audio_path):
                try:
                    with AudioFileClip(audio_path) as audio_clip:
                        audio_duration = audio_clip.duration
                except Exception as e:
                    logger.warning(f"Could not get duration for slide {slide_id}: {e}")

            # 3. Process slide images
            is_first_slide = (slide_id == 1)
            slide_result = self.slide_processor.process_slide_images(
                slide, slide_temp_dir, slide_id,
                self.image_resolution,
                add_disclaimer=is_first_slide,
                language=self.language
            )

            slide_result = self.slide_processor.calculate_slide_timing(slide_result, audio_duration)

            self._create_slide_video_with_timing(slide_result, audio_path, video_path)

            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not created: {video_path}")

            return video_path

        except Exception as e:
            logger.error(f"Error processing slide {slide_index + 1}: {e}")
            return None

    def _generate_tts_audio(self, text: str, output_path: str, silence_duration: float = 0.8) -> str:
        text = text.strip()

        if not text:
            logger.debug(f"No text provided, creating silent audio at {output_path}")
            return self.tts_service.create_silent_audio(output_path, duration=2.0)

        try:
            path = self.tts_service.synthesize_text(text, output_path)

            if silence_duration <= 0:
                return path

            try:
                with AudioFileClip(path) as audio:
                    audio = audio_fadeout(audio, 0.02)

                    fps = 44100
                    channels = 2 if audio.nchannels == 2 else 1
                    silence_samples = np.zeros((int(silence_duration * fps), channels), dtype=np.float32)
                    silence_clip = AudioArrayClip(silence_samples, fps=fps)

                    with silence_clip as silence:
                        final_clip = concatenate_audioclips([audio, silence])

                        temp_output = f"{os.path.splitext(path)[0]}_temp.mp3"
                        final_clip.write_audiofile(temp_output, codec="libmp3lame", logger=None, verbose=False)

                        final_clip.close()

                os.replace(temp_output, path)
                logger.debug(f"Added {silence_duration}s silence to audio: {path}")

                return path

            except Exception as silence_error:
                logger.warning(f"Could not add silence to audio: {silence_error}")
                return path

        except Exception as e:
            logger.error(f"TTS error: {e}")
            return self.tts_service.create_silent_audio(output_path, duration=3.0)

    def _create_slide_video_with_timing(self, slide_result: Dict[str, Any], audio_path: str, output_path: str):
        """Optimized video creation for slide with flexible image count."""
        output_path = os.path.normpath(os.path.abspath(output_path))
        audio_path = os.path.normpath(os.path.abspath(audio_path))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with self._safe_moviepy_context() as clips:
            try:
                audio_clip = AudioFileClip(audio_path)
                clips.append(audio_clip)
                total_duration = audio_clip.duration

                images = slide_result.get('images', [])
                if not images:
                    raise ValueError("No images provided for video creation")

                image_clips = []
                for img_info in images:
                    img_path = os.path.normpath(os.path.abspath(img_info['path']))
                    if not os.path.exists(img_path):
                        logger.warning(f"Image file not found: {img_path}")
                        continue
                    
                    try:
                        clip = (
                            ImageClip(img_path)
                            .resize(height=self.image_resolution[1])
                            .set_duration(img_info['duration'])
                            .set_fps(self.video_fps)
                        )
                        image_clips.append(clip)
                        clips.append(clip)
                    except Exception as e:
                        logger.warning(f"Could not create image clip for {img_path}: {e}")

                if not image_clips:
                    raise ValueError("No valid image clips could be created")

                video_clip = concatenate_videoclips(image_clips, method="compose")
                video_clip = video_clip.set_audio(audio_clip)
                clips.append(video_clip)

                self._safe_file_operation(
                    video_clip.write_videofile,
                    output_path,
                    fps=self.video_fps,
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None,
                    preset='medium',
                    ffmpeg_params=['-crf', '23']
                )

            except Exception as e:
                logger.error(f"Error creating slide video: {e}")
                raise

    async def _combine_videos(self, video_paths: List[str], output_path: str) -> str:
        """
        Combine all slide videos using FFmpeg CLI for memory efficiency.
        """
        try:
            if not video_paths:
                raise ValueError("No video files to combine")

            output_path = os.path.abspath(output_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            temp_dir = os.path.dirname(video_paths[0])
            list_file_path = os.path.join(temp_dir, "filelist.txt")

            with open(list_file_path, 'w') as f:
                for path in video_paths:
                    f.write(f"file '{os.path.abspath(path)}'\n")

            logger.info(f"Using FFmpeg to concatenate {len(video_paths)} videos...")

            cmd = [
                'ffmpeg',
                '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file_path,
                '-c', 'copy',
                output_path
            ]
            
            # Run FFmpeg command
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    logger.error(f"FFmpeg failed: {stderr.decode()}")
                    raise RuntimeError("FFmpeg concatenation failed")
                    
            except asyncio.CancelledError:
                logger.info("FFmpeg cancelled, cleaning up...")
                if 'process' in locals() and process.returncode is None:
                    process.terminate()
                    await asyncio.sleep(1)  # Give time to terminate
                raise

            logger.info(f"Final video saved successfully: {output_path}")
            
            # Dọn dẹp file list.txt
            os.remove(list_file_path)

            return output_path

        except Exception as e:
            logger.error(f"Error combining videos: {e}")
            raise


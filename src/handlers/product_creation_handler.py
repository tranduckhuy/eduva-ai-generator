"""
Product creation handler for generating final products (video/audio) from content
"""
import os
from datetime import datetime
from typing import Dict, Any
import shutil
import asyncio
import uuid

from src.handlers.base_handler import BaseTaskHandler
from src.models.task_messages import CreateProductMessage, JobType
from src.services.video_generator import VideoGenerator
from src.config.job_status import JobStatus
from src.utils.logger import logger
from src.services.tts_service import TTSService
from src.services.tts_service import TTSService
from moviepy.editor import concatenate_audioclips, AudioFileClip, VideoFileClip


class ProductCreationHandler(BaseTaskHandler):
    """Handler for create_product tasks"""
    
    async def process(self, message: CreateProductMessage) -> bool:
        """
        Process product creation task
        
        Args:
            message: Product creation message
            
        Returns:
            bool: True if successful, False otherwise
        """
        job_id = message.jobId
        local_product_file = None
        product_blob_name = None
        
        try:
            logger.info(f"Starting product creation for job {job_id}")
            
            workspace_dir = os.path.join(self.config.temp_dir, f"product_job_{job_id}_{uuid.uuid4().hex[:8]}")
            os.makedirs(workspace_dir, exist_ok=True)
            logger.info(f"Created unique job directory: {workspace_dir}")

            # Step 1: Download content from Azure
            logger.info(f"Downloading content file: {message.contentBlobName}")
            lesson_content = await self.download_json_content(message.contentBlobName)
            
            # Step 2: Generate product based on job type
            logger.info(f"Generating {message.jobType} product")
            local_product_file = await self._generate_product(
                message, lesson_content, workspace_dir
            )

            duration_seconds = None
            if message.jobType == JobType.VIDEO_LESSON:
                # Log video duration
                duration_seconds = self.get_video_duration(local_product_file)
            elif message.jobType == JobType.AUDIO_LESSON:
                # Log audio duration
                duration_seconds = self.get_audio_duration(local_product_file)
            logger.info(f"Product duration: {duration_seconds} seconds")

            # Step 3: Upload product to Azure
            if local_product_file:
                product_blob_name = f"ai-product/product_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{self._get_file_extension(message.jobType)}"
                await self.upload_product_file(local_product_file, product_blob_name)
            
            video_output_blob_name = product_blob_name if message.jobType == JobType.VIDEO_LESSON else None
            audio_output_blob_name = product_blob_name if message.jobType == JobType.AUDIO_LESSON else None

            # Step 4: Notify backend of success
            success_data = {
                "videoOutputBlobName": video_output_blob_name,
                "audioOutputBlobName": audio_output_blob_name,
                "actualDuration": duration_seconds,
            }
            
            await self.notify_success(
                job_id,
                JobStatus.Completed,
                **success_data
            )
            
            logger.info(f"Successfully completed product creation for job {job_id}")
            return True
            
        except Exception as e:
            error_message = f"Product creation failed for job {job_id}: {str(e)}"
            logger.error(error_message)
            
            # Delete blob file on Azure if it was uploaded
            if product_blob_name:
                await self.delete_blob(self.config.azure_output_container, product_blob_name)

            # Notify backend of failure
            await self.notify_failure(job_id, error_message)
            return False
            
        finally:
            # Clean up temporary files
            if os.path.exists(workspace_dir):
                shutil.rmtree(workspace_dir)
                logger.info(f"Cleaned up main workspace: {workspace_dir}")
    
    async def _generate_product(
        self, 
        message: CreateProductMessage, 
        lesson_content: Dict[str, Any],
        workspace_dir: str
    ) -> str:
        """
        Generate the final product based on job type
        
        Args:
            message: Product creation message
            lesson_content: Lesson content data
            
        Returns:
            str: Path to the generated product file
        """
        try:
            if message.jobType == JobType.VIDEO_LESSON:
                return await self._generate_video(message, lesson_content, workspace_dir)
            elif message.jobType == JobType.AUDIO_LESSON:
                return await self._generate_audio(message, lesson_content, workspace_dir)
            else:
                raise ValueError(f"Unsupported job type: {message.jobType}")
                
        except Exception as e:
            logger.error(f"Failed to generate {message.jobType} product: {e}")
            raise
    
    async def _generate_video(
        self, 
        message: CreateProductMessage, 
        lesson_content: Dict[str, Any],
        workspace_dir: str
    ) -> str:
        """
        Generate video from lesson content
        
        Args:
            message: Product creation message
            lesson_content: Lesson content data
            
        Returns:
            str: Path to the generated video file
        """
        try:
            # Prepare voice configuration
            voice_config = message.voiceConfig or {}

            # Set default voice config if not provided
            if not voice_config:
                voice_config = {
                    "languageCode": "vi-VN",
                    "name": "vi-VN-Neural2-A",
                    "speakingRate": 1.1
                }

            # Ensure speaking rate is at least 1.0
            if voice_config.get("speakingRate", 1.0) < 1.1:
                voice_config["speakingRate"] = 1.1

            # Initialize video generator
            logger.info(f"Voice config for video generation: {voice_config}")

            video_generator = VideoGenerator(voice_config=voice_config)
            
            # Generate output path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            unique_dir = os.path.join(workspace_dir, f"video_{message.jobId}_{timestamp}")
            os.makedirs(unique_dir, exist_ok=True)
            logger.info(f"Created unique video directory: {unique_dir}")

            output_filename = f"video_{message.jobId}_{timestamp}.mp4"
            output_path = os.path.join(unique_dir, output_filename)

            # Generate video
            logger.info("Starting video generation...")
            final_video_path = await video_generator.generate_lesson_video(
                lesson_content, 
                output_path,
                temp_dir=unique_dir
            )
            
            logger.info(f"Video generated successfully: {final_video_path}")
            return final_video_path
            
        except Exception as e:
            logger.error(f"Failed to generate video: {e}")
            raise
    
    async def _generate_audio(
        self,
        message: CreateProductMessage,
        lesson_content: Dict[str, Any],
        workspace_dir: str
    ) -> str:
        """
        Generate audio from lesson content (simplified version)
        """
        try:
            # Voice config
            voice_config = message.voiceConfig or {
                "languageCode": "vi-VN",
                "name": "vi-VN-Neural2-A",
                "speakingRate": 1.0
            }

            tts_service = TTSService(voice_config)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Generate output path
            unique_dir = os.path.join(workspace_dir, f"audio_{message.jobId}_{timestamp}")
            os.makedirs(unique_dir, exist_ok=True)

            output_path = os.path.join(unique_dir, f"audio_{message.jobId}_{timestamp}.mp3")

            # Process slides
            slides = lesson_content.get("slides", [])
            chunks = []
            current_chunk = []
            current_size = 0

            for slide in slides:
                text = slide.get("tts_script", "").strip()
                if not text:
                    continue

                text_bytes = len(text.encode('utf-8'))
                
                if current_size + text_bytes > 5000:
                    if current_chunk:
                        chunks.append(". ".join(current_chunk))
                    current_chunk = [text]
                    current_size = text_bytes
                else:
                    current_chunk.append(text)
                    current_size += text_bytes

            # Thêm chunk cuối cùng
            if current_chunk:
                chunks.append(". ".join(current_chunk))

            if not chunks:
                raise ValueError("No audio content found")

            # Generate audio từ các chunks
            temp_files = []
            tasks = []
            for i, chunk in enumerate(chunks):
                temp_path = os.path.join(unique_dir, f"temp_{i}_{uuid.uuid4().hex[:8]}.mp3")
                tasks.append(tts_service.generate_audio(chunk, temp_path))
            
            # Execute all TTS tasks concurrently
            temp_files = await asyncio.gather(*tasks)

            # Concatenate all audio files
            audio_clips = [AudioFileClip(f) for f in temp_files]
            final_audio = concatenate_audioclips(audio_clips)
            final_audio.write_audiofile(output_path)
            
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate audio: {e}")
            raise
    
    def _get_file_extension(self, job_type: JobType) -> str:
        """
        Get file extension based on job type
        
        Args:
            job_type: Type of job
            
        Returns:
            str: File extension
        """
        extension_map = {
            JobType.VIDEO_LESSON: "mp4",
            JobType.AUDIO_LESSON: "mp3",
        }
        return extension_map.get(job_type, "mp4")
    
    def get_video_duration(self, filepath: str) -> float:
        clip = VideoFileClip(filepath)
        duration = clip.duration
        clip.reader.close()
        clip.audio.reader.close_proc() if clip.audio else None
        return duration

    def get_audio_duration(self, filepath: str) -> float:
        clip = AudioFileClip(filepath)
        duration = clip.duration
        clip.close()
        return duration

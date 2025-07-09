"""
Product creation handler for generating final products (video/audio) from content
"""
import os
from datetime import datetime
from typing import Dict, Any

from src.handlers.base_handler import BaseTaskHandler
from src.models.task_messages import CreateProductMessage, JobType
from src.services.video_generator import VideoGenerator
from src.config.job_status import JobStatus
from src.utils.logger import logger


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
        
        try:
            logger.info(f"Starting product creation for job {job_id}")
            
            # Step 1: Download content from Azure
            logger.info(f"Downloading content file: {message.contentBlobName}")
            lesson_content = await self.download_json_content(message.contentBlobName)
            
            # Step 2: Generate product based on job type
            logger.info(f"Generating {message.jobType} product")
            local_product_file = await self._generate_product(
                message, lesson_content
            )
            
            # Step 3: Upload product to Azure
            product_blob_name = f"ai-product/product_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{self._get_file_extension(message.jobType)}"
            logger.info(f"Uploading product to: {product_blob_name}")
            await self.upload_product_file(local_product_file, product_blob_name)
            
            # Step 4: Notify backend of success
            success_data = {
                "productBlobName": product_blob_name
            }
            
            await self.notify_success(
                job_id,
                JobStatus.Completed,  # Pass the enum value directly
                **success_data
            )
            
            logger.info(f"Successfully completed product creation for job {job_id}")
            return True
            
        except Exception as e:
            error_message = f"Product creation failed for job {job_id}: {str(e)}"
            logger.error(error_message)
            
            # Notify backend of failure
            await self.notify_failure(job_id, error_message)
            return False
            
        finally:
            # Clean up temporary files
            if local_product_file:
                self.cleanup_temp_files(local_product_file)
    
    async def _generate_product(
        self, 
        message: CreateProductMessage, 
        lesson_content: Dict[str, Any]
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
                return await self._generate_video(message, lesson_content)
            elif message.jobType == JobType.AUDIO_LESSON:
                return await self._generate_audio(message, lesson_content)
            else:
                raise ValueError(f"Unsupported job type: {message.jobType}")
                
        except Exception as e:
            logger.error(f"Failed to generate {message.jobType} product: {e}")
            raise
    
    async def _generate_video(
        self, 
        message: CreateProductMessage, 
        lesson_content: Dict[str, Any]
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
                    "language_code": "vi-VN",
                    "name": "vi-VN-Neural2-A",
                    "speaking_rate": 1.0
                }
            
            # Initialize video generator
            video_generator = VideoGenerator(voice_config=voice_config)
            
            # Generate output path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"video_{message.jobId}_{timestamp}.mp4"
            output_path = os.path.join(self.config.temp_dir, output_filename)
            
            # Generate video
            logger.info("Starting video generation...")
            final_video_path = await video_generator.generate_lesson_video(
                lesson_content, 
                output_path
            )
            
            logger.info(f"Video generated successfully: {final_video_path}")
            return final_video_path
            
        except Exception as e:
            logger.error(f"Failed to generate video: {e}")
            raise
    
    async def _generate_audio(
        self, 
        message: CreateProductMessage, 
        lesson_content: Dict[str, Any]
    ) -> str:
        """
        Generate audio from lesson content
        
        Args:
            message: Product creation message
            lesson_content: Lesson content data
            
        Returns:
            str: Path to the generated audio file
        """
        try:
            from src.services.tts_service import TTSService
            from moviepy.editor import concatenate_audioclips, AudioFileClip
            import tempfile
            
            # Prepare voice configuration
            voice_config = message.voiceConfig or {}
            
            # Set default voice config if not provided
            if not voice_config:
                voice_config = {
                    "language_code": "vi-VN",
                    "name": "vi-VN-Neural2-A",
                    "speaking_rate": 1.0
                }
            
            # Initialize TTS service
            tts_service = TTSService(voice_config)
            
            # Generate output path
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"audio_{message.jobId}_{timestamp}.mp3"
            output_path = os.path.join(self.config.temp_dir, output_filename)
            
            # Collect all TTS scripts from slides
            slides = lesson_content.get("slides", [])
            audio_clips = []
            temp_audio_files = []
            
            try:
                for i, slide in enumerate(slides):
                    tts_script = slide.get("tts_script", "")
                    if tts_script.strip():
                        # Generate audio for this slide
                        temp_audio_path = os.path.join(
                            self.config.temp_dir, 
                            f"slide_audio_{i}_{timestamp}.mp3"
                        )
                        
                        await tts_service.generate_audio(tts_script, temp_audio_path)
                        
                        # Load audio clip
                        audio_clip = AudioFileClip(temp_audio_path)
                        audio_clips.append(audio_clip)
                        temp_audio_files.append(temp_audio_path)
                
                if audio_clips:
                    # Concatenate all audio clips
                    final_audio = concatenate_audioclips(audio_clips)
                    final_audio.write_audiofile(output_path)
                    final_audio.close()
                    
                    # Close individual clips
                    for clip in audio_clips:
                        clip.close()
                else:
                    raise ValueError("No audio content found in lesson slides")
                
            finally:
                # Clean up temporary audio files
                self.cleanup_temp_files(*temp_audio_files)
            
            logger.info(f"Audio generated successfully: {output_path}")
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

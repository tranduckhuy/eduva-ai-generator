"""
Content generation handler for processing source files into lesson content
"""
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, UnstructuredFileLoader

from src.handlers.base_handler import BaseTaskHandler
from src.models.task_messages import GenerateContentMessage
from src.agents.lesson_creator.flow import run_slide_creator
from src.config.job_status import JobStatus
from src.services.simple_document_processor import SimpleDocumentProcessor
from src.utils.logger import logger


class ContentGenerationHandler(BaseTaskHandler):
    """Handler for generate_content tasks with simple document processing"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.document_processor = SimpleDocumentProcessor()
    
    async def process(self, message: GenerateContentMessage) -> bool:
        """
        Process content generation task with simple document handling
        
        Args:
            message: Content generation message
            
        Returns:
            bool: True if successful, False otherwise
        """
        job_id = message.jobId
        local_source_files = []
        content_blob_name = None
        
        try:
            logger.info(f"Starting content generation for job {job_id}")
            
            # Step 1: Download source files
            local_source_files = await self.download_multiple_source_files(message.sourceBlobNames)
            
            # Step 2: Extract and combine content from all files
            combined_content = await self._extract_multiple_files_content(local_source_files)
            
            # Step 3: Process content to fit within limits
            processed_content = await self.document_processor.process_content(
                combined_content, message.topic
            )
            
            logger.info(f"Content processing complete: {len(processed_content)} characters")
            
            # Step 4: Generate lesson content with processed content
            lesson_content = await self._generate_lesson_content(
                message, processed_content
            )

            # Preview content generation
            preview_content = ""
            slides = lesson_content.get("slides", [])
            if slides and isinstance(slides, list):
                slide_texts = []
                for slide in slides:
                    content = slide.get("content", "")
                    if isinstance(content, list):
                        slide_texts.extend([str(item) for item in content if isinstance(item, str)])
                    elif isinstance(content, str):
                        slide_texts.append(content)
                preview_content = " ".join(slide_texts)[:300]
            if not preview_content:
                preview_content = str(lesson_content)[:300]
            
            # Step 4: Calculate metrics
            lesson_info = lesson_content.get("lesson_info", {})
            word_count = lesson_info.get("total_words", 0)
            
            # Step 5: Upload content to Azure
            content_blob_name = f"jobs/output/content_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            logger.info(f"Uploading content to: {content_blob_name}")
            await self.upload_json_content(lesson_content, content_blob_name)
            
            # Step 6: Notify backend of success
            success_data = {
                "wordCount": word_count,
                "contentBlobName": content_blob_name,
                "previewContent": preview_content,
            }

            success = await self.notify_success(
                job_id, 
                JobStatus.ContentGenerated,  # Use enum directly
                **success_data
            )

            if not success:
                raise Exception("Failed to notify backend of successful content generation")
            
            logger.info(f"Successfully completed content generation for job {job_id}")
            return True
            
        except Exception as e:
            error_message = f"Content generation failed for job {job_id}: {str(e)}"
            logger.error(error_message)

            # Delete blob file on Azure if it was uploaded

            if content_blob_name:
                success = await self.delete_blob(self.config.azure_input_container, content_blob_name)
                logger.error(f"Deleted blob file: {content_blob_name} due to error - Delete status: {success}")

            # Notify backend of failure
            await self.notify_failure(job_id, error_message)
            return False
            
        finally:
            # Clean up temporary files
            if local_source_files:
                self.cleanup_temp_files(*local_source_files)
    
    async def _extract_file_content(self, file_path: str) -> str:
        """
        Extract text content from various file types
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: Extracted text content
        """
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == ".pdf":
                loader = PyMuPDFLoader(file_path)
            elif file_extension in [".docx", ".doc"]:
                loader = Docx2txtLoader(file_path)
            else:
                loader = UnstructuredFileLoader(file_path)
            
            loop = asyncio.get_running_loop()
            # documents = loader.load()
            documents = await loop.run_in_executor(
                None,
                loader.load
            )
            content = "\n".join([doc.page_content for doc in documents])
            
            logger.info(f"Extracted {len(content)} characters from {file_extension} file")
            return content
            
        except Exception as e:
            logger.error(f"Failed to extract content from file {file_path}: {e}")
            raise
    
    async def _extract_multiple_files_content(self, file_paths: List[str]) -> str:
        """
        Extract and combine text content from multiple files
        
        Args:
            file_paths: List of file paths
            
        Returns:
            str: Combined extracted text content
        """
        try:
            combined_content = []
            
            for file_path in file_paths:
                content = await self._extract_file_content(file_path)
                filename = os.path.basename(file_path)
                combined_content.append(f"=== Content from {filename} ===\n{content}\n")
            
            result = "\n".join(combined_content)
            logger.info(f"Combined content from {len(file_paths)} files: {len(result)} characters")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract content from multiple files: {e}")
            raise

    async def _generate_lesson_content(
        self, 
        message: GenerateContentMessage, 
        file_content: str
    ) -> Dict[str, Any]:
        """
        Generate lesson content using the existing lesson creator
        
        Args:
            message: Content generation message
            file_content: Extracted file content
            
        Returns:
            Dict containing the generated lesson content
        """
        try:
            # Use the provided topic (required)
            topic = message.topic

            # Generate slides using existing slide creator
            result = await run_slide_creator(
                topic=topic,
                uploaded_files_content=file_content
            )
            
            if not result["success"]:
                raise Exception(f"Slide creation failed: {result.get('error', 'Unknown error')}")
            
            lesson_data = result["slide_data"]
            
            # Enhance with additional metadata
            lesson_data["generation_metadata"] = {
                "job_id": message.jobId,
                "source_blob_names": message.sourceBlobNames,
                "topic": message.topic,
                "generated_at": datetime.now().isoformat(),
                "source_content_length": len(file_content)
            }
            
            # Ensure lesson_info exists
            if "lesson_info" not in lesson_data:
                lesson_data["lesson_info"] = {}
            
            # Add job-specific metadata to lesson_info
            lesson_info = lesson_data["lesson_info"]
            lesson_info["topic"] = message.topic
            lesson_info["source_files_count"] = len(message.sourceBlobNames)
            
            logger.info(f"Generated lesson with {len(lesson_data.get('slides', []))} slides")
            return lesson_data
            
        except Exception as e:
            raise
    
    def _calculate_word_count(self, lesson_content: Dict[str, Any]) -> int:
        """
        Calculate total word count from lesson content
        
        Args:
            lesson_content: Generated lesson content
            
        Returns:
            int: Total word count
        """
        try:
            total_words = 0
            
            # Count words from slides
            slides = lesson_content.get("slides", [])
            for slide in slides:
                # Count words in content
                content = slide.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, str):
                            total_words += self.count_words(item)
                elif isinstance(content, str):
                    total_words += self.count_words(content)
                
                # Count words in TTS script
                tts_script = slide.get("tts_script", "")
                if tts_script:
                    total_words += self.count_words(tts_script)
            
            # Also get from lesson_info if available
            lesson_info_words = lesson_content.get("lesson_info", {}).get("total_words", 0)
            if lesson_info_words > total_words:
                total_words = lesson_info_words
            
            logger.info(f"Calculated total word count: {total_words}")
            return total_words
            
        except Exception as e:
            logger.error(f"Failed to calculate word count: {e}")
            return 0

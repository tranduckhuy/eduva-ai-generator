"""
Google Cloud Text-to-Speech Service

"""

import os
import time
import tempfile
import logging
from typing import Dict, Any, Optional, List
from google.cloud import texttospeech
from moviepy.editor import AudioClip
import asyncio

logger = logging.getLogger(__name__)

class TTSService:
    """Google Cloud Text-to-Speech Service"""
    
    def __init__(self, voice_config: Optional[Dict[str, Any]] = None):
        """Initialize TTS Service with voice configuration"""
        try:
            self.tts_client = texttospeech.TextToSpeechClient()
            logger.info("TTS Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS client: {e}")
            raise
        
        # Configure voice settings
        self._setup_voice_config(voice_config or {})
        
        # Performance tracking
        self._call_count = 0
        self._total_chars = 0
        self._total_duration = 0.0
    
    def _setup_voice_config(self, voice_config: Dict[str, Any]):
        """Setup voice and audio configuration"""
        language_code = voice_config.get('languageCode', 'vi-VN')
        voice_name = voice_config.get('name')
        
        if voice_name:
            # Use specific voice name
            self.voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name
            )
        else:
            # Use default female voice
            self.voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
        
        # Audio configuration - optimized for performance
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=voice_config.get('speakingRate', 1.1),
            sample_rate_hertz=22050  # Lower sample rate for faster processing
        )
    
    def synthesize_text(self, text: str, output_path: Optional[str] = None) -> str:
        """Convert text to speech and save as audio file"""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Use temp file if no output path specified
        if output_path is None:
            temp_fd, output_path = tempfile.mkstemp(suffix='.mp3', prefix='tts_')
            os.close(temp_fd)
        else:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:  # Only create directory if it's not empty
                os.makedirs(output_dir, exist_ok=True)
        
        # Normalize path for Windows compatibility
        output_path = os.path.normpath(os.path.abspath(output_path))
        
        start_time = time.time()
        
        try:
            # Prepare synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Call Google Cloud TTS API
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=self.voice,
                audio_config=self.audio_config
            )
            
            # Write audio content to file
            with open(output_path, "wb") as audio_file:
                audio_file.write(response.audio_content)
            
            # Verify file was created
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                raise Exception(f"Failed to create audio file: {output_path}")
            
            # Update performance metrics
            duration = time.time() - start_time
            self._call_count += 1
            self._total_chars += len(text)
            self._total_duration += duration
            
            logger.debug(f"TTS generated: {len(text)} chars in {duration:.2f}s -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"TTS synthesis failed for text '{text[:50]}...': {e}")
            raise
    
    async def generate_audio(self, text: str, output_path: str) -> str:
        """
        Generate audio from text (async wrapper for synchronous method)
        
        Args:
            text: Text to convert to speech
            output_path: Path to save the audio file
            
        Returns:
            str: Path to the generated audio file
        """
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.synthesize_text, text, output_path)
    
    def create_silent_audio(self, output_path: str, duration: float = 2.0) -> str:
        """Create a silent audio file"""
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:  # Only create directory if it's not empty
                os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.normpath(os.path.abspath(output_path))
            
            # Create silent audio using MoviePy
            fps = 44100
            silent_clip = AudioClip(lambda t: 0, duration=duration, fps=fps)
            silent_clip.write_audiofile(output_path, verbose=False, logger=None)
            silent_clip.close()
            
            logger.debug(f"Silent audio created: {duration}s -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to create silent audio: {e}")
            raise
    
    def estimate_audio_duration(self, text: str) -> float:
        """Estimate audio duration based on text length and speaking rate"""
        if not text or not text.strip():
            return 0.0
        
        # Average speaking rates adjusted for Vietnamese and our speaking rate setting
        base_wpm = 150  # Base words per minute
        adjusted_wpm = base_wpm * self.audio_config.speaking_rate
        
        # Count words (approximate for Vietnamese)
        word_count = len(text.split())
        
        # Estimate duration in seconds with buffer
        estimated_seconds = (word_count / adjusted_wpm) * 60
        
        # Add buffer for punctuation and natural pauses
        return estimated_seconds * 1.2
    

    # For testing and performance tracking
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get TTS service performance statistics"""
        avg_chars_per_call = self._total_chars / max(1, self._call_count)
        avg_duration_per_call = self._total_duration / max(1, self._call_count)
        chars_per_second = self._total_chars / max(0.1, self._total_duration)
        
        return {
            'total_calls': self._call_count,
            'total_characters': self._total_chars,
            'total_duration_seconds': self._total_duration,
            'average_characters_per_call': avg_chars_per_call,
            'average_duration_per_call': avg_duration_per_call,
            'characters_per_second': chars_per_second,
            'voice_config': {
                'languageCode': self.voice.language_code,
                'speakingRate': self.audio_config.speaking_rate,
                'sample_rate': self.audio_config.sample_rate_hertz
            }
        }
    
    def reset_stats(self):
        """Reset performance statistics"""
        self._call_count = 0
        self._total_chars = 0
        self._total_duration = 0.0

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


# Convenience function for quick usage
def estimate_speech_duration(text: str, speaking_rate: float = 1.1) -> float:
    """Quick function to estimate speech duration"""
    voice_config = {'speakingRate': speaking_rate}
    tts = TTSService(voice_config)
    return tts.estimate_audio_duration(text)

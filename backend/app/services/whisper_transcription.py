"""
Whisper-based lyrics transcription service using OpenAI API
"""
import openai
from typing import Optional, Dict, Any
import logging
import time

from app.models import Lyrics
from app.config import settings

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """Transcribe audio to lyrics using OpenAI Whisper API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Whisper transcriber

        Args:
            api_key: OpenAI API key (defaults to settings.openai_api_key)
        """
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Whisper transcription will not be available.")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=self.api_key)

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Optional[Lyrics]:
        """
        Transcribe audio file to text using Whisper API

        Args:
            audio_path: Path to audio file
            language: Optional language code (e.g., 'en', 'ja', 'es')

        Returns:
            Lyrics object with transcription results, or None if transcription fails
        """
        if not self.client:
            logger.error("Whisper client not initialized. Check API key.")
            return None

        logger.info(f"Transcribing audio with Whisper: {audio_path}")

        try:
            start_time = time.time()

            # Open audio file
            with open(audio_path, 'rb') as audio_file:
                # Call Whisper API with detailed response format
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",  # Using Whisper Large model
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",  # Get detailed segments
                    timestamp_granularities=["segment"]
                )

            processing_time = time.time() - start_time

            # Extract transcription data
            text = response.text
            detected_language = getattr(response, 'language', None)
            segments = []

            # Process segments if available
            if hasattr(response, 'segments') and response.segments:
                for segment in response.segments:
                    segments.append({
                        'id': segment.id,
                        'start': segment.start,
                        'end': segment.end,
                        'text': segment.text,
                        'confidence': getattr(segment, 'confidence', None),
                        'no_speech_prob': getattr(segment, 'no_speech_prob', None)
                    })

            # Calculate average confidence if available
            confidence = None
            if segments:
                confidences = [s.get('confidence') for s in segments if s.get('confidence') is not None]
                if confidences:
                    confidence = sum(confidences) / len(confidences)

            logger.info(f"Transcription completed in {processing_time:.2f}s. Detected language: {detected_language}")

            return Lyrics(
                text=text,
                language=detected_language,
                segments=segments if segments else None,
                confidence=confidence,
                model_used="whisper-1",
                processing_time=processing_time
            )

        except openai.APIError as e:
            logger.error(f"OpenAI API error during transcription: {e}")
            return None
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None

    def transcribe_with_translation(self, audio_path: str) -> Optional[Dict[str, Any]]:
        """
        Transcribe and translate audio to English

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with both transcription and translation
        """
        if not self.client:
            logger.error("Whisper client not initialized. Check API key.")
            return None

        try:
            # Get transcription in original language
            transcription = self.transcribe(audio_path)

            # Get English translation
            with open(audio_path, 'rb') as audio_file:
                translation_response = self.client.audio.translations.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )

            return {
                "transcription": transcription,
                "translation": translation_response
            }

        except Exception as e:
            logger.error(f"Error in transcription with translation: {e}")
            return None

"""
Main audio analysis service
Orchestrates all feature extraction, chord analysis, and transcription
"""
import os
import time
import logging
from typing import Dict, Any, Optional
from mutagen import File as MutagenFile

from app.models import MusicAnalysis, AudioFeatures
from app.services.librosa_features import LibrosaFeatureExtractor
from app.services.essentia_features import EssentiaFeatureExtractor
from app.services.chord_analyzer import ChordAnalyzer
from app.services.whisper_transcription import WhisperTranscriber

logger = logging.getLogger(__name__)


class AudioAnalyzer:
    """Main service to analyze audio files comprehensively"""

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize audio analyzer with all required services

        Args:
            openai_api_key: OpenAI API key for Whisper (optional)
        """
        self.librosa_extractor = LibrosaFeatureExtractor()
        self.essentia_extractor = EssentiaFeatureExtractor()
        self.chord_analyzer = ChordAnalyzer()
        self.whisper_transcriber = WhisperTranscriber(api_key=openai_api_key)

    async def analyze_audio(
        self,
        audio_path: str,
        source: str = "upload",
        source_path: Optional[str] = None,
        extract_lyrics: bool = True
    ) -> MusicAnalysis:
        """
        Perform comprehensive audio analysis

        Args:
            audio_path: Path to audio file
            source: Source of audio ("upload" or "google_drive")
            source_path: Original path if from Google Drive
            extract_lyrics: Whether to extract lyrics using Whisper

        Returns:
            MusicAnalysis document ready to be saved to MongoDB
        """
        logger.info(f"Starting comprehensive analysis of: {audio_path}")
        start_time = time.time()

        # Extract metadata
        metadata = self._extract_metadata(audio_path)
        filename = os.path.basename(audio_path)
        file_size = os.path.getsize(audio_path)

        # Initialize features
        audio_features = AudioFeatures()

        try:
            # 1. Extract librosa features
            logger.info("Extracting librosa features...")
            librosa_features, duration, sample_rate = self.librosa_extractor.extract_all_features(audio_path)
            audio_features.librosa = librosa_features

            # 2. Extract essentia features
            logger.info("Extracting essentia features...")
            essentia_features = self.essentia_extractor.extract_all_features(audio_path)
            audio_features.essentia = essentia_features

            # 3. Analyze chord progression
            logger.info("Analyzing chord progression...")
            chord_progression = self.chord_analyzer.analyze(audio_path)
            audio_features.chord_progression = chord_progression

            # 4. Extract lyrics with Whisper (if enabled)
            if extract_lyrics:
                logger.info("Transcribing lyrics with Whisper...")
                lyrics = self.whisper_transcriber.transcribe(audio_path)
                audio_features.lyrics = lyrics
            else:
                logger.info("Skipping lyrics extraction")

        except Exception as e:
            logger.error(f"Error during feature extraction: {e}")
            raise

        # Calculate total processing time
        processing_time_total = time.time() - start_time
        logger.info(f"Analysis completed in {processing_time_total:.2f}s")

        # Create MusicAnalysis document
        analysis = MusicAnalysis(
            filename=filename,
            file_size=file_size,
            duration=duration,
            sample_rate=sample_rate,
            source=source,
            source_path=source_path,
            title=metadata.get('title'),
            artist=metadata.get('artist'),
            album=metadata.get('album'),
            genre=metadata.get('genre'),
            year=metadata.get('year'),
            features=audio_features,
            processing_time_total=processing_time_total
        )

        return analysis

    def _extract_metadata(self, audio_path: str) -> Dict[str, Any]:
        """
        Extract metadata from audio file using mutagen

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with metadata fields
        """
        metadata = {}

        try:
            audio_file = MutagenFile(audio_path)

            if audio_file is None:
                logger.warning(f"Could not read metadata from: {audio_path}")
                return metadata

            # Common tags across formats
            tag_mapping = {
                'title': ['TIT2', 'Title', '\xa9nam', 'TITLE'],
                'artist': ['TPE1', 'Artist', '\xa9ART', 'ARTIST'],
                'album': ['TALB', 'Album', '\xa9alb', 'ALBUM'],
                'genre': ['TCON', 'Genre', '\xa9gen', 'GENRE'],
                'year': ['TDRC', 'Date', '\xa9day', 'DATE'],
            }

            for key, possible_tags in tag_mapping.items():
                for tag in possible_tags:
                    if tag in audio_file:
                        value = audio_file[tag]
                        if isinstance(value, list):
                            value = str(value[0])
                        else:
                            value = str(value)

                        metadata[key] = value
                        break

            # Handle year specially - extract just the year number
            if 'year' in metadata:
                try:
                    year_str = metadata['year']
                    # Extract first 4 digits
                    import re
                    year_match = re.search(r'\d{4}', year_str)
                    if year_match:
                        metadata['year'] = int(year_match.group())
                except:
                    pass

            logger.info(f"Extracted metadata: {metadata}")

        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")

        return metadata

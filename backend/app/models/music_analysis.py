"""
MongoDB models for music analysis data
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from beanie import Document
from pydantic import BaseModel, Field


class LibrosaFeatures(BaseModel):
    """Librosa extracted features"""
    # Spectral features
    spectral_centroid: Optional[List[float]] = None
    spectral_bandwidth: Optional[List[float]] = None
    spectral_rolloff: Optional[List[float]] = None
    spectral_contrast: Optional[List[List[float]]] = None
    spectral_flatness: Optional[List[float]] = None

    # Rhythm features
    tempo: Optional[float] = None
    beat_frames: Optional[List[int]] = None
    beat_times: Optional[List[float]] = None

    # Timbral features
    mfcc: Optional[List[List[float]]] = None  # Mel-frequency cepstral coefficients
    chroma_stft: Optional[List[List[float]]] = None
    chroma_cqt: Optional[List[List[float]]] = None
    chroma_cens: Optional[List[List[float]]] = None

    # Tonal features
    tonnetz: Optional[List[List[float]]] = None  # Tonal centroid features

    # Zero crossing rate
    zero_crossing_rate: Optional[List[float]] = None

    # Root Mean Square Energy
    rms: Optional[List[float]] = None

    # Mel-scaled spectrogram
    mel_spectrogram: Optional[List[List[float]]] = None

    # Onset detection
    onset_strength: Optional[List[float]] = None
    onset_frames: Optional[List[int]] = None
    onset_times: Optional[List[float]] = None

    # Harmonic and percussive components
    harmonic: Optional[str] = None  # Stored as file reference if needed
    percussive: Optional[str] = None  # Stored as file reference if needed


class EssentiaFeatures(BaseModel):
    """Essentia extracted features"""
    # Low-level descriptors
    loudness: Optional[float] = None
    dynamic_complexity: Optional[float] = None

    # Rhythm descriptors
    bpm: Optional[float] = None
    bpm_histogram: Optional[List[float]] = None
    beats_loudness: Optional[Dict[str, float]] = None
    onset_rate: Optional[float] = None
    danceability: Optional[float] = None

    # Tonal descriptors
    key_key: Optional[str] = None  # Detected key (e.g., "C", "Am")
    key_scale: Optional[str] = None  # "major" or "minor"
    key_strength: Optional[float] = None
    tuning_frequency: Optional[float] = None

    # Spectral descriptors
    spectral_complexity: Optional[float] = None
    spectral_energy: Optional[float] = None
    hfc: Optional[float] = None  # High Frequency Content

    # Timbre descriptors
    dissonance: Optional[float] = None
    spectral_centroid_mean: Optional[float] = None
    spectral_entropy: Optional[float] = None

    # Voice/instrumental
    voice_instrumental: Optional[str] = None  # "voice" or "instrumental"
    voice_instrumental_confidence: Optional[float] = None

    # Mood/Genre (if available)
    mood_acoustic: Optional[float] = None
    mood_aggressive: Optional[float] = None
    mood_electronic: Optional[float] = None
    mood_happy: Optional[float] = None
    mood_sad: Optional[float] = None
    mood_relaxed: Optional[float] = None
    mood_party: Optional[float] = None

    # Additional high-level features
    average_loudness: Optional[float] = None
    pitch_salience: Optional[float] = None


class ChordProgression(BaseModel):
    """Chord progression analysis"""
    chords: List[Dict[str, Any]] = []  # [{"time": 0.5, "chord": "C:maj", "confidence": 0.85}, ...]
    chord_sequence: List[str] = []  # Simplified sequence: ["C:maj", "F:maj", "G:maj", ...]
    key: Optional[str] = None  # Estimated key
    mode: Optional[str] = None  # "major" or "minor"

    # Statistical information
    unique_chords: List[str] = []
    chord_transitions: Dict[str, int] = {}  # Transition frequency
    most_common_chord: Optional[str] = None

    # Analysis metadata
    analyzer_used: str = "madmom"  # "madmom", "crema", or "combined"
    confidence_mean: Optional[float] = None


class Lyrics(BaseModel):
    """Lyrics transcription from Whisper"""
    text: Optional[str] = None
    language: Optional[str] = None
    segments: Optional[List[Dict[str, Any]]] = None  # Time-aligned segments
    confidence: Optional[float] = None

    # Whisper model info
    model_used: str = "whisper-large"
    processing_time: Optional[float] = None


class AudioFeatures(BaseModel):
    """Combined audio features"""
    librosa: Optional[LibrosaFeatures] = None
    essentia: Optional[EssentiaFeatures] = None
    chord_progression: Optional[ChordProgression] = None
    lyrics: Optional[Lyrics] = None


class MusicAnalysis(Document):
    """Main document for music analysis stored in MongoDB"""

    # File information
    filename: str
    file_size: int  # bytes
    duration: float  # seconds
    sample_rate: int
    source: str  # "upload" or "google_drive"
    source_path: Optional[str] = None  # Google Drive path if applicable

    # Metadata
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None

    # Analysis results
    features: AudioFeatures

    # Processing metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_total: Optional[float] = None  # Total processing time in seconds

    class Settings:
        name = "music_analyses"
        indexes = [
            "filename",
            "artist",
            "title",
            "created_at",
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "song.mp3",
                "file_size": 5242880,
                "duration": 180.5,
                "sample_rate": 44100,
                "source": "upload",
                "title": "Example Song",
                "artist": "Example Artist",
            }
        }

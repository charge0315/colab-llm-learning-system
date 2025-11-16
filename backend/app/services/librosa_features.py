"""
Librosa-based feature extraction service
Extracts all available audio features using librosa
"""
import librosa
import numpy as np
from typing import Dict, Any, Tuple
import logging

from app.models import LibrosaFeatures

logger = logging.getLogger(__name__)


class LibrosaFeatureExtractor:
    """Extract comprehensive audio features using librosa"""

    def __init__(self):
        self.sr = 22050  # Default sample rate
        self.hop_length = 512
        self.n_fft = 2048

    def extract_all_features(self, audio_path: str) -> Tuple[LibrosaFeatures, float, int]:
        """
        Extract all available librosa features from an audio file

        Args:
            audio_path: Path to audio file

        Returns:
            Tuple of (LibrosaFeatures, duration, sample_rate)
        """
        logger.info(f"Extracting librosa features from: {audio_path}")

        # Load audio file
        y, sr = librosa.load(audio_path, sr=None)
        self.sr = sr
        duration = librosa.get_duration(y=y, sr=sr)

        logger.info(f"Audio loaded: duration={duration:.2f}s, sr={sr}Hz")

        features = {}

        try:
            # Spectral features
            features.update(self._extract_spectral_features(y))

            # Rhythm features
            features.update(self._extract_rhythm_features(y))

            # Timbral features
            features.update(self._extract_timbral_features(y))

            # Tonal features
            features.update(self._extract_tonal_features(y))

            # Zero crossing rate
            features["zero_crossing_rate"] = librosa.feature.zero_crossing_rate(
                y, frame_length=self.n_fft, hop_length=self.hop_length
            )[0].tolist()

            # RMS Energy
            features["rms"] = librosa.feature.rms(
                y=y, frame_length=self.n_fft, hop_length=self.hop_length
            )[0].tolist()

            # Onset detection
            features.update(self._extract_onset_features(y))

            # Note: Harmonic/percussive separation produces large arrays
            # We'll skip storing the full separated signals for now
            # They can be computed on-demand if needed

            logger.info("Successfully extracted all librosa features")
            return LibrosaFeatures(**features), duration, sr

        except Exception as e:
            logger.error(f"Error extracting librosa features: {e}")
            raise

    def _extract_spectral_features(self, y: np.ndarray) -> Dict[str, Any]:
        """Extract spectral features"""
        features = {}

        # Spectral centroid
        spectral_centroid = librosa.feature.spectral_centroid(
            y=y, sr=self.sr, n_fft=self.n_fft, hop_length=self.hop_length
        )
        features["spectral_centroid"] = spectral_centroid[0].tolist()

        # Spectral bandwidth
        spectral_bandwidth = librosa.feature.spectral_bandwidth(
            y=y, sr=self.sr, n_fft=self.n_fft, hop_length=self.hop_length
        )
        features["spectral_bandwidth"] = spectral_bandwidth[0].tolist()

        # Spectral rolloff
        spectral_rolloff = librosa.feature.spectral_rolloff(
            y=y, sr=self.sr, n_fft=self.n_fft, hop_length=self.hop_length
        )
        features["spectral_rolloff"] = spectral_rolloff[0].tolist()

        # Spectral contrast
        spectral_contrast = librosa.feature.spectral_contrast(
            y=y, sr=self.sr, n_fft=self.n_fft, hop_length=self.hop_length
        )
        features["spectral_contrast"] = spectral_contrast.tolist()

        # Spectral flatness
        spectral_flatness = librosa.feature.spectral_flatness(
            y=y, n_fft=self.n_fft, hop_length=self.hop_length
        )
        features["spectral_flatness"] = spectral_flatness[0].tolist()

        # Mel spectrogram
        mel_spec = librosa.feature.melspectrogram(
            y=y, sr=self.sr, n_fft=self.n_fft, hop_length=self.hop_length
        )
        # Convert to dB and limit size for storage
        mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
        features["mel_spectrogram"] = mel_spec_db.tolist()

        return features

    def _extract_rhythm_features(self, y: np.ndarray) -> Dict[str, Any]:
        """Extract rhythm features"""
        features = {}

        # Tempo and beat tracking
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=self.sr)
        features["tempo"] = float(tempo)
        features["beat_frames"] = beat_frames.tolist()

        # Convert beat frames to time
        beat_times = librosa.frames_to_time(beat_frames, sr=self.sr)
        features["beat_times"] = beat_times.tolist()

        return features

    def _extract_timbral_features(self, y: np.ndarray) -> Dict[str, Any]:
        """Extract timbral features"""
        features = {}

        # MFCCs (Mel-frequency cepstral coefficients)
        mfccs = librosa.feature.mfcc(
            y=y, sr=self.sr, n_mfcc=20, n_fft=self.n_fft, hop_length=self.hop_length
        )
        features["mfcc"] = mfccs.tolist()

        # Chroma features
        chroma_stft = librosa.feature.chroma_stft(
            y=y, sr=self.sr, n_fft=self.n_fft, hop_length=self.hop_length
        )
        features["chroma_stft"] = chroma_stft.tolist()

        chroma_cqt = librosa.feature.chroma_cqt(
            y=y, sr=self.sr, hop_length=self.hop_length
        )
        features["chroma_cqt"] = chroma_cqt.tolist()

        chroma_cens = librosa.feature.chroma_cens(
            y=y, sr=self.sr, hop_length=self.hop_length
        )
        features["chroma_cens"] = chroma_cens.tolist()

        return features

    def _extract_tonal_features(self, y: np.ndarray) -> Dict[str, Any]:
        """Extract tonal features"""
        features = {}

        # Tonnetz (tonal centroid features)
        tonnetz = librosa.feature.tonnetz(
            y=y, sr=self.sr
        )
        features["tonnetz"] = tonnetz.tolist()

        return features

    def _extract_onset_features(self, y: np.ndarray) -> Dict[str, Any]:
        """Extract onset detection features"""
        features = {}

        # Onset strength
        onset_env = librosa.onset.onset_strength(y=y, sr=self.sr)
        features["onset_strength"] = onset_env.tolist()

        # Onset detection
        onset_frames = librosa.onset.onset_detect(
            onset_envelope=onset_env, sr=self.sr
        )
        features["onset_frames"] = onset_frames.tolist()

        # Convert to time
        onset_times = librosa.frames_to_time(onset_frames, sr=self.sr)
        features["onset_times"] = onset_times.tolist()

        return features

"""
Essentia-based feature extraction service
Extracts comprehensive audio features using Essentia
"""
import essentia
import essentia.standard as es
import numpy as np
from typing import Dict, Any
import logging

from app.models import EssentiaFeatures

logger = logging.getLogger(__name__)


class EssentiaFeatureExtractor:
    """Extract comprehensive audio features using Essentia"""

    def __init__(self):
        self.sample_rate = 44100

    def extract_all_features(self, audio_path: str) -> EssentiaFeatures:
        """
        Extract all available Essentia features from an audio file

        Args:
            audio_path: Path to audio file

        Returns:
            EssentiaFeatures object
        """
        logger.info(f"Extracting Essentia features from: {audio_path}")

        # Load audio
        loader = es.MonoLoader(filename=audio_path, sampleRate=self.sample_rate)
        audio = loader()

        features = {}

        try:
            # Low-level descriptors
            features.update(self._extract_lowlevel_features(audio))

            # Rhythm descriptors
            features.update(self._extract_rhythm_features(audio))

            # Tonal descriptors
            features.update(self._extract_tonal_features(audio))

            # High-level descriptors
            features.update(self._extract_highlevel_features(audio))

            logger.info("Successfully extracted all Essentia features")
            return EssentiaFeatures(**features)

        except Exception as e:
            logger.error(f"Error extracting Essentia features: {e}")
            raise

    def _extract_lowlevel_features(self, audio: np.ndarray) -> Dict[str, Any]:
        """Extract low-level audio descriptors"""
        features = {}

        # Loudness
        loudness_algo = es.Loudness()
        features["loudness"] = float(loudness_algo(audio))

        # Dynamic complexity
        dynamic_complexity_algo = es.DynamicComplexity()
        features["dynamic_complexity"] = float(dynamic_complexity_algo(audio))

        # Average loudness (using RMS)
        rms_algo = es.RMS()
        frame_size = 2048
        hop_size = 1024
        rms_values = []

        for frame in es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size):
            rms_values.append(rms_algo(frame))

        if rms_values:
            features["average_loudness"] = float(np.mean(rms_values))

        return features

    def _extract_rhythm_features(self, audio: np.ndarray) -> Dict[str, Any]:
        """Extract rhythm descriptors"""
        features = {}

        # BPM detection using RhythmExtractor2013 (more accurate)
        rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
        bpm, beat_times, confidence, estimates, bpm_intervals = rhythm_extractor(audio)

        features["bpm"] = float(bpm)

        # BPM histogram
        if len(estimates) > 0:
            features["bpm_histogram"] = estimates.tolist()

        # Beats loudness
        if len(beat_times) > 0:
            beat_loudness_values = []
            loudness_algo = es.Loudness()

            for beat_time in beat_times:
                sample_idx = int(beat_time * self.sample_rate)
                window_size = int(0.1 * self.sample_rate)  # 100ms window
                start = max(0, sample_idx - window_size // 2)
                end = min(len(audio), sample_idx + window_size // 2)

                if end > start:
                    beat_frame = audio[start:end]
                    beat_loudness_values.append(loudness_algo(beat_frame))

            if beat_loudness_values:
                features["beats_loudness"] = {
                    "mean": float(np.mean(beat_loudness_values)),
                    "std": float(np.std(beat_loudness_values)),
                    "max": float(np.max(beat_loudness_values)),
                    "min": float(np.min(beat_loudness_values)),
                }

        # Onset rate
        onset_rate_algo = es.OnsetRate()
        onset_rate = onset_rate_algo(audio)
        features["onset_rate"] = float(onset_rate)

        # Danceability
        danceability_algo = es.Danceability()
        danceability, dfa = danceability_algo(audio)
        features["danceability"] = float(danceability)

        return features

    def _extract_tonal_features(self, audio: np.ndarray) -> Dict[str, Any]:
        """Extract tonal descriptors"""
        features = {}

        # Key detection
        key_extractor = es.KeyExtractor()
        key, scale, strength = key_extractor(audio)

        features["key_key"] = key
        features["key_scale"] = scale
        features["key_strength"] = float(strength)

        # Tuning frequency
        tuning_frequency_algo = es.TuningFrequency()
        tuning_freq, tuning_cents = tuning_frequency_algo(audio)
        features["tuning_frequency"] = float(tuning_freq)

        # Pitch salience
        pitch_salience_values = []
        pitch_salience_algo = es.PitchSalience()
        spectrum_algo = es.Spectrum()

        for frame in es.FrameGenerator(audio, frameSize=2048, hopSize=1024):
            spectrum = spectrum_algo(frame)
            salience = pitch_salience_algo(spectrum)
            pitch_salience_values.append(salience)

        if pitch_salience_values:
            features["pitch_salience"] = float(np.mean(pitch_salience_values))

        return features

    def _extract_highlevel_features(self, audio: np.ndarray) -> Dict[str, Any]:
        """Extract high-level descriptors (spectral, timbre, etc.)"""
        features = {}

        # Spectral complexity
        spectral_complexity_algo = es.SpectralComplexity()
        spectrum_algo = es.Spectrum()

        complexity_values = []
        for frame in es.FrameGenerator(audio, frameSize=2048, hopSize=1024):
            spectrum = spectrum_algo(frame)
            complexity = spectral_complexity_algo(spectrum)
            complexity_values.append(complexity)

        if complexity_values:
            features["spectral_complexity"] = float(np.mean(complexity_values))

        # Spectral energy
        energy_algo = es.Energy()
        energy_values = []

        for frame in es.FrameGenerator(audio, frameSize=2048, hopSize=1024):
            spectrum = spectrum_algo(frame)
            energy = energy_algo(spectrum)
            energy_values.append(energy)

        if energy_values:
            features["spectral_energy"] = float(np.mean(energy_values))

        # High Frequency Content
        hfc_algo = es.HFC()
        hfc_values = []

        for frame in es.FrameGenerator(audio, frameSize=2048, hopSize=1024):
            spectrum = spectrum_algo(frame)
            hfc = hfc_algo(spectrum)
            hfc_values.append(hfc)

        if hfc_values:
            features["hfc"] = float(np.mean(hfc_values))

        # Dissonance
        dissonance_algo = es.Dissonance()
        dissonance_values = []

        for frame in es.FrameGenerator(audio, frameSize=2048, hopSize=1024):
            spectrum = spectrum_algo(frame)
            dissonance = dissonance_algo(spectrum)
            dissonance_values.append(dissonance)

        if dissonance_values:
            features["dissonance"] = float(np.mean(dissonance_values))

        # Spectral centroid
        centroid_algo = es.SpectralCentroidTime()
        centroid_values = []

        for frame in es.FrameGenerator(audio, frameSize=2048, hopSize=1024):
            centroid = centroid_algo(frame)
            centroid_values.append(centroid)

        if centroid_values:
            features["spectral_centroid_mean"] = float(np.mean(centroid_values))

        # Spectral entropy
        entropy_algo = es.Entropy()
        entropy_values = []

        for frame in es.FrameGenerator(audio, frameSize=2048, hopSize=1024):
            spectrum = spectrum_algo(frame)
            entropy = entropy_algo(spectrum)
            entropy_values.append(entropy)

        if entropy_values:
            features["spectral_entropy"] = float(np.mean(entropy_values))

        return features

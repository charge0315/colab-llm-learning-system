"""
Chord progression analysis service using madmom
High-accuracy chord detection and progression analysis
"""
import madmom
import numpy as np
from typing import Dict, Any, List, Tuple
from collections import Counter
import logging

from app.models import ChordProgression

logger = logging.getLogger(__name__)


class ChordAnalyzer:
    """Analyze chord progressions using madmom's CNN-based chord recognition"""

    # Standard chord templates
    CHORD_NAMES = [
        'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'
    ]

    CHORD_QUALITIES = ['maj', 'min', 'dim', 'aug', 'maj7', 'min7', '7', 'dim7']

    def __init__(self):
        self.fps = 10  # Frames per second for chord recognition

    def analyze(self, audio_path: str) -> ChordProgression:
        """
        Analyze chord progression from audio file

        Args:
            audio_path: Path to audio file

        Returns:
            ChordProgression object with detected chords and analysis
        """
        logger.info(f"Analyzing chord progression from: {audio_path}")

        try:
            # Use madmom's DeepChromaProcessor and CNNChordFeatureProcessor
            chords_data = self._detect_chords_madmom(audio_path)

            # Process and analyze the chord sequence
            analysis = self._analyze_chord_sequence(chords_data)

            logger.info(f"Detected {len(analysis['unique_chords'])} unique chords")
            return ChordProgression(**analysis)

        except Exception as e:
            logger.error(f"Error analyzing chords: {e}")
            # Return basic analysis with error info
            return ChordProgression(
                chords=[],
                chord_sequence=[],
                analyzer_used="madmom",
                unique_chords=[],
                chord_transitions={}
            )

    def _detect_chords_madmom(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Detect chords using madmom's CNN-based chord recognition

        Returns:
            List of chord detections with time, chord name, and confidence
        """
        # Create chord recognizer
        dcp = madmom.audio.chroma.DeepChromaProcessor()
        decode = madmom.features.chords.DeepChromaChordRecognitionProcessor()

        # Process audio
        chroma = dcp(audio_path)
        chords = decode(chroma)

        # Convert to structured format
        chords_data = []
        prev_chord = None
        prev_time = 0

        for frame_idx, chord_idx in enumerate(chords):
            time = frame_idx / self.fps
            chord_name = self._get_chord_name(chord_idx)

            # Only add when chord changes
            if chord_name != prev_chord:
                if prev_chord is not None:
                    # Add previous chord with duration
                    chords_data.append({
                        'time': prev_time,
                        'chord': prev_chord,
                        'duration': time - prev_time,
                        'confidence': 0.85  # madmom doesn't provide confidence, use default
                    })

                prev_chord = chord_name
                prev_time = time

        # Add final chord
        if prev_chord is not None:
            chords_data.append({
                'time': prev_time,
                'chord': prev_chord,
                'duration': 0.5,  # Estimate
                'confidence': 0.85
            })

        return chords_data

    def _get_chord_name(self, chord_idx: int) -> str:
        """
        Convert madmom chord index to chord name

        madmom uses 25 chord classes:
        - 24 chords: 12 major + 12 minor
        - 1 no-chord class
        """
        if chord_idx == 24:  # No chord
            return "N"

        root = chord_idx % 12
        quality = "maj" if chord_idx < 12 else "min"

        return f"{self.CHORD_NAMES[root]}:{quality}"

    def _analyze_chord_sequence(self, chords_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze detected chord sequence for patterns and statistics

        Args:
            chords_data: List of chord detections

        Returns:
            Dictionary with analysis results
        """
        if not chords_data:
            return {
                "chords": [],
                "chord_sequence": [],
                "unique_chords": [],
                "chord_transitions": {},
                "analyzer_used": "madmom",
                "confidence_mean": 0.0
            }

        # Extract chord sequence
        chord_sequence = [chord['chord'] for chord in chords_data]

        # Get unique chords
        unique_chords = list(set(chord_sequence))

        # Calculate chord transitions
        transitions = {}
        for i in range(len(chord_sequence) - 1):
            from_chord = chord_sequence[i]
            to_chord = chord_sequence[i + 1]
            transition = f"{from_chord} -> {to_chord}"
            transitions[transition] = transitions.get(transition, 0) + 1

        # Find most common chord
        chord_counts = Counter(chord_sequence)
        most_common_chord = chord_counts.most_common(1)[0][0] if chord_counts else None

        # Calculate average confidence
        confidences = [chord['confidence'] for chord in chords_data]
        confidence_mean = float(np.mean(confidences)) if confidences else 0.0

        # Estimate key (simplified - based on most common chord)
        key = None
        mode = None
        if most_common_chord and most_common_chord != "N":
            parts = most_common_chord.split(":")
            if len(parts) == 2:
                key = parts[0]
                mode = "major" if parts[1] == "maj" else "minor"

        return {
            "chords": chords_data,
            "chord_sequence": chord_sequence,
            "unique_chords": unique_chords,
            "chord_transitions": transitions,
            "most_common_chord": most_common_chord,
            "key": key,
            "mode": mode,
            "analyzer_used": "madmom",
            "confidence_mean": confidence_mean
        }

    def _estimate_key_from_chords(self, chord_sequence: List[str]) -> Tuple[str, str]:
        """
        Estimate musical key from chord sequence

        Args:
            chord_sequence: List of chord names

        Returns:
            Tuple of (key, mode)
        """
        # Simple heuristic: most common chord is likely the tonic
        # More sophisticated key estimation would use Krumhansl-Schmuckler algorithm

        chord_counts = Counter(chord_sequence)
        if not chord_counts:
            return None, None

        most_common = chord_counts.most_common(1)[0][0]

        if most_common == "N":  # No chord
            return None, None

        # Parse chord
        parts = most_common.split(":")
        if len(parts) != 2:
            return None, None

        root = parts[0]
        quality = parts[1]

        mode = "major" if quality == "maj" else "minor"

        return root, mode

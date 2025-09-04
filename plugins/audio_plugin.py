# audio plugin 
# plugins/audio_plugin.py
from typing import List, Dict, Any
from pathlib import Path
try:
    import soundfile as sf
    import webrtcvad
    import numpy as np
    _HAS_AUDIO = True
except Exception:
    _HAS_AUDIO = False

class AudioPlugin:
    """Einfache WAV-Aufnahme und Voice-Activity-Detection (VAD)."""

    def __init__(self, sample_rate: int = 16000, vad_mode: int = 3, output_dir: str = "data/uploads/audio"):
        self.sample_rate = int(sample_rate)
        self.vad_mode = int(vad_mode)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_wav(self, path: str):
        if not _HAS_AUDIO:
            raise RuntimeError("Audio-Libs fehlen (soundfile/webrtcvad/numpy)")
        data, sr = sf.read(path, dtype='int16')
        if sr != self.sample_rate:
            raise ValueError("Sample rate mismatch")
        return data

    def vad_frames(self, data: 'np.ndarray', frame_ms: int = 30) -> List[bool]:
        if not _HAS_AUDIO:
            raise RuntimeError("Audio-Libs fehlen (soundfile/webrtcvad/numpy)")
        vad = webrtcvad.Vad(self.vad_mode)
        samples_per_frame = int(self.sample_rate * (frame_ms / 1000.0))
        raw = data.astype(np.int16).tobytes()
        frames = []
        for offset in range(0, len(raw), samples_per_frame * 2):
            chunk = raw[offset: offset + samples_per_frame * 2]
            if len(chunk) < samples_per_frame * 2:
                break
            frames.append(vad.is_speech(chunk, self.sample_rate))
        return frames

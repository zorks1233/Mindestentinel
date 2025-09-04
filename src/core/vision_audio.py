# vision_audio 
# src/core/vision_audio.py
"""
Vision & Audio helpers:
- Image processing (Pillow, OpenCV optional)
- Basic image features, thumbnail, metadata
- Audio: basic WAV loader, optional webrtcvad VAD
Designed to be CPU-friendly and fallback-safe.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Tuple, Dict, Any, List

try:
    from PIL import Image, ImageOps
    _HAS_PIL = True
except Exception:
    _HAS_PIL = False

try:
    import cv2
    _HAS_CV2 = True
except Exception:
    _HAS_CV2 = False

try:
    import soundfile as sf
    import webrtcvad
    _HAS_AUDIO = True
except Exception:
    _HAS_AUDIO = False

class VisionAudio:
    def __init__(self, base_data_dir: str | None = None):
        self.base = Path(base_data_dir) if base_data_dir else Path("data")
        self.images_dir = self.base / "uploads" / "images"
        self.audio_dir = self.base / "uploads" / "audio"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    # ---------- Images ----------
    def save_image(self, src_path: str, make_thumb: bool = True, thumb_size: Tuple[int,int] = (256,256)) -> Dict[str,Any]:
        src = Path(src_path)
        if not src.exists():
            raise FileNotFoundError(src_path)
        dst = self.images_dir / src.name
        if src.resolve() != dst.resolve():
            dst.write_bytes(src.read_bytes())
        result = {"path": str(dst)}
        if make_thumb and _HAS_PIL:
            thumb_path = str(dst) + ".thumb.jpg"
            with Image.open(dst) as im:
                im.thumbnail(thumb_size)
                im.convert("RGB").save(thumb_path, "JPEG", quality=85)
            result["thumbnail"] = thumb_path
        return result

    def basic_image_features(self, path: str) -> Dict[str, Any]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(path)
        if _HAS_PIL:
            with Image.open(p) as im:
                w,h = im.size
                mode = im.mode
                # color histogram (coarse)
                hist = im.histogram()[:256]
                avg_color = sum(i*v for i,v in enumerate(hist)) / max(1, sum(hist))
            return {"width": w, "height": h, "mode": mode, "avg_color_index": avg_color}
        elif _HAS_CV2:
            img = cv2.imread(str(p))
            h,w = img.shape[:2]
            mean = img.mean(axis=(0,1)).tolist()
            return {"width": w, "height": h, "mean_color": mean}
        else:
            raise RuntimeError("Keine Bildbibliothek installiert (Pillow oder OpenCV)")

    # ---------- Audio ----------
    def save_audio(self, src_path: str) -> Dict[str,Any]:
        src = Path(src_path)
        if not src.exists():
            raise FileNotFoundError(src_path)
        dst = self.audio_dir / src.name
        if src.resolve() != dst.resolve():
            dst.write_bytes(src.read_bytes())
        return {"path": str(dst)}

    def vad_frames(self, path: str, frame_duration_ms: int = 30) -> List[bool]:
        if not _HAS_AUDIO:
            raise RuntimeError("Audio libs (soundfile / webrtcvad) fehlen")
        data, sr = sf.read(path, dtype='int16')
        if sr not in (8000, 16000, 32000, 48000):
            raise ValueError("Unsupported sample rate")
        vad = webrtcvad.Vad(3)
        samples_per_frame = int(sr * (frame_duration_ms / 1000.0))
        frames = []
        # convert to bytes for vad
        import numpy as np
        raw = data.astype(np.int16).tobytes()
        for offset in range(0, len(raw), samples_per_frame * 2):  # 2 bytes per sample
            chunk = raw[offset: offset + samples_per_frame * 2]
            if len(chunk) < samples_per_frame * 2:
                break
            frames.append(vad.is_speech(chunk, sr))
        return frames

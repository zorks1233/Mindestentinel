# vision plugin 
# plugins/vision_plugin.py
from pathlib import Path
from typing import Dict, Any
try:
    import cv2
    _HAS_CV2 = True
except Exception:
    _HAS_CV2 = False

class VisionPlugin:
    """Kleine Vision-Plugin-Implementierung mit OpenCV (optional)."""

    def __init__(self, device: int = 0, output_dir: str = "data/uploads/images"):
        self.device = int(device)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._cap = None

    def acquire_frame(self):
        if not _HAS_CV2:
            raise RuntimeError("OpenCV nicht installiert")
        if self._cap is None:
            self._cap = cv2.VideoCapture(self.device)
        ret, frame = self._cap.read()
        if not ret:
            raise RuntimeError("Frame acquisition failed")
        return frame

    def save_frame(self, frame, name: str = "frame.jpg") -> Dict[str, Any]:
        if not _HAS_CV2:
            raise RuntimeError("OpenCV nicht installiert")
        path = self.output_dir / name
        cv2.imwrite(str(path), frame)
        return {"path": str(path), "shape": getattr(frame, "shape", None)}

    def detect_edges(self, frame):
        if not _HAS_CV2:
            raise RuntimeError("OpenCV nicht installiert")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.Canny(gray, 50, 150)

    def release(self):
        if self._cap:
            self._cap.release()
            self._cap = None

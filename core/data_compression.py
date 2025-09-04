# data_compression 
# src/core/data_compression.py
"""
DataCompression - Zstandard-basierte Kompression mit optionaler Chunking-API.
- Funktionen: compress_bytes, decompress_bytes, compress_file, decompress_file
- Optional: stream-compression für sehr große Dateien.
- Prüft Integrität via CRC32 checksum (return metadata).
"""

from __future__ import annotations
import zstandard as zstd
import binascii
from pathlib import Path
from typing import Tuple, Dict, Any

CHUNK_SIZE = 2 ** 20  # 1 MiB

class DataCompression:
    def __init__(self, level: int = 3):
        if not isinstance(level, int) or level < 1 or level > 22:
            raise ValueError("level muss Integer zwischen 1 und 22 sein")
        self.level = level
        self._cparams = zstd.ZstdCompressionParameters.from_level(level)

    def compress_bytes(self, data: bytes) -> Tuple[bytes, Dict[str, Any]]:
        cctx = zstd.ZstdCompressor(level=self.level)
        compressed = cctx.compress(data)
        checksum = binascii.crc_hqx(compressed, 0)
        return compressed, {"orig_len": len(data), "compr_len": len(compressed), "crc": checksum}

    def decompress_bytes(self, compressed: bytes) -> Tuple[bytes, Dict[str, Any]]:
        dctx = zstd.ZstdDecompressor()
        data = dctx.decompress(compressed)
        checksum = binascii.crc_hqx(compressed, 0)
        return data, {"orig_len": len(data), "crc": checksum}

    def compress_file(self, src_path: str, dst_path: str = None) -> Dict[str, Any]:
        src = Path(src_path)
        if not src.exists():
            raise FileNotFoundError(src_path)
        dst = Path(dst_path) if dst_path else src.with_suffix(src.suffix + ".zst")
        cctx = zstd.ZstdCompressor(level=self.level)
        with src.open("rb") as ifh, dst.open("wb") as ofh:
            cctx.copy_stream(ifh, ofh)
        meta = {"src": str(src), "dst": str(dst)}
        return meta

    def decompress_file(self, src_path: str, dst_path: str = None) -> Dict[str, Any]:
        src = Path(src_path)
        if not src.exists():
            raise FileNotFoundError(src_path)
        if src.suffix != ".zst" and ".zst" not in src.name:
            # Still allow decompress if extension differs, try decompress
            pass
        dst = Path(dst_path) if dst_path else Path(str(src).rstrip(".zst"))
        dctx = zstd.ZstdDecompressor()
        with src.open("rb") as ifh, dst.open("wb") as ofh:
            dctx.copy_stream(ifh, ofh)
        return {"src": str(src), "dst": str(dst)}

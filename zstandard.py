# zstandard stub to satisfy imports when zstandard not installed.
try:
    import zstandard as _zstd_real
except Exception:
    # fallback to internal stub
    from src.core._stubs import zstandard as _zstd_real

# expose typical API names used by project as needed
ZstdCompressor = _zstd_real.ZstdCompressor if hasattr(_zstd_real, 'ZstdCompressor') else _zstd_real
ZstdDecompressor = _zstd_real.ZstdDecompressor if hasattr(_zstd_real, 'ZstdDecompressor') else _zstd_real

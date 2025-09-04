# compress_data 
#!/usr/bin/env python3
"""
Compress folder or file using zstandard wrapper from core/data_compression.py
"""
import argparse
from src.core.data_compression import DataCompression

def main():
    p = argparse.ArgumentParser()
    p.add_argument("src")
    p.add_argument("--dst", default=None)
    p.add_argument("--level", type=int, default=3)
    args = p.parse_args()
    dc = DataCompression(level=args.level)
    meta = dc.compress_file(args.src, args.dst)
    print("Compressed:", meta)

if __name__ == "__main__":
    main()

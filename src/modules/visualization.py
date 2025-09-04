# src/modules/visualization.py
"""
Visualization helpers: simple matplotlib-based plots for monitoring.
Optional dependency: matplotlib. If not installed, functions raise a clear error.
"""

from __future__ import annotations
from typing import Sequence, Any, Dict
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except Exception:
    _HAS_MPL = False

def plot_time_series(xs: Sequence[float], ys: Sequence[float], out_path: str, title: str = "timeseries", xlabel: str = "time", ylabel: str = "value") -> str:
    if not _HAS_MPL:
        raise RuntimeError("matplotlib fehlt. pip install matplotlib")
    if len(xs) != len(ys):
        raise ValueError("xs and ys must have same length")
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8,3))
    plt.plot(xs, ys)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(str(p))
    plt.close()
    return str(p)

def simple_table_image(rows: Sequence[Sequence[Any]], out_path: str, title: str = "table") -> str:
    if not _HAS_MPL:
        raise RuntimeError("matplotlib fehlt. pip install matplotlib")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, len(rows)*0.3 + 1.5))
    ax.axis('off')
    table = ax.table(cellText=rows, loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    return out_path

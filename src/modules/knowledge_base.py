# src/modules/knowledge_base.py
"""
VectorStore - FAISS-backed vector index with numpy fallback.
- Expected interface:
    vs = VectorStore(dimension)
    vs.add(item_id: str, embedding: np.ndarray, metadata: dict)
    vs.search(query_embedding: np.ndarray, topk: int) -> List[(id, score, metadata)]
- If faiss is available, use fast index; else use brute-force numpy.
"""

from __future__ import annotations
import os
import threading
import numpy as np
from typing import Any, Dict, List, Tuple, Optional

_HAS_FAISS = False
try:
    import faiss  # type: ignore
    _HAS_FAISS = True
except Exception:
    _HAS_FAISS = False

class VectorStore:
    def __init__(self, dimension: int, persist_dir: Optional[str] = None):
        self.dim = int(dimension)
        self._lock = threading.RLock()
        self._ids: List[str] = []
        self._embeddings: Optional[np.ndarray] = None  # shape (n, dim)
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self.persist_dir = persist_dir
        if _HAS_FAISS:
            self._index = faiss.IndexFlatIP(self.dim)  # inner product (use normalized for cosine)
        else:
            self._index = None

    def _ensure_embeddings(self):
        if self._embeddings is None:
            if not self._ids:
                self._embeddings = np.zeros((0, self.dim), dtype=np.float32)
            else:
                # should not happen, but keep safe
                self._embeddings = np.vstack([np.zeros((1, self.dim), dtype=np.float32) for _ in self._ids])

    def add(self, item_id: str, embedding: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> None:
        emb = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
        if emb.shape[1] != self.dim:
            raise ValueError(f"Embedding dimension mismatch: expected {self.dim}, got {emb.shape[1]}")
        with self._lock:
            if _HAS_FAISS:
                # normalize to use inner product as cosine if desired
                faiss.normalize_L2(emb)
                self._index.add(emb)
                self._ids.append(item_id)
            else:
                if self._embeddings is None:
                    self._embeddings = emb.copy()
                else:
                    self._embeddings = np.vstack([self._embeddings, emb])
                self._ids.append(item_id)
            self._metadata[item_id] = metadata or {}

    def search(self, query_embedding: np.ndarray, topk: int = 10) -> List[Tuple[str, float, Dict[str, Any]]]:
        q = np.asarray(query_embedding, dtype=np.float32).reshape(1, -1)
        if q.shape[1] != self.dim:
            raise ValueError("Query embedding has wrong dimension")
        with self._lock:
            if _HAS_FAISS:
                faiss.normalize_L2(q)
                D, I = self._index.search(q, topk)
                results = []
                for dist, idx in zip(D[0], I[0]):
                    if idx < 0 or idx >= len(self._ids):
                        continue
                    iid = self._ids[idx]
                    results.append((iid, float(dist), self._metadata.get(iid, {})))
                return results
            else:
                if self._embeddings is None or self._embeddings.shape[0] == 0:
                    return []
                # cosine similarity
                # normalize
                emb = self._embeddings
                qn = q / np.linalg.norm(q, axis=1, keepdims=True)
                en = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-12)
                sims = (en @ qn.T).reshape(-1)
                top_idx = np.argsort(-sims)[:topk]
                results = []
                for idx in top_idx:
                    iid = self._ids[int(idx)]
                    results.append((iid, float(sims[int(idx)]), self._metadata.get(iid, {})))
                return results

    def count(self) -> int:
        with self._lock:
            return len(self._ids)

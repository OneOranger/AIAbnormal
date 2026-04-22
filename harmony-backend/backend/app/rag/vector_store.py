"""轻量 RAG — sentence-transformers + 内存向量索引(演示足够)。
生产请换成 FAISS persistent index。
"""
import numpy as np
from typing import List, Tuple
from threading import RLock
from loguru import logger


class InMemoryVectorStore:
    def __init__(self):
        self._docs: List[dict] = []
        self._vectors: np.ndarray | None = None
        self._lock = RLock()

    def add(self, docs: List[dict], vectors: np.ndarray):
        with self._lock:
            self._docs.extend(docs)
            if self._vectors is None:
                self._vectors = vectors
            else:
                self._vectors = np.vstack([self._vectors, vectors])
        logger.info(f"📚 RAG: indexed {len(docs)} docs, total={len(self._docs)}")

    def search(self, query_vec: np.ndarray, top_k: int = 5) -> List[Tuple[dict, float]]:
        if self._vectors is None or len(self._docs) == 0:
            return []
        q = query_vec / (np.linalg.norm(query_vec) + 1e-8)
        m = self._vectors / (np.linalg.norm(self._vectors, axis=1, keepdims=True) + 1e-8)
        sims = m @ q
        idx = np.argsort(-sims)[:top_k]
        return [(self._docs[i], float(sims[i])) for i in idx]


_store: InMemoryVectorStore | None = None


def get_store() -> InMemoryVectorStore:
    global _store
    if _store is None:
        _store = InMemoryVectorStore()
    return _store


def upsert_documents(docs: List[dict]) -> int:
    """对外暴露的文档入库接口(供反馈消费器调用)。"""
    try:
        from app.ml.trainers.embedding import get_embedder
        emb = get_embedder()
        texts = [d.get("title", "") + " " + d.get("content", "") for d in docs]
        vecs = emb.encode(texts)
        get_store().add(docs, vecs)
        return len(docs)
    except Exception as e:
        logger.warning(f"RAG upsert skipped: {e}")
        return 0

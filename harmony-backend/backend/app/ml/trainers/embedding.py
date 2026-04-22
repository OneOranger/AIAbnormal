"""文本 embedding 模型 — 用 sentence-transformers 多语言模型(首次自动下载)。
用于 RAG 知识库 + 商户名/备注语义检索。
"""
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from loguru import logger

DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"  # ≈120MB,中英双语


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    logger.info(f"📥 Loading embedding model: {DEFAULT_MODEL}")
    m = SentenceTransformer(DEFAULT_MODEL)
    logger.info(f"✅ Embedding model ready, dim={m.get_sentence_embedding_dimension()}")
    return m

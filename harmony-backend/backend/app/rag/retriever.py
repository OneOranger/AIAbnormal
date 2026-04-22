"""RAG 检索接口 — embed query + topK,Agent 调用。"""
from typing import List, Dict, Any
from loguru import logger
from .vector_store import get_store

# 预置案例(可扩展为从文件加载)
SEED_CASES = [
    {"id": "case-1", "title": "ATO 经典案例 — 多国登录后大额支付",
     "content": "用户在 11 分钟内跨越 CN→TR→RU,设备指纹突变,随即对新收款方进行 8500 USD 跨境转账。处置:立即拦截 + 强制 2FA + 30 天观察。",
     "type": "case_history"},
    {"id": "case-2", "title": "钱骡账户特征",
     "content": "账户 30 天内进出账比 0.95,日均 12 笔小额转入后聚合大额转出,关联多个新注册商户。处置:冻结 + AML 上报。",
     "type": "case_history"},
    {"id": "case-3", "title": "对账时序差异 SOP",
     "content": "Stripe 渠道结算 T+1,内部已记账但渠道未到账时,系统自动延后 2 天重对账;若 T+3 仍未匹配,推送对账员核查。",
     "type": "rule_doc"},
    {"id": "case-4", "title": "深度伪造活体检测",
     "content": "kyc.deepfake_score>0.7 时直接拒绝开户;若已通过历史 KYC,则触发二次活体 + 视频客服核身。",
     "type": "regulation"},
    {"id": "case-5", "title": "团伙图谱判定标准",
     "content": "同 IP /24 段聚集>=5 个账户、共享设备指纹>=3 个、2 跳内有已确认欺诈节点 → 判定团伙。批量打标 watchlist。",
     "type": "fraud_pattern"},
]


def retrieve(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """对 query 做 embedding + 向量检索,返回相关文档片段。
    如果 embedder 加载失败(如离线),返回关键词匹配降级结果。
    """
    try:
        from app.ml.trainers.embedding import get_embedder
        emb = get_embedder()
        q_vec = emb.encode([query])[0]
        results = get_store().search(q_vec, top_k=top_k)
        return [{"doc": d, "score": s} for d, s in results]
    except Exception as e:
        logger.warning(f"RAG embed failed, fallback to keyword: {e}")
        kw = query.lower()
        scored = []
        for d in SEED_CASES:
            score = sum(1 for w in kw.split() if w in d["content"].lower())
            if score > 0:
                scored.append({"doc": d, "score": float(score)})
        scored.sort(key=lambda x: -x["score"])
        return scored[:top_k]


def index_seed_docs():
    """把 SEED_CASES 写入向量库(bootstrap 调用)。"""
    try:
        from app.ml.trainers.embedding import get_embedder
        emb = get_embedder()
        texts = [d["title"] + " " + d["content"] for d in SEED_CASES]
        vecs = emb.encode(texts)
        get_store().add(SEED_CASES, vecs)
    except Exception as e:
        logger.warning(f"RAG seed index skipped: {e}")

"""处置策略 + 反馈路由 — feedback 提交后自动触发 KnowledgeAgent 异步消费。"""
from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from app.schemas.pipeline import DispositionPolicy, FeedbackRecord
from app.storage.bootstrap import policies_repo, feedback_repo
from app.tasks.feedback_consumer import consume_feedback

router = APIRouter()


class ToggleReq(BaseModel):
    enabled: bool


@router.get("/policies", response_model=List[DispositionPolicy])
async def list_policies():
    return policies_repo.list_all()


@router.post("/policies")
async def upsert_policy(p: dict):
    if "id" not in p:
        p["id"] = f"pol-{int(__import__('time').time())}"
    obj = DispositionPolicy(**p)
    policies_repo.upsert(obj)
    return {"ok": True, "id": obj.id}


@router.post("/policies/{policy_id}/toggle")
async def toggle_policy(policy_id: str, req: ToggleReq):
    updated = policies_repo.patch(policy_id, {"enabled": req.enabled})
    return {"ok": bool(updated)}


@router.get("/feedback", response_model=List[FeedbackRecord])
async def list_feedback(type: Optional[str] = None, reviewer: Optional[str] = None):
    items = feedback_repo.list_all()
    if type and type != "all":
        items = [f for f in items if f.feedbackType == type]
    if reviewer and reviewer != "all":
        items = [f for f in items if reviewer.lower() in f.reviewer.lower()]
    return items


@router.post("/feedback")
async def submit_feedback(fb: dict, bg: BackgroundTasks):
    if "id" not in fb:
        fb["id"] = f"fb-{int(__import__('time').time())}"
    obj = FeedbackRecord(**fb)
    feedback_repo.append_record(obj)
    # 文档 §6.1 阶段 9: 异步消费(入 RAG / 训练样本池 / 规则建议)
    bg.add_task(consume_feedback, obj.model_dump())
    return {"ok": True, "id": obj.id}

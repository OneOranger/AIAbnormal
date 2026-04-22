"""规则引擎路由。"""
from typing import Optional, List
from fastapi import APIRouter
from pydantic import BaseModel
from app.schemas.pipeline import RiskRule
from app.storage.bootstrap import rules_repo

router = APIRouter()


class ToggleReq(BaseModel):
    enabled: bool


@router.get("", response_model=List[RiskRule])
async def list_rules(category: Optional[str] = None, status: Optional[str] = None,
                     search: Optional[str] = None):
    items = rules_repo.list_all()
    if category and category != "all":
        items = [r for r in items if r.category == category]
    if status and status != "all":
        items = [r for r in items if r.status == status]
    if search:
        s = search.lower()
        items = [r for r in items if s in r.name.lower() or s in r.code.lower()]
    return items


@router.post("")
async def upsert_rule(rule: dict):
    if "id" not in rule:
        rule["id"] = f"rule-{int(__import__('time').time())}"
    obj = RiskRule(**rule)
    rules_repo.upsert(obj)
    return {"ok": True, "id": obj.id}


@router.post("/{rule_id}/toggle")
async def toggle_rule(rule_id: str, req: ToggleReq):
    new_status = "active" if req.enabled else "disabled"
    updated = rules_repo.patch(rule_id, {"status": new_status})
    return {"ok": bool(updated)}

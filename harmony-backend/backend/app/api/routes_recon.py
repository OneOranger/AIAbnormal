"""对账路由。"""
from typing import Optional, List
from fastapi import APIRouter
from app.schemas.recon import ReconRecord
from app.storage import recon_repo

router = APIRouter()


@router.get("", response_model=List[ReconRecord])
async def list_recon(status: Optional[str] = None, channel: Optional[str] = None,
                     search: Optional[str] = None):
    items = recon_repo.list_all()
    if status and status != "all":
        items = [r for r in items if r.status == status]
    if channel and channel != "all":
        items = [r for r in items if r.channel == channel]
    if search:
        s = search.lower()
        items = [r for r in items if s in r.internalRef.lower() or s in r.channelRef.lower()]
    return items

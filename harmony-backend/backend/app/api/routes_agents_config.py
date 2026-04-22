"""Agent 配置 + 知识库路由。"""
from typing import List
from fastapi import APIRouter
from app.schemas.pipeline import AgentConfig, KnowledgeBase
from app.storage.bootstrap import agents_repo, kbs_repo
from app.llm import get_llm, LLMMessage

router = APIRouter()


@router.get("", response_model=List[AgentConfig])
async def list_agents():
    return agents_repo.list_all()


@router.get("/kb", response_model=List[KnowledgeBase])
async def list_kbs():
    return kbs_repo.list_all()


@router.patch("/{agent_id}")
async def update_agent(agent_id: str, patch: dict):
    updated = agents_repo.patch(agent_id, patch)
    return {"ok": bool(updated)}


@router.post("/{agent_id}/test")
async def test_agent(agent_id: str, body: dict):
    """Playground — 用真实 LLM 跑一遍 system prompt + 用户输入。"""
    import time
    a = agents_repo.get(agent_id)
    if not a:
        return {"ok": False, "error": "agent not found"}
    user_input = body.get("input", "")
    t0 = time.time()
    resp = await get_llm().chat(
        messages=[LLMMessage("system", a.systemPrompt), LLMMessage("user", user_input)],
        temperature=a.temperature, max_tokens=a.maxTokens,
    )
    return {
        "ok": True, "output": resp.content,
        "tokens": resp.tokens_in + resp.tokens_out,
        "latencyMs": int((time.time() - t0) * 1000),
    }

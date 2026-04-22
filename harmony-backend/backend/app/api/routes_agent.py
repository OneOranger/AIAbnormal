"""Agent Chat 路由 — 支持流式 SSE + 非流式。"""
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.llm import get_llm, LLMMessage

router = APIRouter()

SYSTEM_PROMPT = (
    "你是支付风控 AI Agent,帮助用户分析订单根因、对账差异、欺诈趋势。"
    "回答简洁、结构化,使用 markdown。如果用户问『分析订单 XXX』可以模拟根因分析输出。"
)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    msgs = [LLMMessage("system", SYSTEM_PROMPT)] + [
        LLMMessage(m.role, m.content) for m in req.messages
    ]
    resp = await get_llm().chat(messages=msgs)
    return ChatResponse(content=resp.content)


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """SSE 流式 — 兼容 OpenAI 协议格式。"""
    msgs = [LLMMessage("system", SYSTEM_PROMPT)] + [
        LLMMessage(m.role, m.content) for m in req.messages
    ]

    async def gen():
        try:
            async for chunk in get_llm().chat_stream(messages=msgs):
                payload = {"choices": [{"delta": {"content": chunk}}]}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")

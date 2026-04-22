"""通用 Agent 基类 — 支持 Specialist / Triage / Knowledge / Action / Report / Supervisor 多种角色。

每个 Agent 共用 LLM 调用骨架,区别只在:
- system prompt(领域知识)
- 输入构造(传哪些上下文)
- 输出解析(关心哪些字段)
"""
import json
from typing import Dict, Any, List, Optional
from loguru import logger

from app.llm import get_llm, LLMMessage
from app.prompts import load as load_prompt
from app.rag import retrieve as rag_retrieve
from app.config import settings


def _safe_parse_json(content: str) -> Dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        # 去掉 markdown 代码块
        content = content.split("```", 2)[1]
        if content.lstrip().lower().startswith("json"):
            content = content.split("\n", 1)[1] if "\n" in content else content
    try:
        return json.loads(content)
    except Exception:
        return {"summary": content}


class BaseAgent:
    """所有 Agent 的基类。"""

    kind: str = "base"  # specialist | triage | knowledge | action | report | supervisor

    def __init__(self, name: str, prompt_name: str, category: str = "all"):
        self.name = name
        self.prompt_name = prompt_name
        self.category = category

    async def _call_llm(self, user_prompt: str, temperature: Optional[float] = None) -> Dict[str, Any]:
        sys_prompt = load_prompt(self.prompt_name)
        try:
            resp = await get_llm().chat(
                messages=[LLMMessage("system", sys_prompt), LLMMessage("user", user_prompt)],
                temperature=temperature if temperature is not None else settings.AGENT_DEFAULT_TEMPERATURE,
                max_tokens=settings.AGENT_MAX_TOKENS,
            )
            parsed = _safe_parse_json(resp.content)
            return {
                "agent": self.name,
                "kind": self.kind,
                "category": self.category,
                "result": parsed,
                "raw": resp.content,
                "tokens": resp.tokens_in + resp.tokens_out,
                "latency_ms": resp.latency_ms,
                "provider": resp.provider,
            }
        except Exception as e:
            logger.exception(f"Agent {self.name} failed")
            return {"agent": self.name, "kind": self.kind, "category": self.category, "error": str(e)}


# ============================================================
# 1. SpecialistAgent — Fraud / Behavior / Recon / Chargeback / Compliance
# ============================================================
class SpecialistAgent(BaseAgent):
    kind = "specialist"

    async def run(self, order: Dict[str, Any], rule_hits: List[Dict[str, Any]],
                  ml_scores: Dict[str, Any],
                  rag_hits: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        if rag_hits is None:
            rag_query = f"{order.get('primaryCategory')} {' '.join(order.get('subTypes', []))}"
            rag_hits = rag_retrieve(rag_query, top_k=3)
        rag_text = "\n".join(f"- [{h['doc']['title']}] {h['doc']['content']}" for h in rag_hits) or "(无)"

        user_prompt = (
            f"## 订单上下文\n```json\n{json.dumps({k: order.get(k) for k in ['orderNo','amount','currency','channel','ipCountry','device','userId','merchantName','primaryCategory','subTypes']}, ensure_ascii=False)}\n```\n\n"
            f"## 规则命中 ({len(rule_hits)} 条)\n{json.dumps(rule_hits, ensure_ascii=False)}\n\n"
            f"## ML 评分\n{json.dumps(ml_scores, ensure_ascii=False)}\n\n"
            f"## RAG 检索片段\n{rag_text}\n\n"
            f"请输出 JSON 结论。"
        )
        return await self._call_llm(user_prompt)


# ============================================================
# 2. TriageAgent — 8大类多标签打标
# ============================================================
class TriageAgent(BaseAgent):
    kind = "triage"

    def __init__(self):
        super().__init__("triage_agent", "triage", "all")

    async def run(self, order: Dict[str, Any], rule_hits: List[Dict[str, Any]],
                  ml_scores: Dict[str, Any]) -> Dict[str, Any]:
        user_prompt = (
            f"## 待分诊订单\n"
            f"金额: {order.get('amount')} {order.get('currency')} | 渠道: {order.get('channel')} | "
            f"国家: {order.get('ipCountry')} | 商户: {order.get('merchantName')}\n\n"
            f"## 规则命中\n{json.dumps([{'code':h.get('code'),'name':h.get('name'),'category':h.get('category'),'scoreDelta':h.get('score_delta')} for h in rule_hits], ensure_ascii=False)}\n\n"
            f"## ML 评分\n{json.dumps(ml_scores, ensure_ascii=False)}\n\n"
            f"请按 8 大类做分诊,输出 JSON。"
        )
        return await self._call_llm(user_prompt, temperature=0.1)


# ============================================================
# 3. KnowledgeAgent — RAG 检索
# ============================================================
class KnowledgeAgent(BaseAgent):
    kind = "knowledge"

    def __init__(self):
        super().__init__("knowledge_agent", "knowledge", "all")

    async def run(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        hits = rag_retrieve(query, top_k=top_k)
        # 不必走 LLM,直接组装结果(节省 token)
        return {
            "agent": self.name,
            "kind": self.kind,
            "category": self.category,
            "result": {
                "query": query,
                "hits": [
                    {
                        "kb": h.get("doc", {}).get("kb", "kb-1"),
                        "title": h.get("doc", {}).get("title", ""),
                        "snippet": h.get("doc", {}).get("content", ""),
                        "score": h.get("score", 0.0),
                        "source": h.get("doc", {}).get("id", ""),
                    } for h in hits
                ],
                "summary": f"检索到 {len(hits)} 条相关知识片段",
            },
            "tokens": 0,
            "latency_ms": 0,
            "provider": "local-rag",
        }


# ============================================================
# 4. ActionAgent — 处置二次校验
# ============================================================
class ActionAgent(BaseAgent):
    kind = "action"

    def __init__(self):
        super().__init__("action_agent", "action", "all")

    async def run(self, order: Dict[str, Any], policy: Optional[Dict[str, Any]],
                  agent_decision: Dict[str, Any]) -> Dict[str, Any]:
        if not policy:
            return {
                "agent": self.name, "kind": self.kind, "category": self.category,
                "result": {
                    "validated": False, "primary_action": "review",
                    "secondary_actions": [], "execution_mode": "human_required",
                    "skip_reason": "未匹配到处置策略,转人工",
                    "notify_channels": ["im"],
                    "audit_summary": "无策略命中,降级人工复核",
                },
                "tokens": 0, "latency_ms": 0, "provider": "rule-based",
            }
        user_prompt = (
            f"## 订单\n金额 {order.get('amount')} {order.get('currency')},商户 {order.get('merchantName')},用户 {order.get('userId')}\n\n"
            f"## 命中策略\n{json.dumps(policy, ensure_ascii=False)}\n\n"
            f"## Agent 决策\n{json.dumps(agent_decision, ensure_ascii=False)}\n\n"
            f"请做二次校验后输出 JSON 执行计划。"
        )
        return await self._call_llm(user_prompt, temperature=0.1)


# ============================================================
# 5. ReportAgent — 自然语言报告
# ============================================================
class ReportAgent(BaseAgent):
    kind = "report"

    def __init__(self):
        super().__init__("report_agent", "report", "all")

    async def run(self, order: Dict[str, Any], final_decision: Dict[str, Any],
                  agent_traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        user_prompt = (
            f"## 订单 {order.get('orderNo')}\n"
            f"{json.dumps({k: order.get(k) for k in ['amount','currency','channel','ipCountry','merchantName']}, ensure_ascii=False)}\n\n"
            f"## 最终结论\n{json.dumps(final_decision, ensure_ascii=False)}\n\n"
            f"## 各 Agent 推理摘要\n{json.dumps([{a.get('agent'): a.get('result', {}).get('root_cause') or a.get('result', {}).get('summary')} for a in agent_traces if 'error' not in a], ensure_ascii=False)}\n\n"
            f"请按报告模板生成 markdown 分析报告。返回 JSON: {{\"report_md\":\"...\"}}"
        )
        return await self._call_llm(user_prompt, temperature=0.3)


# ============================================================
# 6. SupervisorAgent — 总调度
# ============================================================
class SupervisorAgent(BaseAgent):
    kind = "supervisor"

    def __init__(self):
        super().__init__("supervisor_agent", "supervisor", "all")

    async def merge(self, triage: Dict[str, Any],
                    specialist_results: List[Dict[str, Any]],
                    knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """聚合多 Agent 结论 + 幻觉校验,产出最终决策。"""
        valid_specialists = [s for s in specialist_results if "error" not in s and isinstance(s.get("result"), dict)]
        user_prompt = (
            f"## Triage 分诊\n{json.dumps(triage.get('result', {}), ensure_ascii=False)}\n\n"
            f"## 各 Specialist 推理\n{json.dumps([s.get('result', {}) for s in valid_specialists], ensure_ascii=False)}\n\n"
            f"## RAG 检索\n{json.dumps(knowledge.get('result', {}).get('hits', []), ensure_ascii=False)}\n\n"
            f"请汇总产出最终结论 JSON。所有结论必须基于以上输入,不要编造。"
        )
        return await self._call_llm(user_prompt, temperature=0.15)

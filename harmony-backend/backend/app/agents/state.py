"""LangGraph 多 Agent 编排状态。"""
from typing import TypedDict, List, Dict, Any, Optional


class PipelineState(TypedDict, total=False):
    # 输入
    order_id: str
    order_dict: Dict[str, Any]
    # 阶段产物
    rule_hits: List[Dict[str, Any]]
    ml_scores: Dict[str, Any]
    rag_context: List[Dict[str, Any]]
    # Agent 输出
    agent_results: Dict[str, Dict[str, Any]]   # {agent_name: result}
    final_decision: Optional[Dict[str, Any]]
    # Trace
    trace: List[Dict[str, Any]]
    error: Optional[str]

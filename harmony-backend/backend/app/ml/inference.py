"""统一 ML 推理接口 — 委托给 serving/ensemble 实现文档 §3.3 完整融合策略。"""
from typing import Dict, Any
from app.schemas.order import AnomalyOrder
from app.ml.serving.ensemble import ensemble_score


def score_order(order: AnomalyOrder, rule_score_delta: int = 0) -> Dict[str, Any]:
    """对一个订单做 5 模型融合评分,返回完整 trace。

    返回字段:
      fused_score      最终融合分 (0-100)
      ml_score         纯 ML 部分(无规则加成)
      rule_bonus       规则贡献(cap +30)
      model_scores     各模型分数 + 权重
      chargeback_prob  拒付概率(单独输出)
      top_features     Top5 特征重要性
      active_models    实际参与融合的模型数
    """
    return ensemble_score(order, rule_score_delta=rule_score_delta)

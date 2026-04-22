"""规则引擎主入口。从 rules_repo 读取活跃规则,逐一评估,产出命中列表 + score 加成。"""
from dataclasses import dataclass
from typing import Dict, List, Any
from loguru import logger

from app.schemas.pipeline import RiskRule
from app.storage.bootstrap import rules_repo
from .dsl import evaluate


@dataclass
class RuleHit:
    rule_id: str
    code: str
    name: str
    action: str
    score_delta: int
    category: str


class RuleEngine:
    def evaluate(self, ctx: Dict[str, Any]) -> List[RuleHit]:
        hits: List[RuleHit] = []
        rules = [r for r in rules_repo.list_all() if r.status in ("active", "shadow")]
        rules.sort(key=lambda r: r.priority, reverse=True)
        for rule in rules:
            try:
                if evaluate(rule.condition, ctx):
                    hits.append(RuleHit(
                        rule_id=rule.id,
                        code=rule.code,
                        name=rule.name,
                        action=rule.action,
                        score_delta=rule.scoreDelta,
                        category=rule.category,
                    ))
            except Exception as e:
                logger.debug(f"Rule {rule.code} skip: {e}")
        return hits


_engine: RuleEngine | None = None


def get_engine() -> RuleEngine:
    global _engine
    if _engine is None:
        _engine = RuleEngine()
    return _engine

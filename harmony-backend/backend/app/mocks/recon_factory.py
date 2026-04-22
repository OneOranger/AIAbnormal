"""对账 Mock 工厂。"""
import random
from datetime import datetime, timedelta
from typing import List
from app.config import settings
from app.schemas.recon import ReconRecord, ReconStatus, ReconDiffType
from app.schemas.order import PaymentChannel

CHANNELS: List[PaymentChannel] = [
    "alipay", "wechat", "unionpay", "visa", "mastercard", "stripe", "paypal",
]
DIFF_TYPES: List[ReconDiffType] = [
    "timing", "amount", "fx", "fee", "duplicate", "missing", "partial", "format",
]
ROOT_CAUSES = {
    "timing": "渠道结算 T+1,内部记账已完成,等待对账窗口",
    "amount": "金额尾数差异,疑似分账规则未同步",
    "fx": "汇率差导致差异,需计入汇兑损益",
    "fee": "渠道手续费未同步入账",
    "duplicate": "渠道重复推送回调,已识别为重复条目",
    "missing": "渠道缺失对账明细,已发起补单查询",
    "partial": "拆分支付,需合并对账",
    "format": "对账文件格式异常,字段映射偏移",
}
AI_SUGGESTIONS = {
    "timing": "T+2 重新对账,自动闭环",
    "amount": "生成调整凭证 + 推送财务复核",
    "fx": "按交易日中间价补差,计入 6603 汇兑损益",
    "fee": "自动补提手续费分录",
    "duplicate": "标记重复并冲销,通知渠道核查",
    "missing": "调用渠道补单 API + 推送对账员",
    "partial": "聚合订单后重新匹配",
    "format": "应用历史模板自动转换字段",
}


def generate_recon(count: int = None, seed: int = None) -> List[ReconRecord]:
    n = count or settings.MOCK_RECON_COUNT
    rng = random.Random((seed or settings.RANDOM_SEED) + 7)
    records: List[ReconRecord] = []
    base = datetime.utcnow()

    for i in range(n):
        ch = rng.choice(CHANNELS)
        internal = round(rng.uniform(50, 50000), 2)
        # 70% 匹配,30% 有差异
        if rng.random() < 0.7:
            channel_amt = internal
            status: ReconStatus = "matched"
            diff = 0.0
            diff_type = None
            root = None
            sug = None
            confidence = round(rng.uniform(0.96, 1.0), 3)
        else:
            diff_type = rng.choice(DIFF_TYPES)
            if diff_type == "duplicate":
                channel_amt = internal * 2
            elif diff_type == "missing":
                channel_amt = 0.0
            elif diff_type == "fee":
                channel_amt = internal - rng.uniform(0.5, 50)
            elif diff_type == "fx":
                channel_amt = internal * rng.uniform(0.985, 1.012)
            elif diff_type == "amount":
                channel_amt = internal + rng.uniform(-200, 200)
            elif diff_type == "partial":
                channel_amt = internal * rng.uniform(0.3, 0.7)
            else:
                channel_amt = internal + rng.uniform(-5, 5)
            channel_amt = round(channel_amt, 2)
            diff = round(channel_amt - internal, 2)
            status = "missing" if diff_type == "missing" else (
                "duplicate" if diff_type == "duplicate" else "discrepancy"
            )
            root = ROOT_CAUSES[diff_type]
            sug = AI_SUGGESTIONS[diff_type]
            confidence = round(rng.uniform(0.55, 0.92), 3)

        date = (base - timedelta(days=rng.randint(0, 14))).strftime("%Y-%m-%d")
        records.append(ReconRecord(
            id=f"rec-{i + 1}",
            date=date,
            internalRef=f"INT{rng.randint(10000000, 99999999)}",
            channelRef=f"{ch.upper()[:3]}{rng.randint(10000000, 99999999)}",
            internalAmount=internal,
            channelAmount=channel_amt,
            diff=diff,
            channel=ch,
            status=status,
            diffType=diff_type,
            rootCause=root,
            aiSuggestion=sug,
            matchedConfidence=confidence,
        ))

    records.sort(key=lambda r: r.date, reverse=True)
    return records

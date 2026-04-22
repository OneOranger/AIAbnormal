"""异常订单 Mock 工厂 — 与前端 mock-data.ts 输出风格一致。"""
import random
import hashlib
from datetime import datetime, timedelta
from typing import List
from app.config import settings
from app.schemas.order import (
    AnomalyOrder, Evidence, AISuggestion,
    AnomalyCategory, RiskLevel, OrderStatus, PaymentChannel,
)

CATEGORIES: List[AnomalyCategory] = [
    "fraud", "behavioral", "system", "reconciliation",
    "chargeback", "merchant", "user", "compliance",
]
CHANNELS: List[PaymentChannel] = [
    "alipay", "wechat", "unionpay", "visa", "mastercard",
    "stripe", "paypal", "applepay", "bank_transfer",
]
COUNTRIES = ["CN", "US", "RU", "NG", "BR", "VN", "PH", "TR", "ID", "MY"]
HIGH_RISK = {"RU", "NG", "PH", "TR"}
DEVICES = [
    "iPhone 15 Pro", "Pixel 8", "Xiaomi 14", "Samsung S24",
    "Huawei Mate60", "Emulator-X86", "Headless Chrome",
]
FIRST = ["李", "王", "张", "刘", "陈", "杨", "黄", "Wang", "Smith", "Garcia", "Müller"]
LAST = ["明", "伟", "芳", "娜", "强", "磊", "敏", "静", "Lee", "Chen", "Patel"]
MERCHANTS = [
    "云耀数码旗舰店", "悦购国际", "极速优选", "ShopSmart Inc",
    "GameTopUp Pro", "云端会员订阅", "海外购精选", "Quick Recharge",
    "LuxLife Boutique", "盛世彩金平台", "CryptoFastPay", "EduOnline 课程",
]

SUB_TYPES_MAP = {
    "fraud": ["合成身份欺诈", "账户接管(ATO)", "新账户欺诈", "钱骡欺诈", "深度伪造", "信用卡盗刷", "BEC邮件欺诈"],
    "behavioral": ["突发大额", "高频小额刷单", "夜间大额", "IP跳变", "设备跳变", "支付方式突变"],
    "system": ["重复支付", "回调延迟丢失", "API集成故障", "状态同步失败"],
    "reconciliation": ["时序差异", "缺失交易", "重复条目", "汇率差", "手续费未同步", "结算延迟"],
    "chargeback": ["欺诈拒付", "友好欺诈", "商品服务不符", "未收到货"],
    "merchant": ["高退款率", "高争议率", "高风险行业MCC"],
    "user": ["误操作重复下单", "财务困难拒付"],
    "compliance": ["OFAC黑名单", "AML大额可疑", "高风险行业跨境"],
}

EVIDENCE_TEMPLATES = {
    "device": ("设备指纹首次出现", "{device} 在该用户名下首次出现,且历史指纹与本次差异 73%"),
    "ip": ("IP 段集群命中", "IP 落在 /24 段已出现 7 个欺诈账户,关联度 0.86"),
    "behavior": ("行为序列异常", "登录→改密→大额支付,3 步耗时 12s,远低于人类基线"),
    "pattern": ("交易频率异常", "5 分钟内同 SKU 下单 8 次,触发刷单模式"),
    "rule": ("风控规则命中", "命中 R-FRD-003 (Headless 浏览器+大额),score+35"),
    "graph": ("团伙图谱命中", "与 12 个已标欺诈账户在 2 跳内连通,中心度 0.42"),
    "ml": ("ML 模型高分", "fraud-xgb-v2.4 输出 0.92,IsolationForest 离群分 -0.18"),
}


def _level(score: int) -> RiskLevel:
    if score >= 85: return "critical"
    if score >= 65: return "high"
    if score >= 40: return "medium"
    return "low"


def _status_for(score: int, rng: random.Random) -> OrderStatus:
    if score >= 85: return rng.choice(["intercepted", "intercepted", "pending_review", "escalated"])
    if score >= 65: return rng.choice(["pending_review", "intercepted", "observing"])
    if score >= 40: return rng.choice(["observing", "released", "pending_review"])
    return rng.choice(["released", "resolved"])


def _make_evidence(rng: random.Random, n: int, idx: int) -> List[Evidence]:
    types = list(EVIDENCE_TEMPLATES.keys())
    rng.shuffle(types)
    out = []
    for i, t in enumerate(types[:n]):
        label, detail = EVIDENCE_TEMPLATES[t]
        device_choice = rng.choice(DEVICES)
        out.append(Evidence(
            id=f"ev-{idx}-{i}",
            type=t,  # type: ignore
            label=label,
            detail=detail.format(device=device_choice),
            weight=round(rng.uniform(0.35, 0.95), 2),
        ))
    return out


def _make_suggestions(score: int, rng: random.Random, amount: float) -> List[AISuggestion]:
    if score >= 85:
        return [
            AISuggestion(action="intercept", label="立即拦截",
                         confidence=rng.randint(88, 98),
                         rationale="多重高权证据 + ML 高分,拦截可避免实际损失",
                         estimatedLoss=round(amount * 0.85, 2)),
            AISuggestion(action="auto_refund", label="自动退款",
                         confidence=rng.randint(70, 85),
                         rationale="若已扣款,建议立即原路退款减少投诉"),
        ]
    if score >= 65:
        return [
            AISuggestion(action="review", label="人工复核",
                         confidence=rng.randint(72, 88),
                         rationale="证据偏强但存在不确定性,建议 30 分钟内人工二次判断"),
            AISuggestion(action="observe", label="加入观察名单",
                         confidence=rng.randint(60, 78),
                         rationale="保留交易但 30 天内重点跟踪同用户后续行为"),
        ]
    if score >= 40:
        return [
            AISuggestion(action="observe", label="观察",
                         confidence=rng.randint(60, 75),
                         rationale="弱信号,建议观察 7 天"),
        ]
    return [
        AISuggestion(action="release", label="放行",
                     confidence=rng.randint(80, 95),
                     rationale="低风险,无需干预"),
    ]


def _root_cause(category: AnomalyCategory, sub_types: List[str]) -> str:
    return f"{category} / {sub_types[0] if sub_types else '未知子类'}"


def _rca_summary(category: AnomalyCategory, score: int, evidences: List[Evidence]) -> str:
    head = f"AI 综合判断本订单为 **{category}** 类异常,风险分 {score}。"
    body = " 主要证据: " + "; ".join(f"{e.label}(权重{e.weight})" for e in evidences[:3]) + "。"
    return head + body


def generate_orders(count: int = None, seed: int = None) -> List[AnomalyOrder]:
    n = count or settings.MOCK_ORDER_COUNT
    rng = random.Random(seed or settings.RANDOM_SEED)
    orders: List[AnomalyOrder] = []
    base_time = datetime.utcnow()

    for i in range(n):
        category = rng.choices(
            CATEGORIES,
            weights=[35, 22, 8, 14, 9, 5, 3, 4],  # 欺诈最多
        )[0]
        sub_pool = SUB_TYPES_MAP[category]
        sub_types = rng.sample(sub_pool, k=min(rng.randint(1, 3), len(sub_pool)))

        score = rng.randint(15, 99)
        # 欺诈/合规倾向高分
        if category in ("fraud", "compliance"):
            score = max(score, rng.randint(55, 99))

        amount = round(rng.uniform(15, 95000), 2)
        currency = rng.choices(["CNY", "USD", "EUR"], weights=[70, 25, 5])[0]
        country = rng.choice(COUNTRIES)
        if category == "fraud":
            country = rng.choices(COUNTRIES, weights=[20, 10, 18, 16, 8, 8, 8, 6, 3, 3])[0]

        device = rng.choice(DEVICES)
        ts = base_time - timedelta(minutes=rng.randint(0, 60 * 24 * 30))
        n_evidence = rng.randint(2, 6)
        evidences = _make_evidence(rng, n_evidence, i)
        suggestions = _make_suggestions(score, rng, amount)
        user_id = f"U{rng.randint(100000, 999999)}"
        user_name = rng.choice(FIRST) + rng.choice(LAST)

        order = AnomalyOrder(
            id=f"ord-{i + 1}",
            orderNo=f"PAY{ts.strftime('%Y%m%d')}{1000 + i:06d}",
            createdAt=ts.isoformat() + "Z",
            amount=amount,
            currency=currency,
            channel=rng.choice(CHANNELS),
            merchantName=rng.choice(MERCHANTS),
            merchantId=f"M{rng.randint(10000, 99999)}",
            userId=user_id,
            userName=user_name,
            userIp=f"{rng.randint(1, 223)}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(0, 255)}",
            ipCountry=country,
            device=device,
            deviceFingerprint=hashlib.md5(f"{user_id}-{device}-{i}".encode()).hexdigest()[:16],
            status=_status_for(score, rng),
            primaryCategory=category,
            subTypes=sub_types,
            riskScore=score,
            riskLevel=_level(score),
            confidence=rng.randint(60, 98),
            tags=sub_types + ([country] if country in HIGH_RISK else []),
            evidence=evidences,
            suggestions=suggestions,
            rootCause=_root_cause(category, sub_types),
            rcaSummary=_rca_summary(category, score, evidences),
            similarCases=rng.randint(3, 87),
        )
        orders.append(order)

    # 按时间倒序
    orders.sort(key=lambda o: o.createdAt, reverse=True)
    return orders

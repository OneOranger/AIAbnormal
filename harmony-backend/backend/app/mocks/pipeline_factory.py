"""配置类(规则/模型/Agent/处置/反馈)的 Mock 工厂。"""
import random
from datetime import datetime, timedelta
from typing import List
from app.config import settings
from app.schemas.pipeline import (
    RiskRule, MLModel, MLFeature, AgentConfig, AgentTool,
    KnowledgeBase, DispositionPolicy, FeedbackRecord,
)

# ============ 规则模板 ============
RULE_TEMPLATES = [
    ("R-FRD-001", "同设备多账号高频登录", "fraud", "device.account_count_1h > 5 AND geo.distinct_country_1h >= 2", ["ATO", "团伙"]),
    ("R-FRD-002", "合成身份特征命中", "fraud", "id.synthetic_score > 0.85 AND age_days < 30", ["合成身份"]),
    ("R-FRD-003", "Headless 浏览器 + 大额", "fraud", "device.headless = true AND amount > 5000", ["设备指纹"]),
    ("R-FRD-004", "信用卡 BIN 高风险国家", "fraud", "card.bin_country IN ('NG','RU','VE') AND amount > 1000", ["盗刷"]),
    ("R-FRD-005", "钱骡账户特征", "fraud", "account.in_out_ratio > 0.92 AND tx_count_24h > 20", ["Money Mule"]),
    ("R-FRD-006", "深度伪造活体检测命中", "fraud", "kyc.deepfake_score > 0.7", ["Deepfake"]),
    ("R-FRD-007", "支付页面脚本异常", "fraud", "page.skimming_signature_match = true", ["Magecart"]),
    ("R-BHV-001", "夜间大额海外交易", "behavioral", "hour BETWEEN 0 AND 5 AND amount > 10000 AND geo != home_country", ["夜间", "大额"]),
    ("R-BHV-002", "短时高频小额刷单", "behavioral", "tx_count_5min > 8 AND avg_amount < 50", ["刷单"]),
    ("R-BHV-003", "IP 跳变 (10分钟跨3国)", "behavioral", "ip.distinct_country_10min >= 3", ["IP跳变"]),
    ("R-BHV-004", "支付方式突变", "behavioral", "channel != user.preferred_channel AND amount > 2000", ["渠道突变"]),
    ("R-SYS-001", "回调超时 (>30s)", "system", "callback.elapsed_ms > 30000", ["回调"]),
    ("R-SYS-002", "重复支付检测", "system", "duplicate_in_24h(order_no, amount, user_id)", ["重复"]),
    ("R-REC-001", "渠道金额差异 > ¥1", "reconciliation", "ABS(internal_amount - channel_amount) > 1", ["对账"]),
    ("R-REC-002", "结算 T+2 未到账", "reconciliation", "settle_pending_days >= 2", ["结算"]),
    ("R-CHB-001", "近 30 天拒付率 > 1%", "chargeback", "merchant.chargeback_rate_30d > 0.01", ["商户"]),
    ("R-CHB-002", "友好欺诈高频用户", "chargeback", "user.friendly_fraud_count_180d >= 3", ["友好欺诈"]),
    ("R-MCH-001", "高风险行业商户", "merchant", "merchant.mcc IN ('7995','5967','6051')", ["MCC"]),
    ("R-MCH-002", "商户退款率突增", "merchant", "merchant.refund_rate_7d / merchant.refund_rate_30d > 3", ["突增"]),
    ("R-USR-001", "用户冲动消费提示", "user", "user.same_sku_count_5min >= 3", ["误操作"]),
    ("R-CMP-001", "OFAC 黑名单命中", "compliance", "kyc.ofac_match = true", ["AML"]),
    ("R-CMP-002", "AML 大额可疑 (¥50w+)", "compliance", "amount > 500000 AND aml.risk_level >= 'high'", ["AML"]),
    ("R-CMP-003", "高风险行业 + 跨境", "compliance", "merchant.high_risk = true AND tx.cross_border = true", ["跨境"]),
    ("R-FRD-008", "新设备 + 新IP + 新收款方", "fraud", "device.new = true AND ip.new = true AND payee.new = true", ["三新"]),
    ("R-BHV-005", "登录与支付相隔 < 10s", "behavioral", "login_to_pay_seconds < 10 AND amount > 3000", ["机器化"]),
]

OWNERS = ["王小风", "陈安全", "李对账", "周合规", "Alex Chen", "Sarah Kim"]


def generate_rules(seed: int = None) -> List[RiskRule]:
    rng = random.Random((seed or settings.RANDOM_SEED) + 1)
    statuses = ["active", "active", "active", "shadow", "draft", "disabled"]
    actions = ["intercept", "review", "score", "tag", "release"]
    scopes = ["realtime", "realtime", "both", "offline"]
    out = []
    for i, (code, name, cat, cond, tags) in enumerate(RULE_TEMPLATES):
        st = statuses[i % len(statuses)]
        out.append(RiskRule(
            id=f"rule-{i + 1}", code=code, name=name, category=cat,  # type: ignore
            description="命中即按规则动作处理。AI 持续监控该规则的精确率/召回率,漂移时建议下线。",
            status=st,  # type: ignore
            scope=rng.choice(scopes),  # type: ignore
            priority=rng.randint(40, 100),
            condition=cond,
            action=rng.choice(actions),  # type: ignore
            scoreDelta=rng.randint(8, 45),
            hitCount24h=0 if st == "disabled" else rng.randint(20, 4800),
            hitCount7d=0 if st == "disabled" else rng.randint(200, 38000),
            precision=round(rng.uniform(0.72, 0.98), 3),
            recall=round(rng.uniform(0.55, 0.94), 3),
            falsePositiveRate=round(rng.uniform(0.005, 0.08), 4),
            owner=rng.choice(OWNERS),
            updatedAt=(datetime.utcnow() - timedelta(days=rng.randint(1, 30))).isoformat() + "Z",
            createdAt=(datetime.utcnow() - timedelta(days=rng.randint(60, 720))).isoformat() + "Z",
            version=rng.randint(1, 12),
            tags=tags,
        ))
    return out


# ============ ML 模型 ============
MODEL_TEMPLATES = [
    ("fraud-xgb-v2", "欺诈识别主模型", "XGBoost", "fraud", "二分类 + 概率输出,集成 38 维行为/设备/图特征"),
    ("fraud-graphsage-v1", "团伙关联图模型", "GraphSAGE", "fraud", "用户-设备-IP 三元图,2 跳邻居聚合"),
    ("behavior-iforest-v1", "行为异常检测", "IsolationForest", "behavioral", "无监督离群检测,适合冷启动"),
    ("behavior-lstm-v1", "支付序列模型", "DeepFM", "behavioral", "近 30 笔行为序列编码 + 注意力"),
    ("recon-match-v1", "对账智能匹配", "GBDT", "reconciliation", "金额/时序/参考号模糊匹配"),
    ("chargeback-pred-v1", "拒付概率预测", "LightGBM", "chargeback", "T+30 内拒付概率预测"),
    ("compliance-text-v1", "合规文本风险", "AutoEncoder", "compliance", "交易备注+商户名 embedding 异常"),
]


def generate_models(seed: int = None) -> List[MLModel]:
    rng = random.Random((seed or settings.RANDOM_SEED) + 2)
    statuses = ["online", "online", "online", "shadow", "training"]
    feature_pools = {
        "fraud": [("device_age_days", "numeric"), ("ip_velocity_1h", "numeric"),
                  ("user_account_age", "numeric"), ("amount_zscore", "numeric"),
                  ("merchant_risk", "categorical"), ("device_fp_emb", "embedding"),
                  ("graph_centrality", "graph"), ("login_to_pay_secs", "numeric")],
        "behavioral": [("hour_of_day", "numeric"), ("amount", "numeric"),
                       ("tx_freq_5min", "numeric"), ("country_distinct_1h", "numeric")],
        "reconciliation": [("amount_diff", "numeric"), ("ref_similarity", "numeric"),
                           ("time_gap_min", "numeric"), ("channel", "categorical")],
        "chargeback": [("merchant_cb_rate", "numeric"), ("user_cb_history", "numeric"),
                       ("category", "categorical")],
        "compliance": [("text_emb", "embedding"), ("aml_score", "numeric")],
    }
    out = []
    for i, (mid, name, algo, cat, desc) in enumerate(MODEL_TEMPLATES):
        st = statuses[i % len(statuses)]
        pool = feature_pools.get(cat, feature_pools["fraud"])
        feats = [MLFeature(name=n, importance=round(rng.uniform(0.05, 0.95), 3), type=t)  # type: ignore
                 for n, t in pool]
        feats.sort(key=lambda f: f.importance, reverse=True)
        out.append(MLModel(
            id=mid, name=name, algo=algo, version=f"v2.{rng.randint(1, 8)}.{rng.randint(0, 9)}",  # type: ignore
            status=st, category=cat, description=desc,  # type: ignore
            threshold=round(rng.uniform(50, 80), 1),
            weight=round(rng.uniform(0.15, 0.45), 2),
            auc=round(rng.uniform(0.86, 0.97), 4),
            precision=round(rng.uniform(0.78, 0.95), 4),
            recall=round(rng.uniform(0.7, 0.92), 4),
            f1=round(rng.uniform(0.74, 0.93), 4),
            ks=round(rng.uniform(0.45, 0.72), 3),
            qps=rng.randint(800, 12000),
            p99Latency=rng.randint(15, 120),
            driftScore=round(rng.uniform(0.02, 0.18), 3),
            lastTrainedAt=(datetime.utcnow() - timedelta(days=rng.randint(1, 14))).isoformat() + "Z",
            nextRetrainAt=(datetime.utcnow() + timedelta(days=rng.randint(1, 7))).isoformat() + "Z",
            trainSamples=rng.randint(120000, 8500000),
            features=feats,
            owner=rng.choice(OWNERS),
            abTestRatio=round(rng.uniform(0.1, 0.5), 2) if st == "shadow" else None,
        ))
    return out


# ============ Agent ============
def generate_agents(seed: int = None) -> List[AgentConfig]:
    rng = random.Random((seed or settings.RANDOM_SEED) + 3)
    tool_pool = [
        ("queryGraph", "查询团伙关联图谱"),
        ("fetchUserHistory", "获取用户近 90 天交易历史"),
        ("checkBlacklist", "查询黑名单 / OFAC"),
        ("ragSearch", "RAG 检索知识库"),
        ("callMLModel", "调用 ML 模型评分"),
        ("generateRule", "生成 DSL 风控规则建议"),
        ("sendNotification", "推送 IM/邮件通知"),
    ]
    # 完整 9 Agent (Supervisor + Triage + Knowledge + Action + Report + 5 Specialists)
    agents_def = [
        ("agent-supervisor", "Supervisor 总调度", "deepseek-v3", "deepseek-chat", "fraud"),
        ("agent-triage", "Triage 分诊 Agent", "qwen-max", "qwen-max-2024", "fraud"),
        ("agent-knowledge", "Knowledge 知识管家", "qwen-max", "bge-large-zh", "fraud"),
        ("agent-fraud", "Fraud 欺诈深度分析", "qwen-max", "qwen-max-2024", "fraud"),
        ("agent-behavior", "Behavior 行为异常", "deepseek-v3", "deepseek-chat", "behavioral"),
        ("agent-recon", "Recon 智能对账", "gpt-4o", "gpt-4o-mini", "reconciliation"),
        ("agent-chargeback", "Chargeback 拒付应对", "claude-sonnet", "claude-3-5-sonnet", "chargeback"),
        ("agent-compliance", "Compliance 合规审查", "qwen-max", "qwen-max-2024", "compliance"),
        ("agent-action", "Action 处置执行", "deepseek-v3", "deepseek-chat", "fraud"),
        ("agent-report", "Report 报告生成", "qwen-max", "qwen-max-2024", "fraud"),
    ]
    out = []
    for i, (aid, name, prov, model, cat) in enumerate(agents_def):
        n_tools = rng.randint(3, 6)
        chosen = rng.sample(tool_pool, n_tools)
        tools = [AgentTool(name=t[0], description=t[1], enabled=rng.random() > 0.2,
                           callCount24h=rng.randint(50, 4500)) for t in chosen]
        out.append(AgentConfig(
            id=aid, name=name, description=f"针对 {cat} 类异常的专家 Agent",
            enabled=True, provider=prov, model=model,  # type: ignore
            temperature=round(rng.uniform(0.1, 0.5), 2),
            topP=round(rng.uniform(0.85, 0.98), 2),
            maxTokens=rng.choice([1024, 2048, 4096]),
            triggers=["auto", "rule_escalation"],
            triggerScore=rng.choice([60, 65, 70, 75]),
            triggerCategories=[cat],  # type: ignore
            enableMultimodal=rng.random() > 0.4,
            enableCausalGraph=rng.random() > 0.3,
            enableRAG=True,
            ragTopK=rng.choice([3, 5, 8]),
            ragKnowledgeBases=[f"kb-{rng.randint(1, 4)}"],
            tools=tools,
            systemPrompt=(f"你是「{name}」,负责对支付订单的 {cat} 类异常进行深度推理。"
                          "请输出: 1) 主分类与置信度 2) 核心证据链 3) 因果根因 4) 处置建议。"
                          "结论需基于 RAG 检索到的事实片段,严禁幻觉。"),
            enableHallucinationCheck=True,
            enableFactGrounding=True,
            enableSensitiveFilter=True,
            callCount24h=rng.randint(800, 6500),
            avgLatencyMs=rng.randint(800, 2400),
            avgTokens=rng.randint(900, 1800),
            costUSD24h=round(rng.uniform(2.5, 38.0), 2),
            hallucinationRate=round(rng.uniform(0.005, 0.045), 4),
        ))
    return out


def generate_kbs(seed: int = None) -> List[KnowledgeBase]:
    rng = random.Random((seed or settings.RANDOM_SEED) + 4)
    defs = [
        ("kb-1", "风控规则文档库", "rule_doc"),
        ("kb-2", "历史欺诈案例库", "case_history"),
        ("kb-3", "支付合规法规库", "regulation"),
        ("kb-4", "商户画像库", "merchant_profile"),
        ("kb-5", "欺诈模式知识库", "fraud_pattern"),
    ]
    out = []
    for kid, name, t in defs:
        out.append(KnowledgeBase(
            id=kid, name=name, type=t,  # type: ignore
            documentCount=rng.randint(120, 3500),
            vectorCount=rng.randint(2400, 78000),
            lastIndexedAt=(datetime.utcnow() - timedelta(hours=rng.randint(1, 72))).isoformat() + "Z",
            embedding=rng.choice(["bge-large-zh", "text-embedding-3-large", "m3e-large"]),  # type: ignore
        ))
    return out


# ============ 处置策略 ============
def generate_policies(seed: int = None) -> List[DispositionPolicy]:
    rng = random.Random((seed or settings.RANDOM_SEED) + 5)
    defs = [
        ("p-1", "欺诈高分自动拦截", "fraud", "critical", 85, 90, "intercept", ["force_2fa", "add_blacklist"]),
        ("p-2", "高风险人工复核", "all", "high", 65, 75, "review", ["watchlist"]),
        ("p-3", "重复支付自动退款", "system", "all", 30, 80, "auto_refund", ["notify_user"]),
        ("p-4", "合规命中冻结账户", "compliance", "critical", 80, 85, "freeze_account", ["escalate"]),
        ("p-5", "中等风险加观察", "behavioral", "medium", 40, 60, "watchlist", []),
        ("p-6", "拒付高风险升级", "chargeback", "high", 70, 75, "escalate", ["notify_user"]),
    ]
    out = []
    for i, (pid, name, cat, lvl, ms, mc, pa, sas) in enumerate(defs):
        out.append(DispositionPolicy(
            id=pid, name=name, description=f"AI 推荐 + 人工策略组合",
            enabled=True, priority=100 - i * 10,
            category=cat, riskLevel=lvl,
            minScore=ms, minConfidence=mc,
            primaryAction=pa,  # type: ignore
            secondaryActions=sas,  # type: ignore
            autoExecute=(pa in ["intercept", "auto_refund", "watchlist"]),
            requireHumanApproval=(pa in ["freeze_account", "escalate"]),
            notifyChannels=rng.sample(["email", "sms", "webhook", "im"], rng.randint(1, 3)),
            feedbackRequired=True,
            cooldownMinutes=rng.choice([5, 15, 30, 60]),
            executedCount24h=rng.randint(80, 1200),
            successRate=round(rng.uniform(0.85, 0.99), 3),
            reversedCount24h=rng.randint(0, 25),
            avgProcessingMs=rng.randint(120, 1800),
            updatedAt=(datetime.utcnow() - timedelta(days=rng.randint(1, 14))).isoformat() + "Z",
        ))
    return out


def generate_feedback(seed: int = None, n: int = 60) -> List[FeedbackRecord]:
    rng = random.Random((seed or settings.RANDOM_SEED) + 6)
    actions = ["intercept", "review", "release", "auto_refund", "watchlist", "escalate"]
    types = ["confirm", "override", "partial_correct", "false_positive", "false_negative"]
    reviewers = ["王小风", "陈安全", "李对账", "周合规"]
    out = []
    for i in range(n):
        ai = rng.choice(actions)
        final = ai if rng.random() < 0.7 else rng.choice(actions)
        ftype = "confirm" if ai == final else rng.choice(types[1:])
        out.append(FeedbackRecord(
            id=f"fb-{i + 1}",
            orderNo=f"PAY{(datetime.utcnow() - timedelta(hours=rng.randint(1, 720))).strftime('%Y%m%d')}{1000 + i:06d}",
            originalAction=ai, aiSuggestion=ai, finalAction=final,  # type: ignore
            reviewer=rng.choice(reviewers),
            reviewedAt=(datetime.utcnow() - timedelta(hours=rng.randint(1, 720))).isoformat() + "Z",
            isCorrect=(ftype == "confirm"),
            feedbackType=ftype,  # type: ignore
            comment=rng.choice([
                "证据链充分,AI 判断准确,已确认拦截。",
                "用户实际为正常交易,AI 误杀,需补充该商户白名单。",
                "AI 漏判,实际为团伙欺诈,已加入训练样本。",
                "部分正确,主分类对但子类需要细化。",
            ]),
            fedToRAG=rng.random() > 0.3,
            fedToTraining=rng.random() > 0.4,
            ruleSuggestion="ADD: device.fp = X AND merchant.id = Y → 自动通过" if rng.random() > 0.6 else None,
            estimatedSavedLoss=round(rng.uniform(120, 25000), 2) if ftype == "confirm" else None,
        ))
    return out

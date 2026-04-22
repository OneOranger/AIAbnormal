# AI 支付异常订单分析系统 — 后端架构与开发计划 (v1)

> 适用阶段:**前端 Demo 已完成 / 后端待开发**
> 数据库:**暂不接入,使用模拟数据 + 本地内存/文件存储**
> 部署形态:**多 Agent 微服务化 + 模型推理服务 + 编排层 + 反馈闭环**
> 接口契约:**已在前端 `src/lib/api.ts` 预留**,后端只需对齐 URL 与 Schema 即可无缝替换。

---

## 一、整体架构总览

### 1.1 分层视图

```
┌──────────────────────────────────────────────────────────────────────┐
│  接入层 (Ingress)                                                    │
│  Kafka / REST / SFTP / Webhook  →  统一事件总线 (event-bus)          │
└──────────────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────────────┐
│  预处理层 (Preprocess Service)                                       │
│  字段归一化 / 缺失补全 / 设备指纹解析 / 特征工程 / 标准化事件         │
└──────────────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────────────┐
│  推理编排层 (Orchestrator / Pipeline)  ★核心★                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 规则引擎 │→│  ML 模型 │→│ AI Agent │→│ 自动处置 │→ 反馈回流      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘              │
│   (毫秒级)     (10-50ms)     (1-3s,可选) (策略匹配执行)              │
└──────────────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────────────┐
│  多 Agent 协作层 (Multi-Agent Layer)                                 │
│  Triage / Fraud / Recon / Chargeback / Compliance / Knowledge /      │
│  Action / Report  (8 个专业 Agent + 1 个 Supervisor)                 │
└──────────────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────────────┐
│  存储与知识层 (Storage)                                              │
│  内存 LRU(热) + JSONL 文件(暖) + 向量库占位 + 图谱占位               │
└──────────────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────────────┐
│  对外 API 层 (BFF)                                                   │
│  对齐前端 src/lib/api.ts 的 24 个端点                                │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.2 推荐技术栈 (后端)

| 层 | 推荐选型 | 备注 |
|---|---|---|
| 语言 | **Python 3.11**(AI/ML 主力) + **Go**(高 QPS 网关,可选) | Python 单体起步即可 |
| Web 框架 | **FastAPI** + Uvicorn | 与前端 `api.ts` 对齐 REST |
| Agent 框架 | **LangGraph** 或 **CrewAI** | LangGraph 更适合状态机编排 |
| LLM | 通义千问 Max / DeepSeek-V3 / GPT-4o(可切换) | 通过 LiteLLM 网关统一 |
| 向量库 | Milvus / Qdrant(占位,先用本地 FAISS) | RAG |
| 图数据库 | Neo4j / NebulaGraph(占位,先用 networkx) | 团伙图谱 |
| 流处理 | Kafka + Faust(可选) | 第一阶段用 asyncio 队列模拟 |
| 模型训练 | scikit-learn / XGBoost / LightGBM / PyTorch | + MLflow 跟踪 |
| 调度 | APScheduler(轻量) → Airflow(重量) | 模型重训定时任务 |
| 监控 | Prometheus + Grafana + Loki | 全链路 trace |

---

## 二、多 Agent 架构设计

### 2.1 为什么是多 Agent

支付异常场景**异构性极强**:欺诈分析需要图谱推理,对账需要数值匹配,拒付需要文档生成。单 Agent 既要又要会导致 Prompt 膨胀、幻觉率上升、成本失控。**按业务领域拆分 Agent**,每个 Agent 拥有独立的:
- System Prompt(领域知识)
- Tools(可调用函数)
- Knowledge Base(RAG 索引)
- Model(可选不同 LLM,贵的留给关键任务)

### 2.2 Agent 清单(9 个)

| # | Agent | 职责 | 触发时机 | 主要 Tools | 推荐模型 |
|---|---|---|---|---|---|
| 0 | **SupervisorAgent** | 总调度,根据订单分类路由到对应专家 Agent;聚合多 Agent 结论 | 每笔进入 Agent 层的订单 | `route()`, `merge_results()` | DeepSeek-V3(便宜快) |
| 1 | **TriageAgent**(分诊) | 8 大类异常打标 + 多标签 + 置信度 | 规则/ML 输出后 | `classify()`, `query_taxonomy()` | Qwen-Max |
| 2 | **FraudAgent**(欺诈专家) | 欺诈类深度根因(ATO/合成身份/团伙) | 主分类=fraud | `query_graph()`, `device_lookup()`, `ip_geo()`, `rag_search()` | GPT-4o |
| 3 | **BehaviorAgent**(行为专家) | 行为模式异常分析(频率/速度/突变) | 主分类=behavioral | `time_series_check()`, `user_history()` | Qwen-Max |
| 4 | **ReconAgent**(对账专家) | 对账差异根因 + 调整凭证生成 | 对账模块触发 | `fuzzy_match()`, `fee_calc()`, `fx_calc()`, `gen_voucher()` | DeepSeek-V3 |
| 5 | **ChargebackAgent**(拒付专家) | 拒付争议分析 + 抗辩文案生成 | 主分类=chargeback | `case_search()`, `gen_dispute_letter()`, `evidence_pack()` | GPT-4o |
| 6 | **ComplianceAgent**(合规专家) | 黑名单/反洗钱/制裁名单匹配 | 命中合规规则 | `aml_check()`, `sanction_check()`, `pep_check()` | Qwen-Max |
| 7 | **KnowledgeAgent**(知识管家) | RAG 检索 + 相似案例召回 + 知识更新 | 被其他 Agent 调用 | `vector_search()`, `kb_update()`, `case_recall()` | bge-large-zh(纯检索) |
| 8 | **ActionAgent**(执行) | 调用支付网关执行处置动作 + 二次校验 | 处置策略命中 | `intercept()`, `refund()`, `freeze()`, `notify()` | DeepSeek-V3(轻推理) |
| 9 | **ReportAgent**(报告) | 自然语言报告 + 看板数据生成 | 用户对话/定时 | `query_db()`, `gen_chart()`, `format_md()` | Qwen-Max |

### 2.3 协作模式

**LangGraph 状态机示意**:

```python
# pseudo-code
graph = StateGraph(OrderState)

graph.add_node("preprocess", preprocess_node)
graph.add_node("rules", rules_engine_node)
graph.add_node("ml_score", ml_ensemble_node)
graph.add_node("supervisor", supervisor_agent)
graph.add_node("triage", triage_agent)
graph.add_node("fraud", fraud_agent)
graph.add_node("behavior", behavior_agent)
graph.add_node("compliance", compliance_agent)
graph.add_node("disposition", disposition_node)
graph.add_node("feedback_log", feedback_writer)

graph.add_edge("preprocess", "rules")
graph.add_edge("rules", "ml_score")
graph.add_edge("ml_score", "supervisor")

# Supervisor 条件路由
graph.add_conditional_edges("supervisor", route_by_category, {
    "fraud": "fraud",
    "behavioral": "behavior",
    "compliance": "compliance",
    "low_risk": "disposition",   # 低风险跳过 Agent
})

graph.add_edge(["fraud", "behavior", "compliance"], "triage")
graph.add_edge("triage", "disposition")
graph.add_edge("disposition", "feedback_log")
graph.set_entry_point("preprocess")
```

**关键设计**:
- **短路机制**:规则命中 `intercept` 高分 → 直接跳过 ML/Agent,1 秒内拦截
- **并行触发**:对账类与欺诈类可同时入两条流
- **降级策略**:Agent 超时 / LLM 故障 → 退回 ML 评分 + 默认策略,绝不阻塞业务

---

## 三、ML 模型详细说明

### 3.1 是否需要训练?

**需要,但分层处理**:
- **冷启动期**:用预训练 + 规则数据合成训练样本,前 30 天可纯规则 + LLM
- **稳定期**:基于真实标注数据(人工反馈 + 处置结果)持续微调
- **成熟期**:每周自动重训 + A/B 影子模型

### 3.2 模型矩阵(7 个模型,各司其职)

| # | 模型名 | 算法 | 业务作用 | 输入特征 | 输出 | 训练频率 |
|---|---|---|---|---|---|---|
| 1 | **fraud-gbdt-v2** | XGBoost | 通用欺诈打分(主力) | 80 维:金额/时间/设备/IP/历史 | risk_score 0-100 | 周级 |
| 2 | **ato-deepfm-v1** | DeepFM | 账户接管识别(深度交叉特征) | 用户行为序列 + 设备 embedding | ato_prob 0-1 | 月级 |
| 3 | **fraud-graphsage-v1** | GraphSAGE | 团伙欺诈(图神经网络) | 用户-设备-IP-收款方异构图 | gang_score + cluster_id | 月级 |
| 4 | **anomaly-iforest-v3** | IsolationForest | 无监督异常检测(新型欺诈兜底) | 全量数值特征 | anomaly_score | 日级(增量) |
| 5 | **behavior-lstm-v1** | LSTM AutoEncoder | 用户行为序列异常 | 近 30 天交易序列 | reconstruction_error | 周级 |
| 6 | **recon-match-lgb-v2** | LightGBM | 对账模糊匹配置信度 | 金额差/时间差/字符串相似度 | match_prob | 月级 |
| 7 | **chargeback-pred-v1** | XGBoost | 拒付概率预测(事前) | 商户/用户/品类历史 | chargeback_prob | 月级 |

### 3.3 模型融合策略

```
final_risk = 0.40 * fraud_gbdt
           + 0.20 * ato_deepfm     (仅账户类异常)
           + 0.20 * graphsage      (仅有团伙关联时)
           + 0.10 * iforest        (兜底)
           + 0.10 * behavior_lstm
+ rule_score_delta(规则命中加成,最多 +30)
```

权重在前端 `/config/models` 页可视化调整,后端读取热更新。

### 3.4 模型训练完整业务流程(以 fraud-gbdt 为例)

```
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: 样本构建 (Sample Construction)                          │
│  ─ 来源:                                                         │
│    a. 历史订单(过去 90 天)                                       │
│    b. 人工标注反馈(FeedbackRecord 表)                            │
│    c. 拒付回执(chargeback 结果作为强标签)                         │
│    d. 规则确认拦截(高精度规则的命中作为正样本)                      │
│  ─ 正负比例:1:20(欺诈占比 5%),用 SMOTE 上采样到 1:5             │
│  ─ 输出:train.parquet / valid.parquet / test.parquet            │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: 特征工程 (Feature Engineering)                          │
│  ─ 80 维特征,分 6 组:                                            │
│    • 交易特征(15):金额、币种、渠道、时间小时段、是否周末…        │
│    • 用户特征(20):注册天数、近 7/30 天交易数、平均金额…          │
│    • 设备特征(15):指纹熵、是否模拟器、首次出现、设备多账号数…    │
│    • 网络特征(10):IP 信誉、是否代理、IP /24 段共用账号数…        │
│    • 商户特征(10):商户风险分、退款率、行业…                      │
│    • 衍生特征(10):金额/平均值比、距上单时间、跨地理速度…         │
│  ─ 在线/离线特征一致性校验(避免训练-推理偏差)                     │
│  ─ 特征存储:Feast Feature Store(占位,先用 dict)                │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: 训练 (Training)                                         │
│  ─ XGBoost 超参搜索(Optuna,50 trials)                           │
│  ─ 5-fold CV,目标 AUC                                           │
│  ─ 早停 50 轮                                                    │
│  ─ MLflow 记录:超参 / 指标 / 特征重要性 / 模型 artifact          │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: 评估 (Evaluation) — 必须全部通过才能上线                 │
│  ─ AUC ≥ 0.92  (当前线上 0.94)                                  │
│  ─ KS  ≥ 0.55                                                   │
│  ─ Top 1% 精确率 ≥ 0.85(高分段不能误杀好人)                      │
│  ─ Top 5% 召回率 ≥ 0.70                                         │
│  ─ 公平性检查(地区/年龄不能有显著偏差)                            │
│  ─ 漂移检查 PSI ≤ 0.1                                           │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: 影子上线 (Shadow Deployment)  3-7 天                    │
│  ─ 新模型与旧模型同时打分,只记录不决策                             │
│  ─ 对比关键指标:误杀率 / 召回 / 分数分布                          │
│  ─ A/B 实验配置在 `/config/models` 页                            │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│  Step 6: 灰度上线 (Canary)                                       │
│  ─ 5% → 20% → 50% → 100%,每阶段观察 24h                        │
│  ─ 任一指标恶化 > 5% 自动回滚                                     │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│  Step 7: 线上监控 (Monitoring)                                   │
│  ─ 实时:QPS / P99 延迟 / 错误率                                  │
│  ─ 每日:分数分布 PSI / 特征 PSI / 召回与精确率(T+1 标签)         │
│  ─ 漂移告警 → 触发自动重训                                        │
└─────────────────────────────────────────────────────────────────┘
```

### 3.5 训练代码骨架(目录结构)

```
backend/
├── ml/
│   ├── pipelines/
│   │   ├── fraud_gbdt/
│   │   │   ├── 01_build_samples.py      # 样本构建
│   │   │   ├── 02_feature_eng.py        # 特征工程
│   │   │   ├── 03_train.py              # 训练
│   │   │   ├── 04_evaluate.py           # 评估
│   │   │   ├── 05_register.py           # 注册到 MLflow
│   │   │   └── config.yaml
│   │   ├── ato_deepfm/...
│   │   ├── graphsage/...
│   │   └── ...
│   ├── serving/
│   │   ├── ensemble.py                  # 融合打分服务
│   │   ├── feature_store.py             # 在线特征(Redis,先用 dict)
│   │   └── model_registry.py            # 模型版本管理
│   ├── monitoring/
│   │   ├── drift_detector.py            # PSI 计算
│   │   └── perf_tracker.py
│   └── scheduler/
│       └── retrain_jobs.py              # APScheduler
```

---

## 四、对外 API 清单(对齐前端)

前端 `src/lib/api.ts` 已定义 24 个端点,后端只需实现以下 URL(把 mock 换成真实逻辑):

```
# 异常订单
GET    /orders                         列表(分页+筛选)
GET    /orders/{id}                    详情
POST   /orders/{id}/actions            执行处置动作

# 对账
GET    /reconciliation                 对账列表

# AI Agent 对话
POST   /agent/chat                     流式对话(建议 SSE)

# 规则引擎
GET    /rules
POST   /rules                          新增/修改
POST   /rules/{id}/toggle

# ML 模型
GET    /models
PATCH  /models/{id}
POST   /models/{id}/retrain

# AI Agent 配置
GET    /agents
GET    /agents/kb
PATCH  /agents/{id}
POST   /agents/{id}/test               Playground

# 处置策略 + 反馈
GET    /policies
POST   /policies
POST   /policies/{id}/toggle
GET    /feedback
POST   /feedback
```

切换方式:前端只需设置 `VITE_API_BASE_URL=https://api.xxx.com`,无需改任何业务代码。

---

## 五、模拟数据 + 本地存储方案(无数据库阶段)

### 5.1 存储分层

```
backend/storage/
├── seeds/              # 启动时加载的种子数据(JSON)
│   ├── orders.json     # 1200 笔订单(与前端 mock 同源)
│   ├── recon.json      # 480 条对账
│   ├── rules.json      # 25 条规则
│   ├── models.json     # 7 个模型元数据
│   ├── agents.json
│   ├── policies.json
│   └── feedback.json
├── runtime/            # 运行时写入(JSONL,追加模式)
│   ├── new_orders.jsonl       # 新进单
│   ├── inferences.jsonl       # 每次推理快照(全链路审计)
│   ├── actions.jsonl          # 处置动作日志
│   └── feedback.jsonl         # 人工反馈
└── kb/                 # 知识库占位
    └── faiss_index/
```

### 5.2 内存层(高频读)

```python
# backend/store/memory.py
class InMemoryStore:
    orders: Dict[str, Order] = {}        # LRU 1万条
    rules: Dict[str, Rule] = {}
    models_meta: Dict[str, ModelMeta] = {}
    # ... 启动时从 seeds/ 加载

    def append_inference(self, snapshot):
        # 同步写 runtime/inferences.jsonl
```

替换数据库时只需改 `InMemoryStore` 的实现(Repository 模式),业务层无感知。

---

## 六、★业务数据流转全链路★

### 6.1 一笔订单从进入到处置的 9 个阶段

```
[阶段 0] 数据进入
  ↓ Kafka topic: payment.events  /  REST POST /ingest
  ↓ payload: { orderNo, userId, amount, currency, channel, ip, deviceId, ... }

[阶段 1] 预处理 (Preprocess Service,~20ms)
  ↓ • 字段归一化(币种统一为 CNY,时间统一 UTC)
  ↓ • 关联补全:查用户画像、设备画像、商户画像、IP 画像
  ↓ • 输出 EnrichedOrder(80 维特征向量)
  ↓ 写入 runtime/new_orders.jsonl

[阶段 2] 规则引擎 (Rules Engine,~5ms)
  ↓ • 加载 25 条 active 规则,按 priority 排序逐条匹配
  ↓ • 命中 → 累计 score_delta、收集 hit_rules[]
  ↓ • 高优先级"硬拦截"规则命中 → 直接跳到阶段 7(短路)
  ↓ • 输出 RuleResult { hit_rules, rule_score, suggested_action }

[阶段 3] ML 模型融合打分 (ML Ensemble,~30ms)
  ↓ • 并行调用 7 个模型(GBDT 主力 + 其他特征性模型)
  ↓ • 按权重融合 → final_ml_score (0-100)
  ↓ • 漂移检测:PSI > 阈值 → 异步告警
  ↓ • 输出 MLResult { model_scores{}, ensemble_score, top_features[] }

[阶段 4] 综合风险评分 + 路由判定 (Risk Aggregator,~5ms)
  ↓ risk_score = clip(rule_score + ml_score, 0, 100)
  ↓ 路由表:
  ↓   risk < 30           → 直接 release(跳到阶段 7)
  ↓   30 ≤ risk < 60      → 进入 Agent 轻分析
  ↓   60 ≤ risk < 85      → 进入 Agent 深度分析(全 RAG + 工具)
  ↓   risk ≥ 85           → Agent 分析 + 强制人工复核

[阶段 5] AI Agent 多模态因果推理 (Multi-Agent,~1.5s)
  ↓ ① SupervisorAgent 接单,根据 primary_category 分发
  ↓ ② 专家 Agent(Fraud/Behavior/Recon/...) 并行执行:
  ↓     - 调用 Tools(图谱查询、设备查询、相似案例召回)
  ↓     - RAG:在 KnowledgeAgent 中检索 Top-K 知识片段
  ↓     - LLM 推理生成结构化 JSON:
  ↓       { root_cause, evidence_chain[], confidence, recommended_actions[] }
  ↓ ③ ComplianceAgent 同步合规检查(黑名单/制裁名单)
  ↓ ④ SupervisorAgent 聚合多 Agent 结论,做幻觉校验
  ↓ ⑤ 输出 AgentResult { reasoning, evidence, confidence, actions }

[阶段 6] 处置策略匹配 (Disposition Engine,~10ms)
  ↓ • 遍历 active policies,匹配条件 (category + risk_level + score + confidence)
  ↓ • 选中最高 priority 的 policy
  ↓ • 判断 autoExecute / requireHumanApproval
  ↓ • 输出 DispositionDecision { primary_action, secondary_actions[], mode }

[阶段 7] 动作执行 (Action Agent,~100-500ms)
  ↓ ① 二次校验(冷却期、用户黑白名单、节假日策略)
  ↓ ② 调用支付网关 API:
  ↓     - intercept   → 调用 /gateway/block
  ↓     - auto_refund → 调用 /gateway/refund
  ↓     - force_2fa   → 推送 /auth/challenge
  ↓     - freeze      → 调用 /account/freeze
  ↓ ③ 通知渠道(email/sms/webhook/im)
  ↓ ④ 写 runtime/actions.jsonl(全链路审计)

[阶段 8] 全链路落库 + 推送前端
  ↓ • 落 inferences.jsonl(订单 + 规则 + ML + Agent + 动作 全快照)
  ↓ • 推送 WebSocket / SSE → 前端订单列表实时刷新
  ↓ • 触发 webhook(给商户/财务系统)

[阶段 9] 反馈闭环 (异步,T+0 ~ T+7)
  ↓ ① 人工复核员在前端 /config/disposition 反馈页操作:
  ↓     - confirm(AI 正确)
  ↓     - override(改判)
  ↓     - false_positive / false_negative
  ↓ ② 反馈写入 feedback.jsonl
  ↓ ③ KnowledgeAgent 异步消费:
  ↓     - 正确案例 → 入 RAG 向量库(强化知识)
  ↓     - 错判案例 → 入训练样本池(下次重训用)
  ↓     - AI 自动生成规则建议 → 推送到 /config/rules 待审核
  ↓ ④ 调度器(APScheduler)按周触发模型重训(章节 3.4 流程)
```

### 6.2 一图速览:数据流 + 时延预算

```
   进单
    │  20ms
    ▼
 预处理 ──→ runtime/new_orders.jsonl
    │  5ms
    ▼
 规则引擎 ━━━高分硬拦截━━━┓
    │  30ms                ┃
    ▼                      ┃
 ML 融合打分                ┃
    │  5ms                  ┃
    ▼                      ┃
 综合评分 + 路由            ┃
    │  低分→直放            ┃
    │  中高分               ┃
    ▼                      ┃
 多 Agent 推理(1-3s)      ┃
    │                      ┃
    ▼                      ▼
 处置策略匹配 ←━━━━━━━━━━━━┛
    │  100-500ms
    ▼
 网关执行 + 通知
    │
    ▼
 落库 + 推前端 + 反馈闭环

总时延预算:
  - 短路路径:< 200ms
  - 标准路径:< 2.5s
  - SLA  P99:< 3s
```

### 6.3 三个典型场景示例

**场景 A:夜间 5 万元跨境转账**
```
进单 → 规则命中"R-FRAUD-007 大额跨境夜间" (+25 分)
     → ML 融合 78 分 → 总分 100 (cap)
     → 路由到 FraudAgent + ComplianceAgent
     → FraudAgent 发现设备首次出现 + 同 IP /24 段有 7 个欺诈历史
     → ComplianceAgent 命中 PEP 名单
     → 处置策略 P-001 命中 → autoExecute=true
     → ActionAgent 执行:intercept + force_2fa + add_blacklist
     → 全程 1.8s
```

**场景 B:对账差异**
```
对账文件入 → ReconAgent
          → fuzzy_match(金额±0.01,参考号 Levenshtein<3)
          → 80% 自动匹配
          → 20% 差异分类:手续费未同步 / 时序差异 / 重复条目
          → 调用 gen_voucher() 生成调整凭证
          → 推送财务系统 + 前端 /reconciliation 页展示
```

**场景 C:用户友好欺诈拒付**
```
拒付通知 webhook → ChargebackAgent
                → 调用 case_search() 召回相似 5 个胜诉案例
                → KnowledgeAgent 检索发卡行抗辩模板
                → gen_dispute_letter() 生成抗辩信 + 证据包
                → 人工复核确认 → 提交 Visa/MC
                → 反馈结果回流 → 训练 chargeback-pred 模型
```

---

## 七、开发里程碑(8 周计划)

| 周 | 里程碑 | 交付物 |
|---|---|---|
| W1 | 脚手架 + Mock 数据迁移 | FastAPI 工程、24 个端点骨架、JSONL 存储 |
| W2 | 规则引擎 + 简单 ML(GBDT) | DSL 解析器、规则热更新、第一个可用模型 |
| W3 | 预处理服务 + 特征工程 | 80 维特征流水线、特征一致性校验 |
| W4 | LangGraph 编排 + Supervisor + Triage | 端到端最简推理链路打通 |
| W5 | Fraud/Behavior/Recon 三大 Agent | RAG + Tools 完整版 |
| W6 | 处置引擎 + ActionAgent + 反馈闭环 | 策略匹配、网关 mock、反馈写入 |
| W7 | 模型训练流水线 + 调度 + 监控 | MLflow + APScheduler + 漂移告警 |
| W8 | 性能压测 + 灰度发布 + 联调前端 | 替换 `VITE_API_BASE_URL` 全链路联调 |

---

## 八、可演进点(未来不必现在做)

1. **Kafka + Flink 流处理**:替换当前 asyncio 队列
2. **真实数据库**:PostgreSQL(订单) + Milvus(向量) + Neo4j(图) + Redis(特征)
3. **联邦学习**:多商户数据不出域联合建模
4. **端侧设备指纹 SDK**:提升设备画像质量
5. **强化学习**:用 RL 优化处置策略(reward = 节省损失 - 误杀成本)

---

_文档版本 v1 — 与前端 Demo `src/lib/api.ts`、`pipeline-types.ts` 完全对齐_

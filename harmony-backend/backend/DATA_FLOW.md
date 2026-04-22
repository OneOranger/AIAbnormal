# 🔄 业务数据流转 — 一笔订单进来后发生了什么

```
┌──────────────────────────────────────────────────────────────────┐
│ 业务系统 (商户/收银台/批量文件)                                  │
└──────────────────┬───────────────────────────────────────────────┘
                   │ HTTP POST /orders/{id}/analyze
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 1: Ingest — FastAPI 接收,Pydantic 校验                     │
│ Stage 2: Preprocess — 字段标准化 / 特征补齐                      │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 3: 规则引擎 (5ms)                                          │
│  app/rules/engine.py → DSL 求值 → 命中列表 + score_delta         │
│  例: 命中 R-FRD-003(Headless+大额) +35 分                        │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 4: ML 集成评分 (30ms)                                      │
│  app/ml/inference.py → score_order()                             │
│   ├─ fraud-xgb-v2 (XGBoost) → 0.92                              │
│   ├─ behavior-iforest-v1 → 离群分                               │
│   └─ 加权融合 → fused_score = 88                                 │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 5: 路由 — fused_score≥60 或 命中规则≥2 → 走 Agent          │
└──────────────────┬───────────────────────────────────────────────┘
                   │ Yes
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 6: 多 Agent 推理 (1.5s)                                    │
│  app/agents/graph.py → run_graph()                               │
│   ├─ Supervisor 选 Specialist (按 category)                      │
│   ├─ FraudAgent / BehaviorAgent / ... 并行执行                  │
│   │   每个 Agent:                                                │
│   │    1. 加载 system prompt (app/prompts/system/*.md)          │
│   │    2. RAG 检索相关案例 (sentence-transformers)              │
│   │    3. 调 LLM (OpenAI/Qwen/DeepSeek/Mock 自动)               │
│   │    4. 输出 JSON: 根因 + 证据 + 建议                          │
│   └─ Supervisor 汇总 → final_decision                            │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 7: 处置匹配                                                │
│  policies_repo 中找第一条满足 (category + minScore + minConf)   │
│  例: 匹配到 p-1 "欺诈高分自动拦截"                              │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 8: Action 执行                                             │
│  policy.autoExecute=true → 直接 orders_repo.update(status)       │
│  policy.requireHumanApproval=true → 推到待审队列                 │
│  根据 notifyChannels 推 IM/Email/SMS/Webhook                     │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ Stage 9: 反馈闭环                                                │
│  人工在前端点"确认/覆盖" → POST /feedback                       │
│   ├─ fedToRAG=true → 案例进 RAG 知识库                          │
│   └─ fedToTraining=true → 进下次 ML 训练样本                    │
│  下次模型重训 (APScheduler 定时 / 手动 retrain) → 闭环           │
└──────────────────────────────────────────────────────────────────┘
```

## 关键数据落地

| 阶段 | 写入位置 |
|---|---|
| Ingest | (无,内存对象) |
| Rules 命中 | trace 内存 + 日志 |
| ML 评分 | trace 内存 |
| Agent 推理 | trace 内存 + LLM 日志 |
| 状态变更 | `data/runtime/orders.jsonl` |
| 反馈记录 | `data/runtime/feedback.jsonl` |
| 模型权重 | `data/models/*.pkl` |
| RAG 向量 | `data/vectors/` |
| 缓存 | `data/cache/` |

## 想看真实流转?

```bash
curl -X POST http://localhost:8000/orders/ord-1/analyze | python -m json.tool
```

返回的 `trace.stages` 会展示每阶段耗时与中间产物。

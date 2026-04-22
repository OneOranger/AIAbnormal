# 后端设计对齐检查

## 结论

你指出的问题是准确的：之前后端不是完全没有实现，而是功能实现和目录结构没有完全对齐 `backend-design-v1.md`。

本次已经做了两类修正：

1. 数据目录按设计文档落位到 `backend/storage/seeds`、`backend/storage/runtime`、`backend/storage/kb/faiss_index`。
2. 9 阶段流水线从单个 `orchestrator.py` 内联实现，拆成 `pipeline/stage_*` 文件，方便后续维护和定位。

## 功能对照

| 设计项 | 当前状态 | 说明 |
|---|---|---|
| FastAPI BFF | 已实现 | 前端 `api.ts` 需要的接口已经覆盖，并额外提供 `/ingest`、`/system/*` 诊断接口。 |
| 订单列表/详情/动作 | 已实现 | `GET /orders`、`GET /orders/{id}`、`POST /orders/{id}/actions`。 |
| 真实业务进单 | 已实现 | `POST /ingest` 支持生产风格最小事件字段，并转换为完整 `AnomalyOrder`。 |
| 对账列表 | 已实现 | `GET /reconciliation`。 |
| 一键对账 | 已补齐 | `POST /reconciliation/match` 会扫描本地对账数据并写动作审计。 |
| 规则配置 | 已实现 | 规则列表、upsert、启停。 |
| ML 模型配置 | 已实现 | 模型列表、配置更新、异步重训入口。 |
| Agent 配置 | 已实现 | Agent 列表、KB 列表、配置更新、Playground 测试。 |
| 处置策略 | 已实现 | 策略列表、upsert、启停。 |
| 反馈闭环 | 已实现 | 反馈列表、提交反馈、异步消费到 RAG/训练样本占位。 |
| LLM Provider | 已实现 | OpenAI/Qwen/DeepSeek/mock，按 `.env` 自动选择或强制选择。 |
| 多 Agent | 已实现为本地 async 编排 | 当前是 LangGraph 风格编排，不是拆成真实微服务；无 key 时可降级 mock。 |
| 7 个 ML 模型 | 已实现训练/推理骨架 | 本地 `.pkl` 产物放 `data/models/`，默认不提交 Git。 |
| RAG | 部分实现 | 当前是内存向量检索和种子案例；`storage/kb/faiss_index` 已按设计占位，持久化 FAISS 可下一阶段接入。 |
| Kafka/SFTP/Webhook 接入层 | 部分实现 | 当前用 REST `/ingest` 和本地 JSONL 导入脚本模拟。Kafka/SFTP 是下一阶段替换点。 |
| 真实数据库 | 暂不接入 | 当前按你的要求使用本地 JSON/JSONL 文件模拟。 |
| 真实支付网关执行 | 暂未接入 | 当前 ActionAgent 做二次校验和本地动作审计，不调用真实网关。 |

## 目录结构对照

设计文档里的数据目录现在已经建立：

```text
backend/storage/
├── seeds/
│   ├── orders.json
│   ├── recon.json
│   ├── rules.json
│   ├── models.json
│   ├── agents.json
│   ├── kbs.json
│   ├── policies.json
│   └── feedback.json
├── runtime/
│   ├── orders.jsonl
│   ├── recon.jsonl
│   ├── rules.jsonl
│   ├── models.jsonl
│   ├── agents.jsonl
│   ├── kbs.jsonl
│   ├── policies.jsonl
│   ├── feedback.jsonl
│   ├── new_orders.jsonl
│   ├── inferences.jsonl
│   └── actions.jsonl
└── kb/
    └── faiss_index/
```

说明：

- `storage/seeds/*.json` 是启动种子数据，提交到 Git，便于团队拿到仓库后有一致的初始数据。
- `storage/runtime/*.jsonl` 是运行时数据，不提交 Git，模拟数据库的当前状态和审计日志。
- `storage/kb/faiss_index/` 是知识库向量索引占位，目前保留 `.gitkeep`。
- `data/examples/` 放可提交的脱敏测试事件样例。
- `data/incoming/` 放客户脱敏样本或临时导入文件，默认忽略，不提交。
- `data/models/` 放本地训练出来的 `.pkl`，默认忽略，不提交。

代码层的 `app/storage/` 继续保留，因为它是 Repository/持久化代码包，不是业务数据目录。

## 业务链路对照

当前一笔订单可以走完整链路：

```text
POST /ingest 或本地 JSONL 导入
  -> stage_1_ingest
  -> stage_2_preprocess
  -> stage_3_rules
  -> stage_4_ml
  -> stage_5_router
  -> stage_6_agent
  -> stage_7_disposition
  -> stage_8_action
  -> stage_8_persist
  -> stage_9_feedback
```

运行产物：

- 新进单写入 `storage/runtime/orders.jsonl`。
- 进单埋点写入 `storage/runtime/new_orders.jsonl`。
- 自动或人工动作写入 `storage/runtime/actions.jsonl`。
- 推理全链路快照写入 `storage/runtime/inferences.jsonl`。
- 人工反馈写入 `storage/runtime/feedback.jsonl`。

## 已知边界

当前阶段重点是把无数据库、可演示、可测试的业务闭环跑通。下面这些不是缺文件，而是刻意留给下一阶段替换：

- Kafka/Flink：目前用 REST `/ingest` 和 JSONL 导入脚本模拟异步进单。
- PostgreSQL/Milvus/Neo4j/Redis：目前用 JSON/JSONL、本地向量占位、DiskCache 替代。
- 真实支付网关：当前只写本地动作审计，不调用真实网关。
- 持久化 FAISS：目录已经准备好，当前 RAG 是内存索引。
- WebSocket 实时推送：当前前端用刷新/API 拉取，后续可加 SSE/WebSocket 推送订单状态。

## 本次改进点

- 新增 `STORAGE_DIR=./storage` 配置。
- `settings.runtime_path` 已从 `data/runtime` 迁移到 `storage/runtime`。
- `settings.vectors_path` 已对齐到 `storage/kb/faiss_index`。
- 启动种子数据从 `storage/seeds/*.json` 加载。
- `MOCK_DATA_ENABLED=false` 时不会灌入 demo 订单/对账/反馈。
- `SEED_DEFAULT_CONFIG=true` 时仍会加载规则、模型、Agent、策略等系统配置。
- 新增 `GET /system/storage` 查看当前本地存储状态。
- 处置策略匹配补充了 `riskLevel` 和 `minConfidence` 判断。
- 人工动作接口补齐了 `force_2fa`、`freeze_account`、`add_blacklist`、`watchlist`、`notify_user` 等状态映射。
- 反馈列表接口补齐了 `reviewer` 过滤，和前端 API 参数保持一致。

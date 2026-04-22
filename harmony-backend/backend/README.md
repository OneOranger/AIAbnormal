# AI 支付异常分析系统 - 后端说明

后端当前是无数据库阶段的 FastAPI 服务，目标是先把前端 Demo、规则引擎、ML 推理、多 Agent 分析、本地文件存储和反馈闭环跑通。真实数据库、Kafka、网关执行、持久化向量库可以在下一阶段替换对应 Repository 或任务层，不影响前端 API 契约。

## 快速启动

```powershell
cd E:\AIPG\AIAbnormal\harmony-backend\backend
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m pip install -r requirements.txt
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m app.scripts.reseed_data
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问：

```text
http://localhost:8000/docs
http://localhost:8000/health
http://localhost:8000/system/storage
```

前端接后端：

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 当前目录结构

这里要区分两类 storage：

- `app/storage/` 是代码层，放 Repository、JSONL 读写、bootstrap 逻辑。
- `storage/` 是数据层，按 `backend-design-v1.md` 放 seeds、runtime、kb。

```text
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── routes_orders.py
│   │   ├── routes_recon.py
│   │   ├── routes_agent.py
│   │   ├── routes_rules.py
│   │   ├── routes_models.py
│   │   ├── routes_agents_config.py
│   │   ├── routes_policies.py
│   │   └── routes_system.py
│   ├── schemas/
│   │   ├── order.py
│   │   ├── recon.py
│   │   ├── pipeline.py
│   │   └── chat.py
│   ├── agents/
│   │   ├── graph.py
│   │   ├── specialist.py
│   │   ├── state.py
│   │   └── tools.py
│   ├── llm/
│   │   ├── base.py
│   │   ├── openai_provider.py
│   │   ├── qwen_provider.py
│   │   ├── deepseek_provider.py
│   │   ├── mock_provider.py
│   │   └── factory.py
│   ├── ml/
│   │   ├── registry.py
│   │   ├── features.py
│   │   ├── inference.py
│   │   ├── trainers/
│   │   ├── pipelines/
│   │   ├── serving/
│   │   ├── monitoring/
│   │   └── scheduler/
│   ├── rules/
│   │   ├── engine.py
│   │   └── dsl.py
│   ├── pipeline/
│   │   ├── orchestrator.py
│   │   ├── stage_1_ingest.py
│   │   ├── stage_2_preprocess.py
│   │   ├── stage_3_rules.py
│   │   ├── stage_4_ml.py
│   │   ├── stage_5_router.py
│   │   ├── stage_6_agent.py
│   │   ├── stage_7_disposition.py
│   │   ├── stage_8_action.py
│   │   ├── stage_8_persist.py
│   │   └── stage_9_feedback.py
│   ├── prompts/
│   ├── rag/
│   ├── storage/
│   │   ├── bootstrap.py
│   │   ├── jsonl_store.py
│   │   ├── orders_repo.py
│   │   ├── recon_repo.py
│   │   ├── generic_repo.py
│   │   ├── runtime_log.py
│   │   └── cache.py
│   ├── tasks/
│   ├── mocks/
│   └── scripts/
│       ├── bootstrap.py
│       ├── reseed_data.py
│       ├── train_all.py
│       └── ingest_events.py
├── storage/
│   ├── seeds/
│   │   ├── orders.json
│   │   ├── recon.json
│   │   ├── rules.json
│   │   ├── models.json
│   │   ├── agents.json
│   │   ├── kbs.json
│   │   ├── policies.json
│   │   └── feedback.json
│   ├── runtime/
│   │   ├── orders.jsonl
│   │   ├── recon.jsonl
│   │   ├── rules.jsonl
│   │   ├── models.jsonl
│   │   ├── agents.jsonl
│   │   ├── kbs.jsonl
│   │   ├── policies.jsonl
│   │   ├── feedback.jsonl
│   │   ├── new_orders.jsonl
│   │   ├── inferences.jsonl
│   │   └── actions.jsonl
│   └── kb/
│       └── faiss_index/
├── data/
│   ├── examples/
│   │   └── payment_events.jsonl
│   ├── incoming/
│   ├── models/
│   └── cache/
├── tests/
├── LOCAL_DATA_TESTING.md
├── BACKEND_DESIGN_ALIGNMENT.md
├── E2E_TESTING_GUIDE.md
├── .env.example
├── requirements.txt
└── README.md
```

## API 覆盖

前端 `harmony-flow/src/lib/api.ts` 使用到的接口已经覆盖：

```text
GET    /orders
GET    /orders/{id}
POST   /orders/{id}/actions
POST   /orders/{id}/analyze
GET    /reconciliation
POST   /reconciliation/match
POST   /agent/chat
POST   /agent/chat/stream
GET    /rules
POST   /rules
POST   /rules/{id}/toggle
GET    /models
PATCH  /models/{id}
POST   /models/{id}/retrain
GET    /agents
GET    /agents/kb
PATCH  /agents/{id}
POST   /agents/{id}/test
GET    /policies
POST   /policies
POST   /policies/{id}/toggle
GET    /feedback
POST   /feedback
POST   /ingest
GET    /system/perf
GET    /system/models
GET    /system/inferences
GET    /system/actions
GET    /system/storage
```

## 运行模式

客户演示模式：

```env
MOCK_DATA_ENABLED=true
SEED_DEFAULT_CONFIG=true
LLM_PROVIDER=mock
STORAGE_DIR=./storage
```

真实流程测试模式：

```env
MOCK_DATA_ENABLED=false
SEED_DEFAULT_CONFIG=true
LLM_PROVIDER=qwen
DASHSCOPE_API_KEY=your_dashscope_api_key_here
STORAGE_DIR=./storage
```

`MOCK_DATA_ENABLED=false` 时，后端不会自动把 demo 订单、demo 对账、demo 反馈灌入 runtime。你需要通过 `POST /ingest` 或 `app.scripts.ingest_events` 导入本地 JSONL 测试数据。

## 详细文档

- `BACKEND_DESIGN_ALIGNMENT.md`：设计文档对齐情况、已实现内容、占位内容、结构说明。
- `E2E_TESTING_GUIDE.md`：从新增测试数据到完整业务链路的端到端测试步骤。
- `LOCAL_DATA_TESTING.md`：本地数据目录、JSONL 格式、演示/真实模式说明。

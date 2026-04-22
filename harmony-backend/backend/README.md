# AI 支付异常分析系统 — 后端 (Backend)

> Python 3.10+ | FastAPI | LangGraph | XGBoost | sentence-transformers
> 多 Agent 架构,9 阶段数据流水线,完全适配前端 `src/lib/api.ts`。

## ✨ 功能总览

| 模块 | 实现技术 | 说明 |
|---|---|---|
| HTTP 层 | FastAPI + Uvicorn | 24 个 REST 端点,与前端字段 100% 对齐 |
| 多 Agent 编排 | LangGraph | Supervisor + 8 Specialist (Fraud/Behavior/Recon/Chargeback/Compliance/Knowledge/Action/Report) |
| LLM Provider | OpenAI / Qwen / DeepSeek | 按 .env Key 自动切换,无 Key 自动降级 mock |
| ML 模型 | XGBoost / IsolationForest / sentence-transformers | 真训练 + 真推理,CPU 可跑 |
| 规则引擎 | 自研 DSL | 25+ 规则,毫秒级评估 |
| RAG 知识库 | sentence-transformers + FAISS | 案例库 + 法规 + 商户画像 |
| 异步任务 | FastAPI BackgroundTasks | Agent 推理 / 模型重训 (无 Redis 依赖) |
| 定时任务 | APScheduler | 模型监控、PSI 漂移检测 |
| 缓存 | DiskCache | 替代 Redis,纯本地文件 |
| 持久化 | JSONL 文件 | data/runtime/*.jsonl |

## 🚀 快速启动 (5 分钟)

```bash
# 1. 进入目录
cd backend

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate          # macOS/Linux
# 或: .venv\Scripts\activate       # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 复制环境变量(可选,不填也能跑)
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY 或 DASHSCOPE_API_KEY 任一即可

# 5. 初始化 mock 数据 + 训练 ML 模型(首次必跑,约 30 秒)
python -m app.scripts.bootstrap

# 6. 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. 浏览器打开
# http://localhost:8000/docs   ← Swagger 自动文档
# http://localhost:8000/health ← 健康检查
```

## 🔗 前端对接

在前端项目根目录创建 `.env.local`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

然后重启前端 `npm run dev`,所有页面自动切换到真实后端。

## 📁 目录结构

```
backend/
├── app/
│   ├── main.py                 # FastAPI 入口
│   ├── config.py               # Pydantic Settings
│   │
│   ├── api/                    # HTTP 路由层 (24 个端点)
│   │   ├── routes_orders.py
│   │   ├── routes_recon.py
│   │   ├── routes_agent.py
│   │   ├── routes_rules.py
│   │   ├── routes_models.py
│   │   ├── routes_agents_config.py
│   │   └── routes_policies.py
│   │
│   ├── schemas/                # Pydantic 模型 (与前端 types.ts 一一对应)
│   │   ├── order.py
│   │   ├── recon.py
│   │   ├── pipeline.py
│   │   └── chat.py
│   │
│   ├── agents/                 # LangGraph 多 Agent
│   │   ├── graph.py            # Supervisor 编排
│   │   ├── state.py            # 共享状态机
│   │   ├── supervisor.py
│   │   ├── fraud_agent.py
│   │   ├── behavior_agent.py
│   │   ├── recon_agent.py
│   │   ├── chargeback_agent.py
│   │   ├── compliance_agent.py
│   │   ├── knowledge_agent.py
│   │   ├── action_agent.py
│   │   └── report_agent.py
│   │
│   ├── llm/                    # LLM Provider 抽象
│   │   ├── base.py             # BaseProvider
│   │   ├── openai_provider.py
│   │   ├── qwen_provider.py
│   │   ├── deepseek_provider.py
│   │   ├── mock_provider.py
│   │   └── factory.py          # 按 Key 自动选择
│   │
│   ├── ml/                     # ML 模型
│   │   ├── registry.py         # 模型注册表 + 热加载
│   │   ├── features.py         # 特征工程
│   │   ├── trainers/
│   │   │   ├── fraud_xgb.py    # XGBoost 欺诈分类
│   │   │   ├── anomaly_iforest.py  # IsolationForest 行为异常
│   │   │   ├── recon_match.py  # 对账匹配模型
│   │   │   └── embedding.py    # 文本 embedding
│   │   └── inference.py        # 统一推理接口
│   │
│   ├── rules/                  # 规则引擎
│   │   ├── engine.py           # DSL 解析 + 执行
│   │   ├── dsl.py              # 简易表达式求值
│   │   └── seed.py             # 25 条预置规则
│   │
│   ├── pipeline/               # 9 阶段数据流水线
│   │   ├── orchestrator.py     # 主入口
│   │   ├── stage_1_ingest.py
│   │   ├── stage_2_preprocess.py
│   │   ├── stage_3_rules.py
│   │   ├── stage_4_ml.py
│   │   ├── stage_5_router.py
│   │   ├── stage_6_agent.py
│   │   ├── stage_7_disposition.py
│   │   ├── stage_8_action.py
│   │   └── stage_9_feedback.py
│   │
│   ├── prompts/                # Prompt 工程模板
│   │   ├── system/
│   │   │   ├── supervisor.md
│   │   │   ├── fraud.md
│   │   │   ├── behavior.md
│   │   │   ├── recon.md
│   │   │   └── ...
│   │   └── loader.py
│   │
│   ├── rag/                    # 检索增强生成
│   │   ├── vector_store.py     # FAISS 索引
│   │   ├── retriever.py
│   │   └── seed_docs.py        # 预置案例 / 法规
│   │
│   ├── storage/                # 持久化层
│   │   ├── jsonl_store.py      # 通用 JSONL 读写
│   │   ├── orders_repo.py
│   │   ├── recon_repo.py
│   │   ├── feedback_repo.py
│   │   └── cache.py            # DiskCache 封装
│   │
│   ├── tasks/                  # 异步任务
│   │   ├── background.py       # FastAPI BackgroundTasks 包装
│   │   └── scheduler.py        # APScheduler (模型重训/监控)
│   │
│   ├── mocks/                  # Mock 数据生成器(种子可重复)
│   │   ├── order_factory.py
│   │   ├── recon_factory.py
│   │   └── pipeline_factory.py
│   │
│   └── scripts/                # 维护脚本
│       ├── bootstrap.py        # 一键初始化数据 + 训练
│       ├── train_all.py        # 重训所有 ML 模型
│       └── reseed_data.py      # 重新生成 mock 数据
│
├── data/                       # 运行时数据(自动生成)
│   ├── runtime/                # JSONL: orders/recon/feedback
│   ├── models/                 # 训练好的 .pkl 模型
│   ├── vectors/                # FAISS 向量索引
│   └── cache/                  # DiskCache 文件
│
├── tests/                      # pytest
│   ├── test_api_orders.py
│   ├── test_pipeline.py
│   └── test_agents.py
│
├── .env.example
├── requirements.txt
└── README.md
```

## 🧪 测试方式

本地 JSONL 数据、mock 开关、真实 LLM 测试流程详见 `LOCAL_DATA_TESTING.md`。

详见 `TESTING.md`,涵盖:
- API 单元测试 (pytest)
- 端到端流水线测试
- 前端联调清单
- Postman 集合
- 性能压测脚本

## 🔄 迭代说明

- **加新 LLM Provider**: 在 `app/llm/` 新增一个继承 `BaseProvider` 的类即可
- **加新 Agent**: 在 `app/agents/` 复制一个 _agent.py + 在 `graph.py` 注册节点
- **加新规则**: 在 `app/rules/seed.py` 追加 dict,或调用 `POST /rules`
- **改 Prompt**: 修改 `app/prompts/system/*.md`,无需重启(热加载)
- **接真实 Kafka/Celery**: 把 `app/tasks/background.py` 替换成 Celery 实现,其它不变

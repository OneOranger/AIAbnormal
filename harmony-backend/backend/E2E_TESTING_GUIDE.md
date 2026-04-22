# 端到端测试文档

本文档用于从 0 开始测试后端完整业务流程：自己新增数据、导入数据、触发规则/ML/Agent/处置、查看审计快照、提交反馈，并联调前端页面。

## 1. 测试前准备

进入后端目录：

```powershell
cd E:\AIPG\AIAbnormal\harmony-backend\backend
```

确认使用项目根目录已有虚拟环境：

```powershell
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe --version
```

安装依赖：

```powershell
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

生成或重置种子数据：

```powershell
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m app.scripts.reseed_data
```

运行自动化测试：

```powershell
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m pytest -q
```

## 2. 选择运行模式

### 2.1 客户演示模式

适合演示页面、规则、模型配置、Agent 配置、对账、反馈闭环，不需要真实大模型 Key。

`.env` 推荐：

```env
STORAGE_DIR=./storage
DATA_DIR=./data
MOCK_DATA_ENABLED=true
SEED_DEFAULT_CONFIG=true
LLM_PROVIDER=mock
```

行为：

- `storage/seeds/*.json` 作为初始数据。
- `storage/runtime/*.jsonl` 为空时自动灌入 demo 订单、demo 对账、demo 反馈。
- LLM 走 mock，不消耗真实大模型额度。

### 2.2 真实业务流程测试模式

适合测试真实大模型、真实进单、完整业务链路。

`.env` 推荐：

```env
STORAGE_DIR=./storage
DATA_DIR=./data
MOCK_DATA_ENABLED=false
SEED_DEFAULT_CONFIG=true
LLM_PROVIDER=qwen
DASHSCOPE_API_KEY=your_dashscope_api_key_here
```

也可以切换 OpenAI 或 DeepSeek：

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
```

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

行为：

- 不自动生成 demo 订单、demo 对账、demo 反馈。
- 规则、模型元数据、Agent、策略配置仍从 seed 加载，保证流水线能跑。
- 订单必须通过 `POST /ingest` 或 JSONL 导入脚本进入系统。

## 3. 数据目录说明

```text
harmony-backend/backend/storage/seeds/
  orders.json       # 启动种子订单，JSON 数组，可提交 Git
  recon.json        # 启动种子对账数据，JSON 数组，可提交 Git
  rules.json        # 规则配置种子
  models.json       # 模型元数据种子
  agents.json       # Agent 配置种子
  kbs.json          # 知识库配置种子
  policies.json     # 处置策略种子
  feedback.json     # 反馈种子

harmony-backend/backend/storage/runtime/
  orders.jsonl      # 当前本地订单主数据，运行时生成，不提交 Git
  recon.jsonl       # 当前本地对账主数据，运行时生成，不提交 Git
  new_orders.jsonl  # 进单埋点
  inferences.jsonl  # 每次推理全链路快照
  actions.jsonl     # 自动/人工动作审计
  feedback.jsonl    # 人工反馈记录

harmony-backend/backend/storage/kb/faiss_index/
  .gitkeep          # FAISS 持久化索引占位，后续可接入真实索引

harmony-backend/backend/data/examples/
  payment_events.jsonl  # 可提交的脱敏测试事件样例

harmony-backend/backend/data/incoming/
  customer_sample_xxx.jsonl # 客户脱敏样本，默认忽略，不提交 Git

harmony-backend/backend/data/models/
  *.pkl             # 本地训练模型产物，默认忽略，不提交 Git
```

## 4. 自己新增测试数据

推荐使用 JSONL：一行一个 JSON 对象，最接近 Kafka/SFTP/Webhook 批量异步进单。

新建文件示例：

```text
harmony-backend/backend/data/incoming/my_payment_events.jsonl
```

最小字段：

| 字段 | 必填 | 示例 | 说明 |
|---|---|---|---|
| `orderNo` | 是 | `PAY-MY-000001` | 订单号或交易号 |
| `userId` | 是 | `U10001` | 用户 ID |
| `amount` | 是 | `68000` | 支付金额 |
| `eventTime` | 建议 | `2026-04-22T02:14:00Z` | ISO 时间 |
| `currency` | 建议 | `CNY` | `CNY`、`USD`、`EUR` |
| `channel` | 建议 | `visa` | `alipay`、`wechat`、`unionpay`、`visa`、`mastercard`、`stripe`、`paypal`、`applepay`、`bank_transfer` |
| `ip` | 建议 | `45.12.88.10` | 用户 IP |
| `ipCountry` | 建议 | `RU` | IP 国家或地区代码 |
| `device` | 建议 | `Headless Chrome` | 设备或 User-Agent 摘要 |
| `deviceId` | 建议 | `DEV-RISK-001` | 设备 ID 或指纹 |
| `merchantId` | 建议 | `M10001` | 商户 ID |
| `merchantName` | 建议 | `跨境数码店` | 商户名 |

高风险样例：

```json
{"orderNo":"PAY-MY-000001","eventTime":"2026-04-22T02:14:00Z","userId":"U10001","merchantId":"M10001","merchantName":"跨境数码店","amount":68000,"currency":"CNY","channel":"visa","ip":"45.12.88.10","ipCountry":"RU","device":"Headless Chrome","deviceId":"DEV-RISK-001"}
```

低风险样例：

```json
{"orderNo":"PAY-MY-000002","eventTime":"2026-04-22T10:20:00Z","userId":"U10002","merchantId":"M10002","merchantName":"本地生活商户","amount":129,"currency":"CNY","channel":"wechat","ip":"120.42.18.9","ipCountry":"CN","device":"iPhone 15 Pro","deviceId":"DEV-NORMAL-002"}
```

中高风险样例：

```json
{"orderNo":"PAY-MY-000003","eventTime":"2026-04-22T18:45:00Z","userId":"U10003","merchantId":"M10003","merchantName":"游戏充值平台","amount":12000,"currency":"USD","channel":"stripe","ip":"196.251.10.22","ipCountry":"NG","device":"Emulator-X86","deviceId":"DEV-RISK-003"}
```

## 5. 导入本地 JSONL 并跑完整流程

只导入订单，不立即跑流水线：

```powershell
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m app.scripts.ingest_events data/examples/payment_events.jsonl
```

导入并立即跑完整 9 阶段流水线：

```powershell
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m app.scripts.ingest_events data/examples/payment_events.jsonl --run-pipeline
```

如果你把自己的文件放在 `data/incoming/my_payment_events.jsonl`：

```powershell
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m app.scripts.ingest_events data/incoming/my_payment_events.jsonl --run-pipeline
```

导入后检查：

```powershell
Get-Content .\storage\runtime\orders.jsonl -Tail 5
Get-Content .\storage\runtime\inferences.jsonl -Tail 3
Get-Content .\storage\runtime\actions.jsonl -Tail 3
```

## 6. 启动服务并用 HTTP 测试

启动后端：

```powershell
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：

```powershell
Invoke-RestMethod http://localhost:8000/health
```

查看本地存储状态：

```powershell
Invoke-RestMethod http://localhost:8000/system/storage
```

提交一条生产风格订单事件：

```powershell
$body = @{
  orderNo = "PAY-HTTP-000001"
  eventTime = "2026-04-22T02:14:00Z"
  userId = "UHTTP001"
  merchantId = "MHTTP001"
  merchantName = "HTTP测试商户"
  amount = 88000
  currency = "CNY"
  channel = "visa"
  ip = "45.12.88.10"
  ipCountry = "RU"
  device = "Headless Chrome"
  deviceId = "DEV-HTTP-001"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/ingest" -ContentType "application/json" -Body $body
```

查询订单列表：

```powershell
Invoke-RestMethod "http://localhost:8000/orders?page=1&pageSize=5"
```

触发指定订单分析：

```powershell
Invoke-RestMethod -Method Post "http://localhost:8000/orders/PAY-HTTP-000001/analyze"
```

查看最近推理快照：

```powershell
Invoke-RestMethod "http://localhost:8000/system/inferences?n=5"
```

查看最近动作审计：

```powershell
Invoke-RestMethod "http://localhost:8000/system/actions?n=5"
```

## 7. 验证 9 阶段是否跑完

`/orders/{id}/analyze` 返回的 `trace.stages` 应包含：

```text
0_ingest
1_preprocess
2_rules
3_ml_ensemble
4_route
5_agent
6_disposition
7_action
8_persist
9_feedback
```

如果订单是低风险，可能短路在 `low_risk_release`，不会进入 Agent。

如果规则命中强拦截，可能短路在 `rule_hard_intercept`，不会进入 ML/Agent。

这两个短路不是错误，是设计文档里的低延迟路径。

## 8. 测试对账流程

查看对账列表：

```powershell
Invoke-RestMethod "http://localhost:8000/reconciliation?status=all"
```

触发一键对账：

```powershell
Invoke-RestMethod -Method Post "http://localhost:8000/reconciliation/match"
```

预期返回：

```json
{
  "ok": true,
  "total": 480,
  "matched": 123,
  "discrepancy": 357,
  "totalDiff": 12345.67,
  "durationMs": 10,
  "message": "AI 对账匹配完成"
}
```

同时会写入：

```text
storage/runtime/actions.jsonl
```

## 9. 测试人工动作和反馈闭环

人工执行动作：

```powershell
$action = @{ action = "review" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/orders/PAY-HTTP-000001/actions" -ContentType "application/json" -Body $action
```

提交反馈：

```powershell
$feedback = @{
  orderNo = "PAY-HTTP-000001"
  originalAction = "review"
  aiSuggestion = "review"
  finalAction = "intercept"
  reviewer = "测试审核员"
  reviewedAt = "2026-04-22T12:00:00Z"
  isCorrect = $false
  feedbackType = "override"
  comment = "人工复核发现设备风险更高，改为拦截。"
  fedToRAG = $true
  fedToTraining = $true
  ruleSuggestion = "device.headless = true AND amount > 5000"
  estimatedSavedLoss = 88000
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/feedback" -ContentType "application/json" -Body $feedback
```

查看反馈：

```powershell
Invoke-RestMethod "http://localhost:8000/feedback?reviewer=测试审核员"
```

## 10. 测试配置接口

规则列表：

```powershell
Invoke-RestMethod http://localhost:8000/rules
```

禁用规则：

```powershell
$body = @{ enabled = $false } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/rules/rule-1/toggle" -ContentType "application/json" -Body $body
```

模型列表：

```powershell
Invoke-RestMethod http://localhost:8000/models
```

触发模型重训：

```powershell
Invoke-RestMethod -Method Post "http://localhost:8000/models/fraud-xgb-v2/retrain"
```

Agent 列表：

```powershell
Invoke-RestMethod http://localhost:8000/agents
```

Agent Playground：

```powershell
$body = @{ input = "分析订单 PAY-HTTP-000001 的风险原因" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/agents/agent-fraud/test" -ContentType "application/json" -Body $body
```

策略列表：

```powershell
Invoke-RestMethod http://localhost:8000/policies
```

## 11. 前端联调

后端启动后，设置前端环境：

```powershell
cd E:\AIPG\AIAbnormal\harmony-flow
```

创建或修改 `.env.local`：

```env
VITE_API_BASE_URL=http://localhost:8000
```

启动前端：

```powershell
npm run dev
```

页面检查清单：

- 首页：统计卡片、趋势图、异常分类是否来自后端订单。
- 订单页：筛选、搜索、分页是否请求 `/orders`。
- 订单详情页：是否请求 `/orders/{id}`。
- 订单分析按钮：是否请求 `/orders/{id}/analyze` 并生成报告。
- 对账页：是否请求 `/reconciliation`，一键对账是否请求 `/reconciliation/match`。
- 规则配置：是否请求 `/rules`。
- 模型配置：是否请求 `/models`。
- Agent 配置：是否请求 `/agents`、`/agents/kb`。
- 处置/反馈：是否请求 `/policies`、`/feedback`。

如果移除 `VITE_API_BASE_URL`，前端会回到自己的 mock 数据，不影响客户演示。

## 12. 重置本地运行数据

只清空运行数据，不动 seed：

```powershell
Remove-Item .\storage\runtime\*.jsonl -Force
```

然后重启后端。

演示模式下，后端会从 `storage/seeds/*.json` 重新生成 runtime。

真实流程模式下，后端不会自动生成 demo 订单，你需要重新导入 JSONL 或调用 `/ingest`。

## 13. 验证真实大模型是否启用

```powershell
Invoke-RestMethod http://localhost:8000/health
```

关注返回字段：

```json
{
  "llm_provider": "qwen"
}
```

如果返回 `mock`，说明当前没有走真实大模型。检查：

- `.env` 中 `LLM_PROVIDER` 是否正确。
- 对应 API Key 是否存在。
- 后端是否已重启。

## 14. 常见问题

如果 `/orders` 没有数据：

- 检查 `MOCK_DATA_ENABLED`。
- 检查 `storage/runtime/orders.jsonl` 是否存在。
- 调用 `GET /system/storage` 看 seed/runtime 计数。
- 真实流程模式下需要先导入 JSONL 或调用 `/ingest`。

如果 Agent 很慢：

- 真实 LLM 会受网络和模型响应影响。
- 演示时建议 `LLM_PROVIDER=mock`。
- 首次 RAG embedding 可能加载模型，第一次会慢，后面会快。

如果不想提交客户样本：

- 放到 `data/incoming/`。
- 该目录已被 `.gitignore` 忽略。

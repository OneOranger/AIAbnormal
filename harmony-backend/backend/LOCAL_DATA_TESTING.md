# 本地数据与真实流程测试说明

本项目当前阶段不接数据库。后端统一使用 `harmony-backend/backend/data` 目录模拟数据库、模型文件、向量索引、缓存和生产异步数据入口。

## 1. 两种运行模式

### 客户演示模式

适合没有真实数据、需要快速展示完整页面和业务闭环的场景。

`.env` 建议配置:

```env
MOCK_DATA_ENABLED=true
SEED_DEFAULT_CONFIG=true
LLM_PROVIDER=mock
```

行为说明:

- 后端启动时如果 `data/runtime/orders.jsonl` 为空,会自动生成异常订单 mock 数据。
- 后端启动时如果 `data/runtime/recon.jsonl` 为空,会自动生成对账 mock 数据。
- 后端启动时如果 `data/runtime/feedback.jsonl` 为空,会自动生成反馈 mock 数据。
- 前端如果不配置 `VITE_API_BASE_URL`,仍然保留并使用前端内置 mock 数据。
- 前端如果配置 `VITE_API_BASE_URL=http://localhost:8000`,会使用后端生成的 mock 数据。

### 真实流程测试模式

适合测试真实大模型、真实业务链路、手工构造生产风格数据的场景。

`.env` 建议配置:

```env
MOCK_DATA_ENABLED=false
SEED_DEFAULT_CONFIG=true
LLM_PROVIDER=qwen
DASHSCOPE_API_KEY=your_dashscope_api_key_here
```

也可以改为:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
```

行为说明:

- 后端不会自动生成订单、对账、反馈 mock 数据。
- 规则、模型、Agent、策略等系统配置仍会保留默认种子,便于流水线正常跑起来。
- 测试订单需要通过 `POST /ingest` 或本地 JSONL 导入脚本进入 `data/runtime/orders.jsonl`。
- 前端需要配置 `VITE_API_BASE_URL=http://localhost:8000`,否则仍会走前端 mock。

## 2. 数据目录说明

```text
harmony-backend/backend/data/
  examples/
    payment_events.jsonl      # 可提交到 Git 的示例测试数据
  runtime/
    orders.jsonl              # 本地订单主数据,模拟订单数据库
    recon.jsonl               # 本地对账主数据,模拟对账数据库
    rules.jsonl               # 风控规则配置
    models.jsonl              # ML 模型元数据
    agents.jsonl              # Agent 配置
    kbs.jsonl                 # 知识库配置
    policies.jsonl            # 自动处置策略
    feedback.jsonl            # 人工反馈记录
    new_orders.jsonl          # 进单埋点
    inferences.jsonl          # 9 阶段推理快照
    actions.jsonl             # 处置动作与对账动作审计
  models/
    *.pkl                     # 本地训练出的模型文件
  vectors/
    ...                       # RAG/向量索引占位
  cache/
    ...                       # DiskCache 本地缓存
```

注意:

- `runtime/*.jsonl` 是运行数据,默认不提交到 Git。
- `models/*.pkl` 是模型产物,默认不提交到 Git。
- `examples/*.jsonl` 是示例数据,可以提交,不要放真实客户敏感信息。

## 3. 生产风格订单事件格式

推荐把测试订单写成 JSONL。JSONL 是“一行一个 JSON 对象”,适合模拟 Kafka、SFTP 批文件、Webhook 等生产异步输入。

最小字段:

| 字段 | 必填 | 示例 | 说明 |
|---|---|---|---|
| `orderNo` | 是 | `PAY-DEMO-900001` | 订单号或交易号 |
| `eventTime` | 建议 | `2026-04-22T02:14:00Z` | 交易发生时间,ISO 格式 |
| `userId` | 是 | `U900001` | 用户 ID |
| `amount` | 是 | `68000` | 支付金额 |
| `currency` | 建议 | `CNY` | 支持 `CNY`、`USD`、`EUR` |
| `channel` | 建议 | `visa` | 支持 `alipay`、`wechat`、`unionpay`、`visa`、`mastercard`、`stripe`、`paypal`、`applepay`、`bank_transfer` |
| `ip` | 建议 | `45.12.88.10` | 用户 IP |
| `ipCountry` | 建议 | `RU` | IP 国家或地区代码 |
| `device` | 建议 | `Headless Chrome` | 设备或 User-Agent 摘要 |
| `deviceId` | 建议 | `DEV-RISK-001` | 设备 ID 或指纹 |
| `merchantId` | 建议 | `M10001` | 商户 ID |
| `merchantName` | 建议 | `跨境数码店` | 商户名称 |

可选字段:

| 字段 | 示例 | 说明 |
|---|---|---|
| `userName` | `测试用户A` | 用户显示名 |
| `merchant_name` | `跨境数码店` | 兼容蛇形命名 |
| `orderAmount` | `68000` | 兼容不同业务系统字段名 |
| `paymentChannel` | `visa` | 兼容不同业务系统字段名 |
| `clientIp` | `45.12.88.10` | 兼容不同业务系统字段名 |
| `deviceFingerprint` | `FP-xxx` | 如果已有设备指纹,可直接传 |

示例:

```json
{"orderNo":"PAY-DEMO-900001","eventTime":"2026-04-22T02:14:00Z","userId":"U900001","userName":"测试用户A","merchantId":"M10001","merchantName":"跨境数码店","amount":68000,"currency":"CNY","channel":"visa","ip":"45.12.88.10","ipCountry":"RU","device":"Headless Chrome","deviceId":"DEV-RISK-001"}
```

## 4. 放在哪里

推荐路径:

```text
harmony-backend/backend/data/examples/payment_events.jsonl
```

你可以新增自己的文件:

```text
harmony-backend/backend/data/examples/payment_events_high_risk.jsonl
harmony-backend/backend/data/examples/payment_events_low_risk.jsonl
harmony-backend/backend/data/examples/payment_events_recon_mix.jsonl
```

如果是客户真实数据脱敏样本,建议放在不提交 Git 的本地目录:

```text
harmony-backend/backend/data/incoming/customer_sample_20260422.jsonl
```

如需防止误提交,可以把 `data/incoming/` 加入 `.gitignore`。

## 5. 如何导入测试数据

先进入后端目录:

```powershell
cd E:\AIPG\AIAbnormal\harmony-backend\backend
```

使用已创建好的虚拟环境运行:

```powershell
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m app.scripts.ingest_events data/examples/payment_events.jsonl
```

导入并立刻跑完整 9 阶段流水线:

```powershell
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m app.scripts.ingest_events data/examples/payment_events.jsonl --run-pipeline
```

导入后数据会写入:

```text
harmony-backend/backend/data/runtime/orders.jsonl
```

如果使用 `--run-pipeline`,还会写入:

```text
harmony-backend/backend/data/runtime/new_orders.jsonl
harmony-backend/backend/data/runtime/inferences.jsonl
harmony-backend/backend/data/runtime/actions.jsonl
```

## 6. 用 HTTP 模拟生产异步进单

启动后端:

```powershell
cd E:\AIPG\AIAbnormal\harmony-backend\backend
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

提交一条订单事件:

```powershell
$body = @{
  orderNo = "PAY-DEMO-HTTP-001"
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

`/ingest` 会先把事件转换为 `AnomalyOrder`,写入本地 JSONL,再异步触发完整流水线。

## 7. 前端如何切换

前端保留 mock 数据。是否走后端只由 `harmony-flow/.env.local` 控制。

前端 mock 模式:

```env
# 不设置 VITE_API_BASE_URL
```

后端真实接口模式:

```env
VITE_API_BASE_URL=http://localhost:8000
```

然后重启前端:

```powershell
cd E:\AIPG\AIAbnormal\harmony-flow
npm run dev
```

## 8. 如何确认走的是真实大模型

查看健康检查:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

关键字段:

```json
{
  "llm_provider": "qwen"
}
```

如果看到:

```json
{
  "llm_provider": "mock"
}
```

说明当前仍是 mock LLM。检查 `.env` 的 `LLM_PROVIDER` 和 API Key,然后重启后端。

## 9. 如何重置本地运行数据

如果要重新开始一轮测试,可以备份或删除这些运行文件:

```text
data/runtime/orders.jsonl
data/runtime/recon.jsonl
data/runtime/feedback.jsonl
data/runtime/new_orders.jsonl
data/runtime/inferences.jsonl
data/runtime/actions.jsonl
```

演示模式下,删除后重启后端会重新生成 mock 数据。

真实流程测试模式下,删除后不会自动生成订单,需要重新导入 JSONL 或调用 `/ingest`。

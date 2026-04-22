# 本地数据与真实流程测试说明

当前阶段暂不接数据库。后端使用本地文件模拟数据库、事件总线、审计日志和知识库占位。

## 目录分层

```text
harmony-backend/backend/storage/
  seeds/                 # 启动种子数据，JSON 数组，可提交 Git
  runtime/               # 运行时数据，JSONL 追加/重写，不提交 Git
  kb/faiss_index/        # FAISS 持久化索引占位

harmony-backend/backend/data/
  examples/              # 可提交的脱敏测试事件
  incoming/              # 客户脱敏样本或临时测试文件，不提交 Git
  models/                # 本地训练模型 .pkl，不提交 Git
  cache/                 # DiskCache，不提交 Git
```

## 两种模式

客户演示：

```env
MOCK_DATA_ENABLED=true
SEED_DEFAULT_CONFIG=true
LLM_PROVIDER=mock
STORAGE_DIR=./storage
```

真实流程测试：

```env
MOCK_DATA_ENABLED=false
SEED_DEFAULT_CONFIG=true
LLM_PROVIDER=qwen
DASHSCOPE_API_KEY=your_dashscope_api_key_here
STORAGE_DIR=./storage
```

## 数据格式

生产风格进单推荐 JSONL，一行一条：

```json
{"orderNo":"PAY-DEMO-900001","eventTime":"2026-04-22T02:14:00Z","userId":"U900001","merchantId":"M10001","merchantName":"跨境数码店","amount":68000,"currency":"CNY","channel":"visa","ip":"45.12.88.10","ipCountry":"RU","device":"Headless Chrome","deviceId":"DEV-RISK-001"}
```

最小必填：

| 字段 | 说明 |
|---|---|
| `orderNo` | 订单号 |
| `userId` | 用户 ID |
| `amount` | 支付金额 |

强烈建议同时提供：

| 字段 | 说明 |
|---|---|
| `eventTime` | 交易时间 |
| `currency` | 币种 |
| `channel` | 支付渠道 |
| `ip` | 用户 IP |
| `ipCountry` | IP 国家/地区 |
| `device` | 设备/User-Agent |
| `deviceId` | 设备 ID/指纹 |
| `merchantId` | 商户 ID |
| `merchantName` | 商户名称 |

## 导入测试数据

```powershell
cd E:\AIPG\AIAbnormal\harmony-backend\backend
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m app.scripts.ingest_events data/examples/payment_events.jsonl --run-pipeline
```

导入后查看：

```powershell
Get-Content .\storage\runtime\orders.jsonl -Tail 5
Get-Content .\storage\runtime\inferences.jsonl -Tail 3
Get-Content .\storage\runtime\actions.jsonl -Tail 3
```

## HTTP 进单

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

## 重置数据

只清空运行时数据：

```powershell
Remove-Item .\storage\runtime\*.jsonl -Force
```

重新生成 seed 和 runtime：

```powershell
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m app.scripts.reseed_data
```

完整端到端测试步骤见 `E2E_TESTING_GUIDE.md`。

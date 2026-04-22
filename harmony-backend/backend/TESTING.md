# 测试入口

详细端到端步骤请看：`E2E_TESTING_GUIDE.md`。

## 后端自动化测试

```powershell
cd E:\AIPG\AIAbnormal\harmony-backend\backend
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m pytest -q
```

## 后端启动

```powershell
cd E:\AIPG\AIAbnormal\harmony-backend\backend
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 常用检查

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/system/storage
Invoke-RestMethod "http://localhost:8000/orders?page=1&pageSize=5"
Invoke-RestMethod -Method Post http://localhost:8000/reconciliation/match
```

## 本地 JSONL 导入

```powershell
E:\AIPG\AIAbnormal\.venv\Scripts\python.exe -m app.scripts.ingest_events data/examples/payment_events.jsonl --run-pipeline
```

## 前端联调

在 `E:\AIPG\AIAbnormal\harmony-flow\.env.local` 中设置：

```env
VITE_API_BASE_URL=http://localhost:8000
```

然后启动前端：

```powershell
cd E:\AIPG\AIAbnormal\harmony-flow
npm run dev
```

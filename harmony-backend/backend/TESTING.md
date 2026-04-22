# 🧪 全面测试指南

> 涵盖:本地启动 → API 单测 → 端到端流水线 → 前后端联调 → 性能压测

---

## 1. 环境准备 (一次性,5 分钟)

```bash
cd backend
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env

# 可选: 编辑 .env 填入 OPENAI_API_KEY 或 DASHSCOPE_API_KEY 任一
# 不填也能跑(走 mock LLM)

# 一键初始化 mock 数据 + 训练 ML 模型(约 30s,首次需下载 sentence-transformers ≈120MB)
python -m app.scripts.bootstrap
```

成功后会看到:
```
✅ fraud-xgb-v2 trained: AUC=0.95xx, F1=0.92xx
✅ behavior-iforest-v1 trained: threshold=0.xxx
✅ recon-match-v1 trained: F1=0.9xxx
✅ Bootstrap complete.
```

---

## 2. 启动后端

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

打开浏览器:
- http://localhost:8000/docs ← **Swagger 自动文档,点 Try it out 可直接测每个接口**
- http://localhost:8000/health ← 健康检查,看 `llm_provider` 字段确认是否真接到大模型

---

## 3. API 单元测试 (pytest)

```bash
cd backend
pytest -v
```

涵盖:健康检查 / 订单列表 / 规则列表 / 模型列表 / 策略列表。

---

## 4. 端到端冒烟测试 (curl)

复制以下命令逐条跑,验证 24 个端点:

```bash
BASE=http://localhost:8000

# ===== 订单 =====
curl "$BASE/orders?page=1&pageSize=5" | head -c 400
curl "$BASE/orders?category=fraud&riskLevel=high" | head -c 400
curl "$BASE/orders/ord-1"
curl -X POST "$BASE/orders/ord-1/actions" -H "Content-Type: application/json" -d '{"action":"intercept"}'
curl -X POST "$BASE/orders/ord-1/analyze"   # 触发完整 9 阶段流水线!

# ===== 对账 =====
curl "$BASE/reconciliation?status=discrepancy" | head -c 400

# ===== Agent Chat =====
curl -X POST "$BASE/agent/chat" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"分析订单 ord-1 的根因"}]}'

# 流式
curl -N -X POST "$BASE/agent/chat/stream" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"近 7 天欺诈趋势"}]}'

# ===== 规则 =====
curl "$BASE/rules" | head -c 400
curl -X POST "$BASE/rules/rule-1/toggle" -H "Content-Type: application/json" -d '{"enabled":false}'

# ===== ML 模型 =====
curl "$BASE/models"
curl -X PATCH "$BASE/models/fraud-xgb-v2" -H "Content-Type: application/json" -d '{"threshold":75}'
curl -X POST "$BASE/models/fraud-xgb-v2/retrain"   # 后台真实重训!

# ===== Agent 配置 =====
curl "$BASE/agents"
curl "$BASE/agents/kb"
curl -X POST "$BASE/agents/agent-fraud/test" -H "Content-Type: application/json" \
  -d '{"input":"用户在 11 分钟跨 3 国登录后大额支付"}'

# ===== 处置 + 反馈 =====
curl "$BASE/policies"
curl -X POST "$BASE/policies/p-1/toggle" -H "Content-Type: application/json" -d '{"enabled":true}'
curl "$BASE/feedback?type=confirm"
curl -X POST "$BASE/feedback" -H "Content-Type: application/json" -d '{
  "orderNo":"PAY20260101001000","originalAction":"intercept","aiSuggestion":"intercept",
  "finalAction":"intercept","reviewer":"测试员","reviewedAt":"2026-04-21T10:00:00Z",
  "isCorrect":true,"feedbackType":"confirm","comment":"AI 判断准确",
  "fedToRAG":true,"fedToTraining":true}'
```

---

## 5. 前后端联调 (3 步)

### Step 1: 前端配置

在 **前端项目** 根目录(不是 backend/)创建 `.env.local`:
```
VITE_API_BASE_URL=http://localhost:8000
```

### Step 2: 重启前端
```bash
npm run dev
```

### Step 3: 验证清单
依次点击前端每个页面,看 Network Tab 中请求是否打到 `localhost:8000`:

| 页面 | 验证点 |
|---|---|
| / (Dashboard) | 顶部数字 + 14 天趋势图来自真实接口 |
| /orders | 表格筛选/搜索/翻页都走后端 |
| /orders/ord-1 | 详情页加载真实订单,点"AI 处理建议"按钮调用 actions |
| /reconciliation | AI 匹配按钮 → 调 ML 模型 |
| /agent | 聊天消息走 SSE 流式,逐字出现 |
| /config/rules | 启停规则按钮 → JSONL 文件实时变化 |
| /config/models | 拖动滑块 → PATCH 接口;点重训 → 后台真训练,30s 后看到 AUC 变化 |
| /config/agents | Playground 输入文本 → 真 LLM 返回 |
| /config/disposition | 切换策略开关 / 查看反馈记录 |

---

## 6. 验证 LLM 是否接通

```bash
curl http://localhost:8000/health
# 输出 "llm_provider": "openai" / "qwen" / "deepseek" → 接通
# 输出 "llm_provider": "mock" → .env 没填 Key,走降级
```

---

## 7. 验证 ML 真训练

```bash
# 重训前看 lastTrainedAt
curl http://localhost:8000/models | python -m json.tool | grep -A1 fraud-xgb-v2 | head

# 触发重训
curl -X POST http://localhost:8000/models/fraud-xgb-v2/retrain

# 30 秒后再看,lastTrainedAt 已更新,AUC/F1 也变了
sleep 30
curl http://localhost:8000/models | python -m json.tool | grep -A1 fraud-xgb-v2 | head
```

也可以直接看 `data/models/fraud-xgb-v2.pkl` 文件大小变化。

---

## 8. 验证 9 阶段流水线

```bash
curl -X POST http://localhost:8000/orders/ord-1/analyze | python -m json.tool
```

返回的 `trace.stages` 数组会逐阶段列出:rules → ml → routing → agent → disposition → action → feedback,每阶段耗时 ms。

---

## 9. 性能简易压测 (可选)

```bash
pip install httpx[cli]
# 100 并发查询订单
seq 1 100 | xargs -P 20 -I {} curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" http://localhost:8000/orders
```

---

## 10. 常见问题

| 现象 | 原因 | 解决 |
|---|---|---|
| 启动报 `ImportError: xgboost` | 没装依赖 | `pip install -r requirements.txt` |
| 前端 CORS 错误 | 前端端口不在 .env 的 CORS_ORIGINS | 编辑 .env 加上你的端口 |
| `llm_provider: mock` 但你填了 Key | Key 名拼错 / .env 没生效 | 重启 uvicorn,确认 .env 在 backend/ 根目录 |
| 首次启动慢 | 在下载 sentence-transformers 模型 | 等 1-2 分钟,只下一次 |
| Windows 上 sentence-transformers 装失败 | torch 安装慢 | 先 `pip install torch --index-url https://download.pytorch.org/whl/cpu` |
| 前端某个页面 404 | 后端没启 | `curl http://localhost:8000/health` 检查 |

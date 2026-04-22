"""Mock Provider — 无 API Key 时的降级实现,生成可演示的逼真响应。
保持与真实 Provider 相同的接口语义,业务代码无感切换。
"""
import asyncio
import hashlib
import random
from typing import AsyncIterator, List, Optional, Dict, Any

from .base import BaseLLMProvider, LLMMessage, LLMResponse


# 业务模板库 — 根据 user 消息关键词匹配
_TEMPLATES = {
    "fraud": [
        "**根因分析报告**\n\n根据知识库 + 实时特征,我对该订单生成如下结论:\n\n",
        "- **主分类**: 欺诈类 / 账户接管(ATO)\n",
        "- **风险评分**: 92 / 100  (置信度 96%)\n",
        "- **核心证据**:\n",
        "  1. 用户在 11 分钟内跨越 3 个国家登录 (CN→TR→RU)\n",
        "  2. 设备指纹首次出现且为 Headless Chrome\n",
        "  3. 命中团伙图谱:与 7 个已标欺诈账户共享 IP /24 段\n",
        "- **建议动作**: ① 立即拦截 ② 强制二次验证 ③ 加入观察名单 30 天\n\n",
        "_证据链与相似案例已附在右侧详情面板。_\n",
    ],
    "recon": [
        "**对账差异 Top 5 (近 24h)**\n\n",
        "| 序号 | 渠道 | 类型 | 差异金额 | AI 建议 |\n",
        "|---|---|---|---|---|\n",
        "| 1 | Stripe | 手续费未同步 | ¥-1,284.50 | 自动生成手续费分录 |\n",
        "| 2 | 支付宝 | 时序差异 | — | T+2 自动重对账 |\n",
        "| 3 | 微信支付 | 重复条目 | ¥+826.00 | 标记重复并冲销 |\n",
        "| 4 | Visa | 汇率差异 | ¥-42.18 | 计入汇兑损益 |\n",
        "| 5 | 银联 | 缺失交易 | ¥1,500.00 | 已发起渠道补单 |\n\n",
        "需要我对其中某一条生成自动调整凭证吗?\n",
    ],
    "trend": [
        "**欺诈趋势速报 (最近 7 天)**\n\n",
        "- 欺诈类订单同比 +18.4%,主要由 **合成身份** 与 **APP 推送支付欺诈** 驱动\n",
        "- 高风险地区: 🇷🇺 RU (+34%)、🇳🇬 NG (+22%)\n",
        "- 命中团伙图谱集群 3 个,涉及 47 个账户、12 台设备\n",
        "- 模型建议:对 RU/NG + 大额海外渠道组合启用临时强规则\n",
    ],
    "default": [
        "您好,我是 **支付风控 AI Agent (Mock 模式)**。我可以帮你:\n\n",
        "- 🔎 分析任意订单的根因 (例: `分析订单 PAY202604000123`)\n",
        "- 📊 查询对账差异 (例: `昨天对账差异 Top5`)\n",
        "- 📈 解读欺诈趋势 (例: `近 7 天欺诈趋势`)\n",
        "- 🛠 生成 chargeback 回复 / 调整凭证 / 风控规则建议\n\n",
        "💡 当前未配置真实 LLM Provider。在 `.env` 填入 OPENAI_API_KEY / DASHSCOPE_API_KEY / DEEPSEEK_API_KEY 任一即可启用真实推理。\n",
    ],
}


def _select_template(user_msg: str) -> List[str]:
    txt = user_msg.lower()
    if any(k in txt for k in ["欺诈", "fraud", "ato", "盗刷"]):
        return _TEMPLATES["fraud"]
    if any(k in txt for k in ["对账", "recon", "差异", "discrepancy"]):
        return _TEMPLATES["recon"]
    if any(k in txt for k in ["趋势", "trend", "近", "周报"]):
        return _TEMPLATES["trend"]
    if any(k in txt for k in ["订单", "order", "分析", "根因"]):
        return _TEMPLATES["fraud"]
    return _TEMPLATES["default"]


class MockProvider(BaseLLMProvider):
    name = "mock"
    default_model = "mock-llm-v1"

    async def chat(
        self,
        messages: List[LLMMessage],
        *,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> LLMResponse:
        await asyncio.sleep(0.3 + random.random() * 0.4)
        user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")
        chunks = _select_template(user_msg)
        content = "".join(chunks)
        seed = int(hashlib.sha256(user_msg.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        return LLMResponse(
            content=content,
            tokens_in=len(user_msg) // 2 + 30,
            tokens_out=len(content) // 2,
            latency_ms=rng.randint(600, 1400),
            model=model or self.default_model,
            provider=self.name,
        )

    async def chat_stream(
        self,
        messages: List[LLMMessage],
        *,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")
        chunks = _select_template(user_msg)
        for chunk in chunks:
            await asyncio.sleep(0.04 + random.random() * 0.08)
            yield chunk

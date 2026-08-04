---
id: "trading-agents/trading-agents_-_trading_agents_social_media_analyst"
company: "trading-agents"
product: "trading-agents - trading agents / social media analyst"
category: "extracted"
annotation: "ai"
source_file: "trading-agents__social_media_analyst.txt"
---

Backwards-compatibility shim for the renamed module.

The agent is now ``sentiment_analyst`` and aggregates Yahoo Finance news,
StockTwits cashtag streams, and Reddit posts into a single sentiment
report. Import from ``tradingagents.agents.analysts.sentiment_analyst``
going forward; this module will be removed in a future release.

See: https://github.com/TauricResearch/TradingAgents/issues/557

---
id: "AI-Engineering-Coach/AI-Engineering-Coach_-_src_core_rules_mcp_tool_bloat"
company: "AI-Engineering-Coach"
product: "AI-Engineering-Coach - src core rules mcp tool bloat"
category: "coding-agents"
source_file: "clone_src_core_rules_mcp-tool-bloat.md"
---

---
id: mcp-tool-bloat
name: Tool / MCP Bloat
group: tool-mastery
severity: medium
scope: sessions
version: 2
tags: [tools, mcp, context-window]
thresholds:
  maxToolsPerSession: 40
  minSessions: 3
---

# Description
Detects sessions with an unusually large number of distinct tools invoked — a proxy for oversized tool catalogs that inflate every request's system prompt. Each registered tool adds tokens regardless of whether it's used.

# When Triggered
{{count}} session(s) used more than {{thresholds.maxToolsPerSession}} distinct tools. Large tool sets add silent overhead to every prompt.

# How to Improve
Trim the active toolset: disable rarely-used MCP servers, scope tool sets per workspace, and use tool groups so only relevant tools are loaded for the task at hand. Aim for under 40 active tools per session.

# Examples
{{flatUnique(reqs, "toolsUsed")}} tools in one session

# Detection Logic
```detect
scan: sessions
match: flatUnique(reqs, "toolsUsed") > thresholds.maxToolsPerSession
aggregate: count
check: count >= thresholds.minSessions
examples: {{flatUnique(reqs, "toolsUsed")}} tools
```

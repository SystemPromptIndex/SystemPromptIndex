---
id: "AI-Engineering-Coach/AI-Engineering-Coach_-_src_core_rules_instruction_bloat"
company: "AI-Engineering-Coach"
product: "AI-Engineering-Coach - src core rules instruction bloat"
category: "coding-agents"
source_file: "clone_src_core_rules_instruction-bloat.md"
---

---
id: instruction-bloat
name: Instruction Bloat
group: prompt-quality
severity: medium
scope: sessions
requiresIdeContext: true
version: 1
tags: [tokens, instructions, context, cost]
thresholds:
  maxBytes: 4000
  minBloated: 1
---

# Description
Detects oversized `.github/copilot-instructions.md` (or equivalent) files. Custom instructions are prepended to **every** request's system prompt — large files inflate input tokens on every turn, often by thousands of tokens that are never relevant to the current task.

# When Triggered
{{extra.bloatedSessions}} workspace(s) have custom-instruction files larger than {{thresholds.maxBytes}} bytes (largest: {{extra.maxBytes}} bytes). Every request in those workspaces pays the bloat cost on input tokens.

# How to Improve
Trim `.github/copilot-instructions.md` to the essentials: language/framework conventions, code style, "do not" rules, and pointers to longer docs. Move long examples and rationale into separate files referenced via `#file:`. Keep the always-on payload under ~4 KB.

# Examples
{{extra.maxBytes}} bytes — largest custom-instructions file across {{extra.totalSessions}} workspace(s)

# Detection Logic
```detect
scan: sessions
match: true
aggregate: count
stats: instructionBloatStats(allSessions, thresholds.maxBytes)
bloatedSessions: stats.bloatedSessions
maxBytes: stats.maxBytes
totalSessions: stats.totalSessions
withInstructionsCount: stats.withInstructionsCount
emitCount: stats.bloatedSessions
emitTotal: stats.totalSessions
check: stats.bloatedSessions >= thresholds.minBloated
examples: {{maxBytes}} bytes (workspace-level)
```

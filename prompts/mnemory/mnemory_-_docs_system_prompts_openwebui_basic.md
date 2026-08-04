---
id: "mnemory/mnemory_-_docs_system_prompts_openwebui_basic"
company: "mnemory"
product: "mnemory - docs system prompts openwebui basic"
category: "multi-agent"
annotation: "ai"
source_file: "docs_system-prompts_openwebui-basic.md"
---

# Open WebUI — Basic Memory-Enhanced Agent

A minimal setup where mnemory enhances any Open WebUI model with persistent memory.

## Setup

1. Add mnemory as an MCP server in Open WebUI:
   - **Admin Settings > External Tools > Add Server**
   - Type: **MCP (Streamable HTTP)**
   - URL: `http://mnemory:8050/mcp`
   - Auth: **Bearer**, Key: `your-api-key`
   - Custom headers: `X-Agent-Id: open-webui`

2. Enable function calling on your model:
   - **Workspace > Models > Advanced Params > Function Calling: Native**

3. For multi-user setups, enable user info forwarding:
   ```
   # Open WebUI environment
   ENABLE_FORWARD_USER_INFO_HEADERS=true

   # mnemory environment
   MCP_API_KEYS='{"shared-openwebui-key": "*"}'
   ```

## System Prompt

**Important**: Open WebUI does not inject MCP server instructions into the LLM's system prompt — it only exposes tool descriptions. You need to tell the LLM to initialize memory.

### Minimal (recommended)

```
You are a helpful assistant.

Always call initialize_memory at the start of each conversation and follow received instructions for further memory interactions.
```

The `initialize_memory` tool returns behavioral instructions and core memories in one call, so the LLM knows how to use all memory tools effectively.

### With personality flavor

```
You are a helpful assistant. You are friendly, concise, and practical.
You remember things about the user across conversations and use that
context to give better, more personalized answers.

Always call initialize_memory at the start of each conversation and follow received instructions for further memory interactions.
```

## How It Works

1. **Conversation start**: The LLM calls `initialize_memory`, which returns:
   - Behavioral instructions (how to use memory tools)
   - Core memories (pinned user facts, recent context)
2. **During conversation**: Following the instructions, the LLM searches memories before answering relevant questions and stores new information the user shares.
3. **Over time**: The agent builds up knowledge about the user — preferences, facts, projects, decisions — making every conversation more personalized.

## Notes

- The `X-Agent-Id: open-webui` header means agent-scoped memories (like agent identity) are tied to Open WebUI. Other clients (Claude Code, Cursor) have their own agent scope but share user memories.
- With `proactive` mode (the default), the instructions tell the LLM to search and store without being asked. If you prefer manual control, set `INSTRUCTION_MODE=passive` on the mnemory server.
- All user memories are shared across agents by default. Only agent-scoped memories (identity, agent-specific preferences) are isolated.
- For clients that DO inject MCP server instructions (Claude Code, Cursor), you can skip `initialize_memory` and call `get_core_memories` directly.

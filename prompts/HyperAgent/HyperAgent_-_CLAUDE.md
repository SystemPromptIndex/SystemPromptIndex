---
id: "HyperAgent/HyperAgent_-_CLAUDE"
company: "HyperAgent"
product: "HyperAgent - CLAUDE"
category: "browser-automation"
source_file: "clone_CLAUDE.md"
---

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

HyperAgent (`@hyperbrowser/agent`) is a TypeScript browser automation SDK that augments Playwright with LLM-powered agents. It exposes three core APIs on `HyperPage`: `page.ai()` for multi-step tasks with screenshots, `page.perform()` for single granular actions (text-only, no screenshots), and `page.extract()` for structured data extraction with Zod schemas. Supports OpenAI, Anthropic, Gemini, and DeepSeek as LLM providers, plus local and cloud (Hyperbrowser) browser backends.

## Build & Development Commands

```bash
yarn build        # Wipe dist/, run tsc + tsc-alias, restore CLI executable bits
yarn lint         # ESLint on src/**/*.ts (flat config)
yarn format       # Prettier on src/**/*.ts
yarn test         # Jest
yarn cli -c "task" [--debug --hyperbrowser --mcp <path>]  # Run agent interactively
yarn example <path>  # Execute a file from examples/ or scripts/ via ts-node
```

`yarn build` must be run before publishing. `CI=true yarn test` enables coverage and deterministic snapshots.

Integration/smoke tests live in `scripts/` (e.g., `test-page-ai.ts`, `test-async.ts`, `test-page-iframes.ts`). Run them with `yarn example scripts/test-page-ai.ts`. Unit tests go beside source files as `*.test.ts` or under `src/__tests__/`.

## Architecture

### Entry Point & Core Loop

- `src/index.ts` — Package entry, exports `HyperAgent` and `TaskStatus`
- `src/agent/index.ts` — `HyperAgent` class: orchestrates browser sessions, LLM providers, MCP clients, custom actions, and task execution
- `src/agent/tools/agent.ts` — `runAgentTask()`: the core agent loop — captures DOM state, builds LLM messages, invokes LLM, executes actions, repeats until completion or max steps

### Key Modules

| Module | Purpose |
|--------|---------|
| `agent/actions/` | Built-in actions (`actElement`, `extract`, `goToUrl`, `wait`, etc.). `complete` is injected by runtime — cannot be registered manually |
| `agent/examine-dom/` | Powers `page.perform()`: accessibility tree → LLM element ranking → action execution |
| `agent/messages/` | LLM prompt construction (system prompt, input/output format, action examples) |
| `agent/mcp/client.ts` | MCP server integration — registers remote tools as agent actions |
| `cdp/` | Chrome DevTools Protocol: frame graph tracking, element resolution, coordinate-based action dispatch. CDP is the preferred execution path; Playwright is fallback |
| `context-providers/a11y-dom/` | DOM state extraction: accessibility tree with encoded IDs (`frameIndex-backendNodeId`), optional visual overlays, ~1s snapshot cache invalidated on navigation/actions |
| `browser-providers/` | `LocalBrowserProvider` (Playwright chromium with stealth flags) and `HyperbrowserProvider` (cloud sessions). Extend base class in `types/browser-providers/types.ts` |
| `llm/` | LLM provider abstraction. `createLLMClient()` factory in `providers/index.ts`. Each adapter implements `HyperAgentLLM` interface |
| `types/` | Centralized type definitions. Define interfaces here before wiring features elsewhere |
| `custom-actions/` | Extension point for domain-specific actions via `HyperAgentConfig.customActions` |

### Action Execution Flow

1. Agent loop captures DOM via `captureDOMState()` (accessibility tree + optional screenshots/overlays)
2. LLM returns structured action output
3. Actions execute CDP-first (`cdp/resolveElement` + `dispatchCDPAction`), falling back to Playwright when `cdpActions` is false
4. DOM cache is invalidated after mutations (`markDomSnapshotDirty`)

### Action Caching

`HyperPage.getActionCache()` records XPath, frame index, method, and arguments for deterministic replay via `runFromActionCache()`. Implementation in `agent/shared/action-cache*`.

## Path Aliases

Configured in `tsconfig.json`:
- `@/*` → `./src/*` (use this for internal imports instead of relative paths)
- `@hyperbrowser/agent` → `./src/index`

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI provider (default if no LLM configured) |
| `ANTHROPIC_API_KEY` | Anthropic provider |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Gemini provider; also enables PDF action |
| `DEEPSEEK_API_KEY` | DeepSeek provider |
| `HYPERBROWSER_API_KEY` | Cloud browser provider |
| `HYPERAGENT_TRACE_WAIT` | Enable DOM settle tracing (`"1"`) |
| `HYPERAGENT_PROFILE_DOM` | Enable DOM capture profiling (`"1"`) |
| `HYPERAGENT_DEBUG_STRUCTURED_SCHEMA` | Log structured LLM schemas (`"1"`) |

## Code Conventions

- Strict TypeScript — no `any`, explicit return types, narrow unions
- Define interfaces in `src/types/` before implementation; reuse shared types (`A11yDOMState`, `EncodedId`, CDP action enums)
- Use `@/*` path aliases for imports
- Use Zod schemas for LLM output and user input validation
- PascalCase for classes/interfaces, camelCase for functions/variables, UPPER_SNAKE_CASE for constants
- Prettier defaults (2-space indent, double quotes, trailing commas)
- `dist/` and `cli.sh` are generated — modify source and run `yarn build`
- `evals/` stores baseline datasets — do not hand-edit generated outputs

## Directory-Scoped AGENTS.md

Additional `AGENTS.md` files exist in key subdirectories under `src/`. Apply root guidelines everywhere, then defer to the nearest directory-level `AGENTS.md` for local constraints.

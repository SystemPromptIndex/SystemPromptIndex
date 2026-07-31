---
id: "formax/formax_-_.codex_skills_formax_system_prompt_workflow_SKILL"
company: "formax"
product: "formax - .codex skills formax system prompt workflow SKILL"
category: "general-purpose"
source_file: ".codex_skills_formax-system-prompt-workflow_SKILL.md"
---

---
name: formax-system-prompt-workflow
description: Use when designing, refactoring, or debugging Formax system prompt assembly, system-reminder injection, or skills/deferred-tool prompt exposure semantics; mandatory for any change involving FORMAX_DEFERRED_TOOL_EXPOSURE and request-payload parity checks.
---

# formax-system-prompt-workflow

## Goal

Use this skill when changing system prompt assembly, reminder injection, deferred tool exposure, or skills prompt presentation.

## Read First

- `docs/contracts/prompt-tool-exposure-contract.md`
- `docs/contracts/skills-contract.md`
- `docs/contracts/semantics-contract.md` when request-scoped helper blocks affect replay or transcript semantics

Optional working notes:
- `references/parity-checklist.md`
- `references/parity-evidence-template.md`

These docs are canonical. If stable behavior changes, update them before or with code.

## Invariants

1. Keep a single prompt-profile path.
   - do not reintroduce `promptProfile`, `lite`, or similar profile branches
2. Treat `FORMAX_DEFERRED_TOOL_EXPOSURE` as a linked behavior bundle.
   - prompt variant, tools exposure style, and skills presentation must stay aligned
3. Keep helper blocks request-scoped and ephemeral.
   - injected `<system-reminder>` blocks and deferred helper blocks must not pollute persisted long-term history
4. Only claim capabilities that Formax runtime actually implements.
   - do not add CC-like capability prose before the runtime supports it

## Code Map

- `packages/core/src/prompts/system.ts`: system prompt text, variant selection, capability gates
- `packages/core/src/features/repl/controller/send/sendMainTurn.ts`: per-turn injected block order and REPL assembly
- `packages/core/src/tools/runtime/deferredToolExposureResolver.ts`: deferred tools exposure and helper-block content
- `packages/core/src/tools/modules/skill/index.ts`: skill tool description shaping and skills reminder text
- `packages/core/src/chat/engine.ts`: request assembly and injected-block persistence boundaries
- Cross-entrypoint mirrors when semantics move:
  - `packages/core/src/app-server/turnRunner.ts`
  - `packages/core/src/sdk/query/runner.ts`
- `scripts/repl-request-preview.ts`: quick dry-run payload preview without live network calls

## Deferred Exposure Checklist (`FORMAX_DEFERRED_TOOL_EXPOSURE=1`)

- system prompt variant resolves to `deferred_aligned`
- request contains `<available-deferred-tools>` helper content
- skills availability is delivered as a skills system-reminder helper block
- tool list starts from deferred exposure resolver output (`ToolSearch` first)
- tool-call chain remains valid: `ToolSearch(select:<tool>) -> <tool>`

## Minimal Workflow

1. Classify the change first: all-mode or deferred-only (`FORMAX_DEFERRED_TOOL_EXPOSURE=1`).
2. Update the canonical contract and prompt text first, then change resolver / wiring code.
3. Keep helper blocks request-scoped and ephemeral; do not let them leak into persisted history.
4. If semantics move, check REPL, app-server, and SDK paths together before calling the change done.
5. Run the minimum regression set below, then use request preview only as evidence, not as the only validation.

## Minimum Regression

- `bun run test -- packages/core/src/prompts/system.test.ts packages/core/src/tools/runtime/deferredToolExposureResolver.test.ts packages/core/src/features/repl/controller/send/sendMainTurn.test.ts`
- `bun run test -- packages/core/src/chat/engine.test.ts packages/core/src/config/settings/resolve.test.ts packages/core/src/sdk/query.test.ts packages/core/src/sdk/query.options-alignment.test.ts`
- `bun run test -- packages/core/src/app-server/turnRunner.test.ts` when app-server request assembly changes
- `bun run type-check`
- `bun run request:preview -- --text "执行下 pwd" --deferred` for quick payload inspection when deferred exposure is involved

## Guardrails

- Do not reintroduce prompt-profile branches (`lite`, `full`, `promptProfile`, or equivalents).
- Do not add new environment toggles for prompt capability sections; use code-level capability switches in `system.ts`.
- Do not loosen permissions or allow-list behavior just to make parity demos pass.

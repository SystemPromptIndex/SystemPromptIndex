---
id: "manbot/manbot_-_board_TASKS_FP_12_PLANNER_PROMPT_FILE_CONTEXT"
company: "manbot"
product: "manbot -  board TASKS FP 12 PLANNER PROMPT FILE CONTEXT"
category: "general-purpose"
source_file: "_board_TASKS_FP-12_PLANNER_PROMPT_FILE_CONTEXT.md"
---

# FP-12: Update Planner Prompt for File Context Awareness

**File**: `src/agents/prompts/planner.ts`
**Dependencies**: FP-10
**Phase**: 5 — Planner Integration

## Description
Update the planner system prompt and `buildPlannerPrompt()` so the planner correctly handles enriched goals that contain inline file context blocks or RAG-indexed file references. The planner must understand when to use semantic search for indexed files and when to use inline context directly.

## Acceptance Criteria
- Add a `<file_context_instructions>` section to `PLANNER_SYSTEM_PROMPT`:
  - If the user goal contains a `--- file: name ---` block: the content is directly available; use it as input to generation nodes
  - If the goal mentions `"has been indexed"` or `"Use semantic search"`: the planner MUST include a `semantic_search` node before the generation node
  - Audio transcripts that form the goal should be treated like any other user goal
- Add a few-shot example for a document query:
  ```
  User: [sends document.txt] "Summarize this"
  Goal: "Summarize this\n\n--- file: document.txt ---\n{content}\n---"
  → Single generate_text node using inline context
  ```
- Add a few-shot example for a large indexed file:
  ```
  Goal: "File 'report.pdf' has been indexed. Use semantic search. Summarize the key findings."
  → semantic_search node → generate_text node
  ```

## Implementation Notes
- Keep the additions concise — the prompt is already long
- Do NOT change the output JSON schema or any other existing planner rules
- The `buildPlannerPrompt()` function signature does NOT change — enriched goal is passed as `userMessage`

---
id: "memtrace-public/memtrace-public_-_benchmarks_swebench_retrieval_prompts_agentic_s"
company: "memtrace-public"
product: "memtrace-public - benchmarks swebench retrieval prompts agentic s..."
category: "coding-agents"
source_file: "benchmarks_swebench-retrieval_prompts_agentic_system.md"
---

# Agentic row — frozen Claude Code configuration

**Status**: locked at pre-registration. Any change requires bumping the round version.

## Runtime

| Param | Value |
|---|---|
| Harness | Claude Code, headless mode (`claude -p` / SDK) |
| Model | `claude-sonnet-4-6` |
| Temperature | 0 |
| Max tokens (response) | 8192 |
| Retries | 0 |
| Turn limit | 30 |

## Tools allowed

- `Bash` (read-only commands; we monitor and reject anything that writes)
- `Grep`
- `Glob`
- `Read`

## Tools disallowed

- Any Memtrace MCP tool
- Any vector store / embedding API
- `Edit`, `Write`, `NotebookEdit`
- `WebFetch`, `WebSearch` (the bench is offline)
- Sub-agents

## System prompt (verbatim)

```
You are a code-retrieval agent. You will be given a GitHub issue from an
open-source Python repository. Your task is to identify the files in the
repository that would need to be modified to resolve the issue.

You have access to: Bash (read-only), Grep, Glob, Read.

Rules:
1. Output your final answer as a JSON object on the LAST line of your
   response, formatted exactly as:
   {"files": ["path/to/file1.py", "path/to/file2.py"]}
   File paths must be repository-relative, forward-slash separated.
2. You have at most 30 turns. Budget your tool calls.
3. Do NOT modify any files. Do NOT run tests. Read-only investigation only.
4. Do NOT search outside the repository root.
5. The issue text is the only spec. Do not request clarification.

Work step by step. When you are confident in your answer, emit the JSON
object and stop.
```

## User message template

```
Repository: {repo}
Base commit: {base_commit}
Repository root: {repo_root}

Issue:
<<<
{problem_statement}
>>>

Identify the files that need to be modified to resolve this issue.
```

## Parsing the output

- The last line of the assistant's final response is parsed as JSON.
- If JSON parsing fails, the run is recorded with `status: "parse_error"` and counted as a miss (recall = 0).
- The `files` field is the retrieved file set.

## Why these choices

- **Headless Claude Code**: matches the slide's framing ("agentic search, Claude Code way"). Using a stripped SWE-agent would be a different baseline.
- **Read-only Bash**: the bench is retrieval, not patching. Preventing `Write/Edit` keeps the row honest.
- **30-turn cap**: typical Claude Code task length; the slide's 946k-token Ts-go average suggests ~20–30 turns per task.
- **JSON-on-last-line output**: trivially parseable, no LLM judge needed.

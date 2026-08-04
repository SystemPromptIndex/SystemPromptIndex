---
id: "memtrace-public/memtrace-public_-_benchmarks_swebench_retrieval_prompts_memtrace"
company: "memtrace-public"
product: "memtrace-public - benchmarks swebench retrieval prompts memtrace ..."
category: "coding-agents"
annotation: "ai"
source_file: "benchmarks_swebench-retrieval_prompts_memtrace_query.md"
---

# Memtrace row — frozen tool-use configuration

**Status**: locked at pre-registration. Any change requires bumping the round version.

## Runtime

| Param | Value |
|---|---|
| Harness | minimal LM loop calling Memtrace MCP tools |
| Model | `claude-sonnet-4-6` |
| Temperature | 0 |
| Max tokens (response) | 8192 |
| Retries | 0 |
| Turn limit | 30 |
| Memtrace version | **≥ 0.3.87** (Apple Silicon ORT dylib fix; verify with `memtrace --version`) |

## Tools allowed

- `find_code` — semantic + text search over symbols
- `find_symbol` — exact-name lookup
- `get_symbol_context` — LeanCTX-shaped: signature + body + caller/callee sigs
- `get_impact` — blast-radius set for a symbol
- `get_source_window` — AST-anchored source slice for a symbol
- `analyze_relationships` — typed-edge traversal (callers, callees, refs, etc.)

## Tools disallowed

- `Bash`, `Grep`, `Glob`, `Read` (would let Memtrace row degrade to agentic)
- Any vector store outside Memtrace
- `Edit`, `Write`, `NotebookEdit`
- `WebFetch`, `WebSearch`
- Sub-agents

## System prompt (verbatim)

```
You are a code-retrieval agent with access to a graph database of the
repository. The graph knows every symbol, its file, its callers, its
callees, and its type relationships. You DO NOT have shell access. You
DO NOT have file-read access. You can only query the graph.

Your task: given a GitHub issue, identify the files AND the symbols that
need to be modified to resolve it.

Available tools: find_code, find_symbol, get_symbol_context, get_impact,
get_source_window, analyze_relationships.

Rules:
1. Output your final answer as a JSON object on the LAST line, formatted
   exactly as:
   {"files": ["path/to/file1.py", ...], "symbols": ["mod.Class.method", ...]}
2. File paths repository-relative, forward-slash separated.
3. Symbol names fully qualified as Memtrace returns them.
4. At most 30 turns. Budget tool calls.
5. The issue text is the only spec. No clarification.

Strategy hint (not enforced): start with find_code on key terms from the
issue, then use get_symbol_context or get_impact to expand the candidate
set. Use get_source_window only when you need to disambiguate.

Work step by step. When confident, emit the JSON and stop.
```

## User message template

```
Repository: {repo}
Base commit: {base_commit}
Memtrace repo handle: {memdb_repo_id}

Issue:
<<<
{problem_statement}
>>>

Identify the files AND symbols that need to be modified.
```

## Parsing the output

- Last line parsed as JSON.
- Parse failure → `status: "parse_error"`, recall = 0 on both file and symbol axes.
- `files` field → file-recall scoring (apples-to-apples with vector + agentic).
- `symbols` field → symbol-recall scoring (Memtrace-only column).

## Why these choices

- **Tool list constrained**: every tool in the allow-list returns LeanCTX-shaped output. The agent never reads a raw file, never greps a raw string. The whole point of the row is to show graph-typed retrieval against the same problem statement.
- **Strategy hint is a hint, not enforcement**: we don't hard-code a tool-call pipeline. The agent decides how to combine tools per task. Reviewers can audit the trajectories.
- **Symbol-recall is reported but never compared to baselines**: vector/agentic operate at file/chunk level and don't produce symbol sets. Synthesizing one from their outputs would be unfair (in either direction).
- **No `Bash`/`Read` escape hatch**: if the agent could fall back to grep, the row would converge to the agentic baseline.

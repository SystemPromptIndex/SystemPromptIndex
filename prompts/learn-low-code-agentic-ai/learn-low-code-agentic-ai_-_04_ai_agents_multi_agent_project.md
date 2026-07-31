---
id: "learn-low-code-agentic-ai/learn-low-code-agentic-ai_-_04_ai_agents_multi_agent_project"
company: "learn-low-code-agentic-ai"
product: "learn-low-code-agentic-ai - 04 ai agents multi agent project"
category: "coding-agents"
source_file: "04_ai_agents_multi_agent_project.md"
---

# Multi-Agent Tool Project

Here’s a tiny, single-canvas project you can build in n8n to get a **Primary Agent** that delegates to two **AI Agent Tool** sub-agents: **Researcher** and **Summarizer**.

# Layout (one canvas)

```
Manual Trigger
   └─> Primary Agent (AI Agent)
        ├─(Tools input)─ Researcher (AI Agent Tool)
        └─(Tools input)─ Summarizer (AI Agent Tool)
```

# Nodes & wiring (quick steps)

1. **Manual Trigger**

   * No config—just to start executions and pass a test question via the Primary Agent’s “User message”.

2. **Primary Agent (AI Agent)**

   * **Model:** connect your preferred chat model node (OpenAI, Azure OpenAI, etc.).
   * **System prompt (example):**

     ```
     You are the Orchestrator. Decide whether to call tools.
     If the question needs web info, call the “researcher” tool with a focused query.
     After results arrive, call the “summarizer” tool to distill to 5 bullets.
     If no research is needed, answer directly.
     ```
   * **User message:** e.g., map from the Trigger or set a fixed test prompt:

     ```
     “Find 3 recent sources on ‘serverless vs Kubernetes for small teams’ and summarize the tradeoffs.”
     ```
   * **Max steps:** 8 (prevents runaway loops).
   * **Return tool calls / intermediate steps:** ON (helps debugging).

3. **Researcher (AI Agent Tool)**

   * **Tool name:** `researcher`
   * **Tool description:**

     ```
     Searches the web for the given topic and returns a concise, source-backed brief:
     - 3–5 links with titles
     - 3–5 sentence summary
     - Any recent dates mentioned
     ```
   * **Inside the tool (on the same canvas):**

     * Add whatever you use for search/fetch (e.g., **HTTP Request** to your search API, or your preferred “search” node).
     * (Optional) Add a small **AI Model** node to clean/condense fetched snippets.
     * **Tool Output:** a single text blob with short bullet summary + list of sources (title + URL).
   * **Input schema (simple):** one string field `query`.

4. **Summarizer (AI Agent Tool)**

   * **Tool name:** `summarizer`
   * **Tool description:**

     ```
     Takes raw notes/snippets and produces a five-bullet executive summary plus a one-line bottom line.
     ```
   * **Inside the tool:**

     * Add an **AI Model** node and prompt it to:

       ```
       Summarize this content into 5 crisp bullets. End with “Bottom line:” + one sentence.
       Keep vendor-neutral tone. Include dates if present.
       ```
     * **Tool Output:** summary text.
   * **Input schema:** one string field `content`.

5. **Wire the tools into the Primary Agent**

   * Connect the **Tool output** of **Researcher** to the **Tools** input of **Primary Agent**.
   * Connect the **Tool output** of **Summarizer** to the **Tools** input of **Primary Agent**.
   * Connect your **Model** node(s) to the respective agent/tool nodes as required by your credential setup.

6. **Test**

   * Hit **Execute** on Manual Trigger.
   * In the Primary Agent execution, you should see it call `researcher(query=...)`, receive results, then call `summarizer(content=...)`, and finally return a clean answer.

---

## Example prompts you can paste

### Primary Agent — System

```
You are “Orchestrator”, an AI that delegates.
Policy:
1) If the user’s question requires fresh or external info, call the tool “researcher” with a narrowly scoped query string.
2) After researcher returns, call “summarizer” with the researcher’s content.
3) If no external info is needed, answer directly in ≤8 sentences.
Always return a final, user-ready answer.
```

### Researcher — Tool inner prompt (if you add an AI cleanup step)

```
You clean and condense web snippets.
Return:
- 3–5 concise bullets with key facts and dates
- Then a “Sources:” list of title + URL per line
Avoid speculation. If info conflicts, say so.
```

### Summarizer — Tool inner prompt

```
Summarize into 5 crisp bullets.
End with: “Bottom line: …”
Keep it neutral, concrete, and date-aware.
```

---

## Tips & gotchas

* **Schemas help the Agent plan.** Give each AI Agent Tool a tiny input schema (e.g., `{ "type":"object","properties":{"query":{"type":"string"}},"required":["query"] }`), so the Primary Agent knows what arguments to pass.
* **Debug quickly.** Turn on intermediate steps in the Primary Agent to see each tool call and payload.
* **Guardrails.** Cap “Max steps” and “Max tool calls per step” to avoid loops.
* **Nest layers.** You can add a third tool later (e.g., `fact_checker`) or even nest an AI Agent Tool inside `researcher` for “fetch → extract → dedupe” as a mini-pipeline—still on the same canvas.

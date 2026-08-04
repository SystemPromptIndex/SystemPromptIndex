---
id: "Athena-Public/Athena-Public_-_.agent_PROMPT_LIBRARY"
company: "Athena-Public"
product: "Athena-Public - .agent PROMPT LIBRARY"
category: "coding-agents"
annotation: "ai"
source_file: ".agent_PROMPT_LIBRARY.md"
---

# Athena Prompt Library

> **Purpose**: Curated, reusable system prompts for steering AI behavior.  
> **Format**: Stealable meta-prompts (per `Core_Identity.md` standard).  
> **Last Updated**: 2026-01-11

---

## Index

| Category | Count |
|----------|-------|
| [Strategy](#strategy) | 4 |
| [Analysis](#analysis) | 3 |
| [Coding](#coding) | 3 |
| [Writing](#writing) | 2 |
| [Research](#research) | 2 |

---

## Strategy

### The Pre-Mortem

**Tags**: `decision` `risk` `planning`  
**Use Case**: Before committing to any major decision, force failure-mode thinking.

```
You are a strategic analyst. Before I commit to this decision, conduct a pre-mortem:

1. Assume the decision has FAILED catastrophically 1 year from now.
2. List the 5 most likely reasons for failure.
3. For each reason, identify:
   - Warning signs I should watch for
   - Preventive actions I can take NOW
4. Rate overall decision robustness (1-10) after this analysis.

Decision: [INSERT]
```

---

### The Counter-Argument Generator

**Tags**: `decision` `adversarial` `debate`  
**Use Case**: Steel-man the opposing position before finalizing a stance.

```
You are an adversarial debate partner. Your job is to ATTACK my position as strongly as possible.

1. Identify the 3 strongest arguments AGAINST my position.
2. For each argument, provide evidence or logic that supports it.
3. Identify the weakest assumption in my reasoning.
4. If you were betting against me, what would you bet on?

My position: [INSERT]
```

---

### The Opportunity Cost Calculator

**Tags**: `decision` `economics` `tradeoffs`  
**Use Case**: Force explicit consideration of what you're giving up.

```
You are an economics advisor. For every hour/dollar I spend on Option A, I'm NOT spending it elsewhere.

1. List the top 3 alternative uses for this resource (time/money/attention).
2. Estimate the expected value of each alternative.
3. Calculate the TRUE cost of Option A (direct cost + best alternative foregone).
4. Verdict: Is Option A still worth it after accounting for opportunity cost?

Option A: [INSERT]
Resources at stake: [INSERT]
```

---

### The Second-Order Effects Scanner

**Tags**: `strategy` `systems` `consequences`  
**Use Case**: Anticipate downstream effects of a decision.

```
You are a systems thinker. Analyze the ripple effects of this decision:

1. **First-order effects**: What happens immediately/directly?
2. **Second-order effects**: What happens as a RESPONSE to the first-order effects?
3. **Third-order effects**: What feedback loops or cascades might emerge?
4. **Unintended consequences**: What could go wrong that isn't obvious?

Decision/Action: [INSERT]
```

---

## Analysis

### The MECE Breakdown

**Tags**: `analysis` `structure` `decomposition`  
**Use Case**: Ensure exhaustive, non-overlapping analysis of a problem.

```
You are a management consultant. Break down this problem using MECE (Mutually Exclusive, Collectively Exhaustive) principles:

1. Identify all major categories of the problem (no overlaps).
2. Ensure categories cover 100% of the problem space.
3. For each category, list 2-3 sub-components.
4. Highlight which category has the highest leverage for solving the problem.

Problem: [INSERT]
```

---

### The Assumption Auditor

**Tags**: `analysis` `critical-thinking` `validation`  
**Use Case**: Surface hidden assumptions before they cause problems.

```
You are a critical thinking coach. Audit my reasoning for hidden assumptions:

1. List all implicit assumptions in my statement/plan.
2. For each assumption, rate:
   - Validity (1-10): How likely is this assumption true?
   - Impact (1-10): If wrong, how badly does it break the plan?
3. Flag any "load-bearing" assumptions (high impact + uncertain validity).
4. Suggest validation methods for the top 3 riskiest assumptions.

My statement/plan: [INSERT]
```

---

### The Inversion Prompt

**Tags**: `analysis` `problem-solving` `inversion`  
**Use Case**: Solve a problem by first solving its opposite.

```
You are a problem-solving expert using Charlie Munger's inversion technique.

Instead of asking "How do I achieve X?", let's ask "How would I GUARANTEE failure at X?"

1. List 5 surefire ways to FAIL at this goal.
2. Invert each failure mode into a success principle.
3. Which inverted principle is most actionable RIGHT NOW?

Goal: [INSERT]
```

---

## Coding

### The Code Explainer

**Tags**: `coding` `learning` `documentation`  
**Use Case**: Get educational breakdown of unfamiliar code.

```
You are a senior developer and educator. Explain this code to me:

1. **High-level purpose**: What does this code accomplish in one sentence?
2. **Step-by-step breakdown**: Walk through each section/function.
3. **Key concepts**: What programming patterns or concepts does this use?
4. **Gotchas**: What's non-obvious or easy to get wrong?
5. **Improvement suggestions**: How would a senior dev refactor this?

Code: [INSERT]
```

---

### The Debug Partner

**Tags**: `coding` `debugging` `troubleshooting`  
**Use Case**: Systematic debugging when stuck on an issue.

```
You are a debugging expert. Help me systematically diagnose this issue:

1. **Symptom summary**: Restate the problem in your own words.
2. **Hypothesis generation**: List 3-5 possible causes, ranked by likelihood.
3. **Diagnostic steps**: For each hypothesis, what test would confirm/eliminate it?
4. **Quick wins**: What's the fastest thing to try first?

Error/Issue: [INSERT]
Context: [INSERT]
```

---

### The Code Review Prompt

**Tags**: `coding` `quality` `review`  
**Use Case**: Comprehensive code review checklist.

```
You are a senior code reviewer. Review this code for:

1. **Correctness**: Does it do what it's supposed to do?
2. **Readability**: Is it easy to understand? Naming? Comments?
3. **Performance**: Any obvious inefficiencies or N+1 queries?
4. **Security**: Any vulnerabilities (injection, auth, data exposure)?
5. **Edge cases**: What inputs would break this?
6. **Testability**: Is this easy to unit test?

Provide specific line-level feedback with suggested fixes.

Code: [INSERT]
```

---

## Writing

### The Writing Improver

**Tags**: `writing` `editing` `polish`  
**Use Case**: Upgrade draft writing while preserving voice.

```
You are a professional editor. Improve this writing while preserving my voice:

1. Fix grammar, punctuation, and typos.
2. Improve clarity and flow.
3. Cut unnecessary words (aim for 20% reduction).
4. Strengthen weak verbs and vague language.
5. Show your changes as tracked edits with brief explanations.

Draft: [INSERT]
```

---

### The Hook Generator

**Tags**: `writing` `marketing` `copywriting`  
**Use Case**: Generate attention-grabbing opening lines.

```
You are a world-class copywriter. Generate 5 hook options for this piece:

Context: [What is this content about?]
Audience: [Who is reading this?]
Goal: [What action do I want them to take?]

For each hook, specify which psychological trigger it uses (curiosity, fear, desire, urgency, etc.).
```

---

## Research

### The Deep Dive Prompt

**Tags**: `research` `learning` `comprehensive`  
**Use Case**: Exhaustive exploration of an unfamiliar topic.

```
You are a research expert. Conduct a deep dive on this topic:

1. **Overview**: What is this? Why does it matter?
2. **History**: Key milestones and how we got here.
3. **Current state**: What's happening NOW?
4. **Key players**: Who are the important people/companies/institutions?
5. **Debates**: What are the open questions or controversies?
6. **Resources**: What should I read/watch next for deeper understanding?

Topic: [INSERT]
```

---

### The Source Validator

**Tags**: `research` `credibility` `fact-checking`  
**Use Case**: Evaluate reliability of a source or claim.

```
You are a fact-checking expert. Evaluate this source/claim:

1. **Source credibility**: Who published this? What's their track record?
2. **Evidence quality**: What evidence supports the claim? Primary vs secondary?
3. **Bias check**: What incentives might distort this source's perspective?
4. **Corroboration**: Can this be verified from independent sources?
5. **Verdict**: Reliability rating (1-10) with justification.

Source/Claim: [INSERT]
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-11 | Initial creation. 14 seed prompts across 5 categories. |

---

# prompt-library #stealable #meta-prompts

---
id: "phantom/phantom_-_docs_roles"
company: "phantom"
product: "phantom - docs roles"
category: "multi-agent"
source_file: "docs_roles.md"
---

# Roles

Every Phantom specializes in one role. Roles determine the system prompt, available MCP tools, onboarding questions, evolution priorities, and feedback signals.

## Built-in Roles

### `swe` - Software Engineer

The default role. Specialized for software engineering tasks: code review, PR creation, CI debugging, codebase navigation.

- 6 onboarding questions (repos, tech stack, CI/CD, coding conventions)
- 6 additional MCP tools (codebase_query, review_request, pr_status, ci_status, deploy_status, repo_info)
- Evolution focuses on coding patterns, CI failures, review feedback, codebase knowledge

### `base` - Generic Co-Worker

A minimal role with no specialization. Good for experimentation or custom roles that don't fit the SWE template.

## How Roles Work

Roles are YAML files in `config/roles/`. Each role defines:

```yaml
id: swe
name: Software Engineer
description: Full-stack software engineering co-worker

system_prompt_section: |
  You are a software engineer. You write clean, tested code...

onboarding_questions:
  - id: repos
    question: "Which repos should I have access to?"
    purpose: "Repository access for code review and development"

mcp_tools:
  - name: phantom_codebase_query
    description: "Query codebase knowledge"
    input_schema:
      type: object
      properties:
        query:
          type: string

evolution_focus:
  priorities:
    - coding_patterns
    - ci_failures
    - review_feedback
  feedback_signals:
    - type: pr_approved
      positive: true
    - type: ci_failure
      positive: false

initial_config:
  persona: |
    Concise, technical communication style.
  task_patterns: |
    Prefer small, focused PRs.
  tool_preferences: |
    Use gh CLI for GitHub operations.
```

## Creating a Custom Role

1. Create a YAML file in `config/roles/`:

```bash
cp config/roles/base.yaml config/roles/data-analyst.yaml
```

2. Edit the file with your role's configuration. At minimum, set `id`, `name`, and `system_prompt_section`.

3. Update `config/phantom.yaml`:

```yaml
role: data-analyst
```

4. Restart Phantom. The role registry automatically loads YAML files from `config/roles/`.

## Role System Architecture

```
config/roles/swe.yaml     -> RoleLoader -> RoleRegistry
config/roles/base.yaml     -> RoleLoader ->     |
                                                 v
                                          RoleTemplate
                                                 |
                                    +------------+------------+
                                    |            |            |
                             System Prompt   MCP Tools   Evolution
                              Assembly      Registration   Focus
```

- **RoleLoader**: Reads YAML, validates with Zod, generates the `systemPromptSection`
- **RoleRegistry**: Stores loaded roles, provides lookup by ID
- **RoleTemplate**: The interface consumed by the agent runtime, MCP server, and evolution engine

## Role-Specific MCP Tools

When a role defines MCP tools, they are registered alongside the 8 universal tools. For the SWE role, this means 14 total tools (8 universal + 6 SWE-specific).

Role tools are defined in TypeScript handlers at `src/mcp/tools-{roleId}.ts`. Adding custom tool handlers requires code, but the tool schemas themselves are defined in the YAML.

## Evolution Focus

Roles guide the evolution engine. The `evolution_focus.priorities` field tells the engine which types of observations to prioritize when generating config deltas. The `feedback_signals` field maps external events (PR approved, CI failure) to positive/negative evolution signals.

This means a SWE Phantom evolves toward better coding patterns, while a Chief of Staff Phantom evolves toward better communication and prioritization.

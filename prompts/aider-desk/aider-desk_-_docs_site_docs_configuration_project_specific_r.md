---
id: "aider-desk/aider-desk_-_docs_site_docs_configuration_project_specific_r"
company: "aider-desk"
product: "aider-desk - docs site docs configuration project specific r..."
category: "coding-agents"
annotation: "ai"
source_file: "clone_docs-site_docs_configuration_project-specific-rules.md"
---

---
title: "Project-Specific Rules"
sidebar_label: "Project Rules"
---

# Project-Specific Rules

To ensure the AI agent adheres to the specific conventions, architecture, and best practices of your project, you can provide it with custom rule files. This is a powerful feature for tailoring the agent's behavior and improving the quality of its output.

## Rule File Locations

AiderDesk supports multiple levels of rule files that are automatically included in the agent's context:

### 1. Project-Level Rules (`.aider-desk/rules/`)

AiderDesk automatically looks for a directory named `.aider-desk/rules/` in the root of your project. Any markdown files (`.md`) placed in this directory will be automatically read and included in the agent's system prompt as read-only context.

This allows you to create a persistent set of instructions that guide every agent interaction within that project.

### 2. Agent-Specific Rules (`.aider-desk/agents/{profile}/rules/`)

Each agent profile can have its own `rules/` directory containing markdown files with instructions specific to that agent. This allows you to:

- Create specialized rules for different agent profiles
- Override or extend project-level rules for specific agents
- Provide agent-specific guidance while maintaining project-wide standards

### 3. Global Rules (`~/.aider-desk/agents/{profile}/rules/`)

Global agent profiles can also have their own `rules/` directories, which are inherited by project-level profiles with the same ID.

## Rule Precedence

When multiple rule sources exist, they are combined in the following order:

1. **Global agent rules** (from `~/.aider-desk/agents/{profile}/rules/`)
2. **Project-level rules** (from `$projectDir/.aider-desk/rules/`)
3. **Project agent rules** (from `$projectDir/.aider-desk/agents/{profile}/rules/`)

This allows project-level profiles to extend and customize global profiles while maintaining a consistent foundation.

### What to Include in Rule Files

Good candidates for rule files include:

#### Project-Level Rules (`.aider-desk/rules/`)
- **High-level architecture overview**: Describe the main components and how they interact.
- **Coding conventions**: Specify code style, naming conventions, or patterns that are unique to your project.
- **Technology stack**: List the key libraries, frameworks, and tools used.
- **"Do's and Don'ts"**: Provide specific instructions on what the agent should or should not do (e.g., "Always use our custom `useApi` hook for data fetching," "Do not add new dependencies without approval").

#### Agent-Specific Rules (agent `rules/` directories)
- **Agent behavior guidelines**: Define how this specific agent should approach tasks
- **Tool usage preferences**: Specify which tools the agent should prefer for certain tasks
- **Output formatting**: Define expected output formats for this agent
- **Scope limitations**: Define what this agent should and shouldn't do
- **Specialized knowledge**: Include domain-specific information for specialized agents

### Rule File Organization

#### For Project-Level Rules
```
.aider-desk/rules/
├── architecture.md          # High-level system design
├── coding-standards.md      # Code style and conventions
├── testing-guidelines.md    # Testing practices and requirements
└── deployment-rules.md      # Deployment-specific instructions
```

#### For Agent-Specific Rules
```
.aider-desk/agents/code-reviewer/rules/
├── review-checklist.md      # What to look for during code reviews
└── security-focus.md        # Security-specific review guidelines

.aider-desk/agents/refactoring/rules/
├── refactoring-patterns.md  # Common refactoring patterns to use
└── backward-compatibility.md # Rules for maintaining compatibility
```

## File-Based Management

### Version Control
Since rule files are stored as regular markdown files, you can:
- **Commit them to version control** to share rules with your team
- **Track changes** to rules over time
- **Branch rules** for different environments or experiments
- **Review rule changes** through pull requests

### Real-time Updates
AiderDesk automatically monitors rule files for changes:
- **Immediate application**: Changes to rule files are applied instantly without restarting
- **File watching**: The system detects additions, modifications, and deletions
- **Error handling**: Malformed rule files are skipped with warnings in the logs

### Sharing and Templates
You can create reusable rule templates:
- **Copy rule directories** between projects
- **Create starter templates** for common project types
- **Share agent profiles** with their custom rules intact
- **Maintain rule libraries** for different technologies or domains

## Best Practices

1. **Keep rules focused**: Each rule file should address a specific aspect of your project
2. **Use clear headings**: Structure rules with markdown headers for better readability
3. **Be specific**: Provide concrete examples and clear "do's and don'ts"
4. **Version control**: Commit your rule files to track changes and share with team
5. **Regular maintenance**: Review and update rules as your project evolves
6. **Test rules**: Verify that rules produce the desired agent behavior
7. **Document exceptions**: Note when rules should be bypassed and why

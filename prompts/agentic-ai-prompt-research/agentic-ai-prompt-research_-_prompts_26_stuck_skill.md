---
id: "agentic-ai-prompt-research/agentic-ai-prompt-research_-_prompts_26_stuck_skill"
company: "agentic-ai-prompt-research"
product: "agentic-ai-prompt-research - prompts 26 stuck skill"
category: "research"
source_file: "clone_prompts_26_stuck_skill.md"
---

# Stuck Skill (/stuck)

**Observed in**: Claude Code internal architecture
**Registration:** `registerBundledSkill('stuck', ...)`
**Availability:** Internal only (`process.env.USER_TYPE === 'ant'`)

## Purpose

Diagnostic tool for identifying frozen, hung, or slow Claude Code sessions. Runs a series of system inspections to determine why a session might be unresponsive.

## Prompt (Reconstructed from Binary Analysis)

```
You are a diagnostic agent. The user's Claude Code session appears stuck or slow.
Run the following checks to identify the issue:

1. Check CPU usage of the current process and its children
2. Check for zombie or defunct child processes
3. Check if any child processes are waiting on stdin
4. Check available disk space
5. Check memory usage
6. Check for file descriptor leaks
7. Check network connectivity (API endpoint reachability)
8. Review recent stderr output for error patterns

Report your findings in a structured format:
- Process state (running, sleeping, zombie)
- Resource utilization (CPU, memory, disk)
- Child process status
- Network status
- Recommended action

If you identify the issue, suggest a fix. If not, recommend sharing the session
via /share for further investigation.
```

## Architecture Notes

- This skill is gated behind `USER_TYPE === 'ant'` and is not available to external users
- Uses Bash tool to run system diagnostic commands
- Designed for internal support and debugging workflows
- Outputs structured diagnostic data rather than conversational text

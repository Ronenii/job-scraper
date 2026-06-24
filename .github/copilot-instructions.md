# Copilot Instructions

Full project guide is in `AGENTS.md` at the repo root — read that first.
It contains: architecture map, conventions, source tiers, how to add an adapter,
testing rules, the incremental-commits workflow, the implementation-tracker
workflow, and the full sub-agent lifecycle team with per-agent prompts.

## Copilot-specific notes
- Use `rg` (ripgrep) for file searches, not `grep`.
- Sub-agents: use `task(..., agent_type="explore")` for architect/reviewer
  (read-only), `task(..., agent_type="task")` for developer/tester/debugger/
  docs-cleanup. Prompts are in `AGENTS.md` → "Sub-agent lifecycle team".
- Skills (incremental-commits, implementation-tracker) are inlined in `AGENTS.md`
  — follow them directly. Skills live in `.claude/skills/` in the repo; copy to
  `~/.agents/skills/` manually if you want native skill loading.

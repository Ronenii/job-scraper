# implementation-tracker

An AI coding agent skill that maintains checkbox-based progress tracking for
multi-session implementation work. It keeps a long-running implementation plan in
sync with what's actually been built, so agents like Claude Code, Codex, Gemini,
and Copilot can pick up where a prior session left off without duplicating work or
losing context.

## What it does

When you're working from a large implementation plan across several sessions, this
skill guides the coding agent to:

- **Resume reliably** — read the tracker before writing any code, then report how
  many tasks are done, what was last completed, and what's next.
- **Track at the right granularity** — one checkbox per discrete, verifiable unit
  of work (roughly 15 minutes to a few hours each).
- **Update as it goes** — mark tasks complete before moving on, note in-progress
  and blocked work inline, and preserve history when the plan changes.

## When it triggers

The skill activates whenever you're working from an implementation plan or resuming
ongoing coding work — for example:

- "Continue where we left off"
- "What's left to do?" / "What's next?"
- "Pick up from yesterday"
- Any session where a `PLAN.md`, `IMPLEMENTATION_PLAN.md`, or
  `IMPLEMENTATION_TASKS.md` is present, even if you don't mention it.

## How it works

1. **Session Start Protocol** — The agent first looks for a tracking file (inline
   checkboxes in `IMPLEMENTATION_PLAN.md` / `PLAN.md` / `docs/IMPLEMENTATION_PLAN.md`,
   or a standalone `IMPLEMENTATION_TASKS.md`). If it finds one, it summarizes
   progress before doing anything else. If it doesn't, it asks where the plan is
   rather than guessing.
2. **Setting up tracking** — If the plan already has checkboxes, it's used in place.
   If not, the agent creates an `IMPLEMENTATION_TASKS.md` and extracts tasks from the
   plan at consistent granularity.
3. **Updating checkboxes** — Tasks are marked `[x]` only when done, updated one at a
   time, and the history of completed and changed work is preserved.

See [SKILL.md](SKILL.md) for the full instructions the agent follows.

## Installation

Install the repository where your AI coding agent looks for skills or reusable
instructions.

### Claude Code

```bash
# Personal skills (available across all projects)
git clone https://github.com/Ronenii/implementation-tracker.git \
  ~/.claude/skills/implementation-tracker

# Or scoped to a single project
git clone https://github.com/Ronenii/implementation-tracker.git \
  .claude/skills/implementation-tracker
```

### Codex

```bash
# Personal skills (available across all projects)
git clone https://github.com/Ronenii/implementation-tracker.git \
  ~/.codex/skills/implementation-tracker

# Or scoped to a single project, if your Codex setup loads project skills
git clone https://github.com/Ronenii/implementation-tracker.git \
  .codex/skills/implementation-tracker
```

### Gemini CLI

```bash
# Personal skills, if your Gemini setup loads user-level skills
git clone https://github.com/Ronenii/implementation-tracker.git \
  ~/.gemini/skills/implementation-tracker

# Or scoped to a single project
git clone https://github.com/Ronenii/implementation-tracker.git \
  .gemini/skills/implementation-tracker
```

### Copilot CLI and other agents

Use the equivalent skills or instructions directory for your agent:

```bash
git clone https://github.com/Ronenii/implementation-tracker.git \
  path/to/your/agent/skills/implementation-tracker
```

If your agent does not support skills directly, add the contents of
[SKILL.md](SKILL.md) to the agent's project instructions file, such as
`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or another instruction file your tool
loads automatically.

Once installed, the skill loads automatically when its trigger conditions are met.

## License

[MIT](LICENSE) © 2026 Ronen Gelmanovich

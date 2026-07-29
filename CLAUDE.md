# CLAUDE.md for TIL Repository

This repo holds my "Today I Learned" notes, now packaged as
[Agent Skills](https://agentskills.io/specification) under `skills/`.

## Commands
- Test: `python3 -m unittest test_til.py`
- Test single test: `python3 -m unittest test_til.TestTILTool.test_til_entry_parsing`
- Run the TIL CLI (uv launcher): `./til <command>`

The CLI now matches the `skills/` layout: `./til list`, `./til search`,
`./til show`, `./til path`, `./til execute`, `./til run`, and
`./til validate` all operate on `skills/<slug>/SKILL.md`.
`./til path <slug>` prints the absolute SKILL.md path. `./til execute`
is mechanical (run a `(executable)` section's shell blocks); `./til run`
is agentic (wrap the whole skill in an "apply this to this host"
imperative and dispatch it via [airan](https://github.com/kfet/airan),
a soft dependency needed by that command alone).
`./til validate` enforces the Agent Skill spec — frontmatter `name` must
equal the directory name and match `[a-z0-9-]{1,64}`, `description` must
exist and be ≤1024 chars, the body must start with a level-1 heading, and
code blocks must declare a language. Shell completion lives under
`completions/` (see `completions/README.md`).

## Code Style Guidelines
- Python: Follow PEP 8 conventions
- Use type hints for function parameters and return values
- Error handling: Use try/except blocks with specific exceptions
- Variable naming: snake_case for variables and functions
- Class naming: PascalCase for classes
- Imports: Standard library first, then third-party, then local modules
- Docstrings: Multi-line docstrings with summary line, description, and args

## Skill Authoring Conventions
- Each skill lives at `skills/{topic}-{slug}/SKILL.md`
- A SKILL.md is **not** executable and carries **no shebang**: byte 0 must
  be `---` or frontmatter parsers (including fir's) silently drop the
  skill. Hand a skill to an agent with `til run <slug>`, which wraps the
  doc in an "apply this to the current host" imperative and dispatches it
  through [airan](https://github.com/kfet/airan)
- `til run` sets no backend — resolution is left to `$AIRAN_BACKEND` then
  the host default (`airan config NAME`), so a skill runs with whatever
  agent the host has. airan is a soft dependency: only `til run` needs it
- The CLI still strips a stray leading `#!` line before parsing/rendering,
  as defensive tolerance — do not rely on it
- Frontmatter has `name` (must equal the directory name, lowercase
  letters/digits/hyphens only, ≤64 chars) and `description` (≤1024
  chars; lead with the title, then a "Use when..." activation hint)
- Body is regular Markdown. Start with a level-1 heading describing
  the topic, use fenced code blocks with language tags, mark
  executable sections with "(executable)" in the heading

## File Organization
- All knowledge entries: `skills/{topic}-{specific_knowledge}/SKILL.md`
- Top-level non-skill files: `README.md`, `CLAUDE.md`, `TODO.md`,
  `install.sh`, `til` (CLI launcher), `til_cli/` (CLI source),
  `test_til.py`, `completions/` (shell completion scripts),
  `tools/` (one-shot maintenance scripts; e.g.
  `tools/fix_skill_validations.py` adds language tags to fenced code
  blocks)

## Rendering
`til show` pipes Markdown through `glow` or `bat` when stdout is a TTY
and `NO_COLOR` is unset; pass `--plain` (or set `TIL_RENDERER=plain`)
to force raw output. Honour these conventions when adding new
rendering paths.

# Ideas on how to make better use of the TIL collection

## ✅ Auto-update local installation in the background

## ✅ Make it installable

## ✅ Make it searchable locally

Implemented as `./til search <term>` and `./til list`.

## ✅ Ignore til_cli folder while using the til tool

Loader now only picks up `skills/<slug>/SKILL.md` — README, LICENSE,
tool docs, and stray Markdown are ignored.

## ✅ Retarget `til validate` to the Agent Skill format

Frontmatter `name` / `description` checks, dir/name consistency, body
must start with `# H1`, code blocks need a language tag.

## ✅ Auto-complete in shell

Bash and zsh scripts live in `completions/` and use the hidden
`til _complete` helper.

## ✅ Syntax highlight when printing the MD files

`til show` renders Markdown when stdout is a TTY via `glow` (preferred)
or `bat`, with a plain fallback. Respects `NO_COLOR`, the `--plain`
flag, and the `TIL_RENDERER` env var.

## ✅ Improve install UX

`install.sh` verifies `til` is on `PATH` after install, prints
shell-specific guidance if not, and optionally installs the shell
completion scripts from `completions/`.

## ✅ Turn this collection into executable configurations

Implicitly done by the migration to Agent Skills: every
`skills/<slug>/SKILL.md` is consumable by a skill-aware AI agent, which
reads, plans, and runs the steps interactively. A dedicated
`til apply <topic>` runner is not needed — point any AI agent at the
repo and ask it to apply the relevant skills.

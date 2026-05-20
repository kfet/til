# Ideas on how to make better use of the TIL collection

## Improve install UX

Verify `til` is on `PATH` after install; print a shell-specific source line
if not. Optionally install the bash/zsh completion scripts from
`completions/`.

## Syntax highlight when printing the MD files

Render Markdown when stdout is a TTY (e.g. via `rich`, `bat`, or `glow`)
with a plain-text fallback. Respect `NO_COLOR` and `--plain`.

## Turn this collection into executable configuration(s)

For example, when setting up a new environment:
`til apply git` could run all Git-related setup steps. Notes:

- Don't reuse `til config` — that's already the CLI's "set repo path" verb.
- Topic discovery needs either slug-prefix parsing (`git-*`) or explicit
  `topic:` / `tags:` frontmatter.
- Use a single plan-then-confirm step, not per-block prompts. Add
  `--dry-run` and `--yes`.

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

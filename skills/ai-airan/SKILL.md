#!/usr/bin/env airan
---
name: ai-airan
description: "Run markdown files as AI prompts with the airan shebang dispatcher. TIL note about ai. Use when working with ai and the user mentions airan, executable prompts, agent files, shebang dispatch, or related topics."
---

# Run markdown files as AI prompts with the airan shebang dispatcher

## Summary

[airan](https://github.com/kfet/airan) is `env` for AI coding agents.
`airan FILE` resolves a backend and execs that agent CLI with the
**whole file** as the prompt, so a prompt spec is written once and the
backend swapped with one line.

```bash
curl -fsSL https://raw.githubusercontent.com/kfet/airan/main/install.sh | sh
brew install kfet/ai/airan
```

The installer downloads a pre-built binary — no Go and no build box.

Do not confuse it with `andisearch/airun` (`#!/usr/bin/env ai`, different
project) or the PyPI package `airun` (unrelated, abandoned).

## Details

```markdown
#!/usr/bin/env airan
---
backend: claude
---
Refactor src/parser into async/await. Don't touch the public API.
```

```bash
chmod +x build.agent
./build.agent
```

Backend precedence: frontmatter `backend:` → `$AIRAN_BACKEND` →
`airan config NAME`. Built-ins are `claude`, `fir`, `aider`.

```bash
airan backends        # list backends + $PATH availability, marking the default
airan config fir      # set the host default
```

Frontmatter is **optional** — omit it and resolution falls through to
env then host default, which is what you want for files meant to run on
many hosts. Pinning `backend:` hard-codes one agent.

Custom backends shadow built-ins of the same name:

```bash
airan backends add mycli mycli --message {{prompt}}
```

## Verify (executable)

Test dispatch without burning a real agent run:

```bash
airan backends add echotest /bin/echo '{{prompt}}'
printf '#!/usr/bin/env airan\n---\nbackend: echotest\n---\nHELLO\n' > /tmp/t.agent
chmod +x /tmp/t.agent && /tmp/t.agent   # echoes the file back, shebang and frontmatter included
airan backends remove echotest
```

## Gotchas

Verified with airan v0.1.2 on linux/arm64.

- **A fir `SKILL.md` can never be executable.** fir requires `---` on
  line 1; airan requires the shebang there. Adding a shebang makes the
  skill vanish from `fir skills list` — silently, with no error. Keep
  executable agent files separate from `SKILL.md`.
- **`{{prompt}}` must be a standalone argument.**
  `add x /bin/echo '{{prompt}}'` works; `'PRE:{{prompt}}'` is rejected
  with `backend command must include the {{prompt}} placeholder`, even
  though the string plainly contains it. Sibling args are fine
  (`/bin/echo -n '{{prompt}}'`).
- **`airan --version` is not a flag** — it treats it as a filename and
  fails with `open --version: no such file or directory`. Use
  `airan config` to confirm it runs.
- **Running an executable doc really launches the agent.** Dispatching a
  long file through the `fir` backend ran a full agent session and
  blocked past 60s. Use the echo backend for mechanical tests.
- **The whole file is the prompt**, frontmatter included, so the body
  must read as instructions to an agent.

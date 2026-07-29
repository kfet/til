---
name: ai-airan
description: "Dispatch markdown prompts to any AI coding agent with airan, and hand a TIL skill to an agent with `til run`. TIL note about ai. Use when working with ai and the user mentions airan, backend dispatch, agent files, running a skill against the current host, or related topics."
---

# Dispatch markdown prompts to an AI agent with airan (and `til run`)

## Summary

[airan](https://github.com/kfet/airan) is `env` for AI coding agents.
`airan FILE` resolves a backend and runs that agent CLI with the
**whole file** as the prompt, so a prompt spec is written once and the
backend swapped with one line.

```bash
curl -fsSL https://raw.githubusercontent.com/kfet/airan/main/install.sh | sh
brew install kfet/ai/airan
```

The installer downloads a pre-built binary — no Go and no build box.

Do not confuse it with `andisearch/airun` (`#!/usr/bin/env ai`, different
project) or the PyPI package `airun` (unrelated, abandoned).

## `til run` — hand a whole TIL to an agent

```bash
til run tmux-tpm-install
```

`til run` reads `skills/<slug>/SKILL.md`, **prepends an imperative**
("apply this TIL to the current host, verify with the commands in the
doc, report what changed"), writes the wrapped prompt to a temp file and
dispatches it through `airan`. The imperative is the point: a bare skill
doc is a reference, and an agent handed one has to guess whether it is
being asked to read, explain, or do. Wrapping removes the guess.

`til run` is agentic; `til execute ENTRY SECTION` is mechanical — it runs
the shell blocks under a `## Section (executable)` heading, with a
confirmation prompt, and no agent involved. Two different tools.

airan is a **soft dependency**: only `til run` needs it, and `til run`
hard-errors with an install hint if it is missing. `til run` sets no
backend, so whatever the host has configured is what runs.

## Backend resolution

Precedence: frontmatter `backend:` → `$AIRAN_BACKEND` → `airan config
NAME`. Built-ins are `claude`, `fir`, `aider`.

```bash
airan backends        # list backends + $PATH availability, marking the default
airan config fir      # set the host default
```

Frontmatter is **optional** — omit it and resolution falls through to
env then host default, which is what you want for files meant to run on
many hosts. Pinning `backend:` hard-codes one agent, so TIL skills never
set it.

Custom backends shadow built-ins of the same name:

```bash
airan backends add mycli mycli --message {{prompt}}
```

## Why a SKILL.md has no shebang

Making each `SKILL.md` directly executable (`#!/usr/bin/env airan` on
line 1) was tried and abandoned. Kernel exec needs `#!` at bytes 0–1;
frontmatter parsers test byte 0 for `---`. Mutually exclusive.

- **A shebang makes a skill vanish.** fir requires `---` on line 1; with
  a shebang the skill disappears from `fir skills list` — silently, with
  no error. YAML tolerates it (`#` is a comment), so nothing complains.
- **A shebang cannot prepend anything.** The kernel passes the file as-is,
  so the agent receives a bare reference doc. A runner (`til run`) can
  wrap it in an instruction. This is the deciding advantage.

`til` still strips a stray leading `#!` line before parsing and
rendering, as cheap defensive tolerance — but skills must not carry one.

## Verify (executable)

Test dispatch without burning a real agent run:

```bash
airan backends add echotest /bin/echo '{{prompt}}'
printf -- '---\nbackend: echotest\n---\nHELLO\n' > /tmp/t.agent
AIRAN_BACKEND=echotest airan /tmp/t.agent   # echoes the file back
airan backends remove echotest
```

## Gotchas

Verified with airan v0.1.2 on linux/arm64.

- **`airan` takes a FILE, not a string.** A runner that wants to send a
  constructed prompt must write a temp file. If you `os.execvp` you can
  never delete it — `subprocess.run` still inherits the TTY these
  interactive backends need, so use that and clean up in `finally`.
- **`{{prompt}}` must be a standalone argument.**
  `add x /bin/echo '{{prompt}}'` works; `'PRE:{{prompt}}'` is rejected
  with `backend command must include the {{prompt}} placeholder`, even
  though the string plainly contains it. Sibling args are fine
  (`/bin/echo -n '{{prompt}}'`).
- **`airan --version` is not a flag** — it treats it as a filename and
  fails with `open --version: no such file or directory`. Use
  `airan config` to confirm it runs.
- **Dispatching really launches the agent.** A long file through the
  `fir` backend ran a full agent session and blocked past 60s. Use the
  echo backend for mechanical tests.
- **The whole file is the prompt**, frontmatter included, so the body
  must read as instructions to an agent.

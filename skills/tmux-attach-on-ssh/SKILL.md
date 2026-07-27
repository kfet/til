---
name: tmux-attach-on-ssh
description: "Attach to (or create) a tmux session automatically on interactive SSH login, without breaking scp/rsync or non-interactive agent sessions. Use when working with tmux and the user mentions attaching on ssh, auto-tmux on login, or worries that it will interfere with automation."
---

# Attach to tmux session on SSH connect

Drop into a persistent tmux session on every interactive SSH login, so
work survives a dropped connection and is there again on reconnect.

Pair this with `tmux-conf-create-tmux-session-if-none` — `new-session`
in `~/.tmux.conf` makes a bare `tmux a` create a session when none
exists, so the very first login works too.

## Configuration

Add to the rc file of your **login shell** — `~/.zshrc` for zsh,
`~/.bashrc` for bash (add it to both if you switch between them):

```bash
# attach (or create, via `new-session` in .tmux.conf) on interactive
# SSH login only
if [ -z "$TMUX" ] && [ -n "$SSH_TTY" ]; then
    tmux a
fi
```

Two guards, each doing a distinct job:

- `-z "$TMUX"` — don't attach from *inside* tmux, which would nest
  sessions (or fail outright) every time you open a new pane.
- `-n "$SSH_TTY"` — only on SSH logins that were given a terminal.

## This does NOT break automation or AI coding agents

A common worry — and the reason this gets left out of server setups —
is that auto-attaching will hijack scripted SSH, file copies, or an AI
agent driving the box. It does not, because **`SSH_TTY` is only set
when sshd allocates a PTY**, which happens exclusively for interactive
logins.

Unaffected, because `SSH_TTY` is unset:

| Invocation | Behaviour |
| --- | --- |
| `ssh host 'cmd'` (non-interactive; how agents and scripts run) | no attach |
| `scp` / `rsync` / `sftp` | no attach |
| Ansible, CI, cron-over-SSH | no attach |
| `ssh host` (interactive login) | attaches |
| `ssh -t host cmd` (explicit PTY request) | attaches |

Belt-and-braces: distro `~/.bashrc` files already start with an
early-return for non-interactive shells, and non-interactive **zsh**
does not read `~/.zshrc` at all — so the block is usually never even
reached in automation.

There is a real benefit for agents, too: when an agent *does* open an
interactive session (or you attach to inspect what it is doing), tmux is
already there — no separate "start a tmux first" step, and long-running
work it kicked off keeps running after the connection drops.

The one case to be careful about is a **broken** attach loop — e.g.
`tmux a` with no `new-session` in `~/.tmux.conf` and no session running
returns an error on every login, and a mistyped guard that runs `tmux a`
unconditionally in a *non*-SSH shell can lock you out of a local
console. Verify before relying on it.

## Verify (executable)

Run from another machine after deploying. The first two must print a
normal result with no tmux involvement; the third must land in tmux:

```bash
# 1. non-interactive: expect empty SSH_TTY and no attach
ssh HOST 'echo "ssh_tty=[$SSH_TTY] tmux=[$TMUX]"'

# 2. file copy: expect a clean transfer
echo hi | ssh HOST 'cat > /tmp/attach_probe && echo copied'

# 3. interactive: expect to be inside tmux
ssh -t HOST 'echo "ssh_tty=[$SSH_TTY]"; tmux ls'
```

## Related

- `tmux-conf-create-tmux-session-if-none` — makes `tmux a` create a
  session when none exists (required for the first login to work).

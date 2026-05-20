---
name: tmux-attach-on-ssh
description: "Attach to tmux session on SSH connect. TIL note about tmux. Use when working with tmux and the user mentions attach on ssh or related topics."
---

# Attach to tmux session on SSH connect

On each SSH attach to a tmux session. See also [create_tmux_session_if_none.md](conf-create_tmux_session_if_none.md)

`cat ~/.bashrc`
```bash
if [[ -z $TMUX ]] && [[ -n $SSH_TTY ]]; then
    tmux a
fi
```

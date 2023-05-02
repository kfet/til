## Attach to tmux session on SSH connect

On each SSH attach to a tmux session. See also [create_tmux_session_if_none.md](conf-create_tmux_session_if_none.md)

`cat ~/.bashrc`
```
if [[ -z $TMUX ]] && [[ -n $SSH_TTY ]]; then
    tmux a
fi
```

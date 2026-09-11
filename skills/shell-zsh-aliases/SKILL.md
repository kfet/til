---
name: shell-zsh-aliases
description: "The zsh ls/history/option aliases worth defining by hand, and how to pick them from your own history. TIL note about shell. Use when setting up aliases in .zshrc, when a framework that provided l/ll/la is removed, or when the user asks which aliases to keep."
---

# zsh aliases worth defining

Frameworks ship hundreds of aliases and you use four of them. Define those
four by hand.

Goes in `~/.zshrc`, anywhere after the options block.

```zsh
alias l='ls -lah'
alias ll='ls -lh'
alias la='ls -lAh'
alias ls='ls -G'          # GNU coreutils: ls --color=auto
```

`-G` is the BSD/macOS colour flag; on Linux it means "no group column" and
will silently do the wrong thing, so pick per platform rather than copying
blind.

`l` is the one that matters. Aliasing `ls` itself is the only entry here that
changes an existing command — everything else is new names, so nothing you
already type can break.

## Pick the rest from your own history

Do not guess. Count what you actually run:

```bash
awk -F';' '{print $2}' ~/.zsh_history | awk '{print $1}' | sort | uniq -c | sort -rn | head -30
```

Then check whether the framework aliases you are about to reinstate ever
appear:

```bash
awk -F';' '{print $2}' ~/.zsh_history | awk '{print $1}' | sort -u \
  | grep -xE 'l|ll|la|gst|gco|gcm|gd|gp|ga|gcb|glog'
```

A four-figure count next to bare `git` with zero `gst`/`gco` means the git
alias set was decoration — do not port it.

## Related options

The other half of what feels like "aliases" is `setopt`:

```zsh
setopt auto_cd               # `..` and bare dir names cd
setopt interactive_comments  # # works on the command line
setopt hist_ignore_space     # leading space keeps a line out of history
```

## Verify

Aliases are expanded at parse time, so a syntax error in one is silent until
used. Check the shell starts clean and the names resolve — in tmux, because
`zsh -i -c` run from an interactive shell can fight over the tty and suspend
it:

```bash
tmux new-session -d -s alchk
tmux send-keys -t alchk 'zsh -i -c "alias l; alias ls" > /tmp/alchk.txt 2>&1' Enter
sleep 5; cat /tmp/alchk.txt; tmux kill-session -t alchk
```

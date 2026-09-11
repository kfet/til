---
name: shell-zsh-aliases
description: "The zsh ls/history/option aliases worth defining by hand, like l/ll/la"
---

In `~/.zshrc`.

Options (`setopts`) block:
```zsh
setopt auto_cd               # `..` and bare dir names cd
setopt interactive_comments  # # works on the command line
setopt hist_ignore_space     # leading space keeps a line out of history
```


Anywhere after the options block:
```zsh
alias l='ls -lah'
alias ll='ls -lh'
alias la='ls -lAh'

# NOTE: platform specfic!!!
alias ls='ls -G' # BSD/macOS ONLY
alias ls='ls --color=auto' # Linux ONLY
```

---
name: shell-zsh-drop-oh-my-zsh
description: "Replace oh-my-zsh with plain zsh, keeping only the aliases and options you actually use. TIL note about shell. Use when removing oh-my-zsh, when zsh startup is slow because of a framework, or when the user asks which omz aliases to keep."
---

# Drop oh-my-zsh, keep what you used

oh-my-zsh is ~16MB and one unconditional, uncached `compinit` you cannot get
underneath (see `shell-zsh-cache-compinit`). Most of what it gives back is a
prompt, a handful of aliases, and some `setopt` lines — all cheap to inline.

## Decide from history, not from taste

Do not guess which of the ~150 git aliases you would miss. Count:

```bash
awk -F';' '{print $2}' ~/.zsh_history | awk '{print $1}' | sort | uniq -c | sort -rn | head -30
```

If the top line is a bare `git` with four figures next to it and `gst`/`gco`
never appear, the git plugin was decoration. The one that reliably *does* show
up is `l`.

## The replacement pieces

```zsh
# --- options omz set for you
setopt prompt_subst auto_cd interactive_comments
setopt append_history share_history inc_append_history
setopt hist_ignore_dups hist_ignore_space hist_verify
HISTFILE=~/.zsh_history; HISTSIZE=50000; SAVEHIST=50000

# --- the ls aliases (this is the bit you will miss)
alias l='ls -lah'
alias ll='ls -lh'
alias la='ls -lAh'
alias ls='ls -G'          # GNU coreutils: --color=auto

# --- completion behaviour
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Za-z}'

# --- arrow keys search by prefix, not blindly
bindkey -e
autoload -Uz up-line-or-beginning-search down-line-or-beginning-search
zle -N up-line-or-beginning-search
zle -N down-line-or-beginning-search
bindkey '^[[A' up-line-or-beginning-search
bindkey '^[[B' down-line-or-beginning-search
```

For the prompt use `shell-zsh-fast-git-prompt` — it reproduces the
`robbyrussell` look without `vcs_info`. Then add `shell-zsh-cache-compinit`,
`shell-zsh-cache-tool-completions` and `shell-zsh-nvm`, which only become
possible once your rc owns `compinit`.

## Order

Rewrite `~/.zshrc` *before* deleting `~/.oh-my-zsh`, and keep the framework
around until a new shell is verified — `mv ~/.oh-my-zsh /tmp/`, not `rm -rf`.
Also grep `~/.zshenv` and `~/.zprofile`: aliases and `brew shellenv` often
live there and are easy to mistake for omz features.

## Verify without hanging your terminal

`zsh -i -c ...` from inside another interactive shell fights over the tty and
can suspend it. Run the check in tmux and read the file:

```bash
tmux new-session -d -s zshchk
tmux send-keys -t zshchk 'zsh -i -c "echo aliases=\$(alias|wc -l) git=\${_comps[git]:-MISSING}" > /tmp/zshchk.txt 2>&1' Enter
sleep 5; cat /tmp/zshchk.txt; tmux kill-session -t zshchk
```

Measure with `shell-zsh-measure-startup`. A real macOS config went 213ms →
114ms with the framework gone and the compinit dump cached.

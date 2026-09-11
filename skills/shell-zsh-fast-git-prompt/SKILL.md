---
name: shell-zsh-fast-git-prompt
description: "Show the git branch, and a dirty marker, in a zsh prompt. Very fast."
---

In `~/.zshrc`:
```zsh
setopt prompt_subst

_git_branch() {
  REPLY=""
  local d=$PWD g
  while [[ $d != / ]]; do
    [[ -e $d/.git ]] && { g=$d/.git; break }
    d=${d:h}
  done
  [[ -n $g ]] || return
  if [[ -f $g ]]; then                          # worktrees / submodules
    local gd=$(<$g)
    g=${gd#gitdir: }
  fi
  local head
  head=$(<$g/HEAD) 2>/dev/null || return
  if [[ $head == ref:* ]]; then REPLY=${head##*/}   # branch
  else REPLY=${head[1,7]}                            # detached: short sha
  fi
}

# If you already have a `precmd`, merge rather than replace
precmd() {
  _git_branch
  if [[ -n $REPLY ]]; then _pgit=" %F{blue}git:(%F{red}${REPLY}%F{blue})%f"
  else _pgit=''; fi
}

PROMPT='%(?:%F{green}➜:%F{red}➜)%f %F{cyan}%c%f${_pgit} '
```

## Dirty marker

The branch is free; dirty is not — nothing in `.git` records it, so it costs a
`git` fork. ~17-22ms per prompt on macOS, scales with tracked files.

Synchronous — replace the `precmd` above:
```zsh
precmd() {
  _git_branch
  if [[ -n $REPLY ]]; then
    local dirty=''
    # --no-optional-locks: don't rewrite .git/index and contend for the lock
    # head -1: stop at the first change instead of listing every file
    # add -uno to ignore untracked (faster, misses new files)
    [[ -n $(command git --no-optional-locks status --porcelain 2>/dev/null | head -1) ]] \
      && dirty=' %F{yellow}✗%f'
    _pgit=" %F{blue}git:(%F{red}${REPLY}%F{blue})%f${dirty}"
  else _pgit=''; fi
}
```

Async — prompt stays instant, `✗` lands a beat later:
```zsh
typeset -g _pgit='' _pdirty=''

_dirty_cb() {
  local fd=$1 line new=''
  if read -r line <&$fd; then [[ -n $line ]] && new=' %F{yellow}✗%f'; fi
  zle -F $fd; exec {fd}<&-          # MUST do both, else an fd leaks per prompt
  [[ $new == $_pdirty ]] && return  # skip redraw or the line flickers on Enter
  _pdirty=$new; zle reset-prompt
}

precmd() {
  _git_branch
  if [[ -n $REPLY ]]; then _pgit=" %F{blue}git:(%F{red}${REPLY}%F{blue})%f"
  else _pgit=''; _pdirty=''; return; fi   # clear, or a stale ✗ follows you out
  local fd
  exec {fd}< <(command git --no-optional-locks status --porcelain 2>/dev/null | head -1)
  zle -F $fd _dirty_cb
}

PROMPT='%(?:%F{green}➜:%F{red}➜)%f %F{cyan}%c%f${_pgit}${_pdirty} '
```

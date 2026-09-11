---
name: shell-zsh-fast-git-prompt
description: "Show the git branch in a zsh prompt. Very fast."
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

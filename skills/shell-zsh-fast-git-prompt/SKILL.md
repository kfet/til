---
name: shell-zsh-fast-git-prompt
description: "Show the git branch, and a dirty marker, in a zsh prompt. Very fast."
---

In `~/.zshrc`:

```zsh
setopt prompt_subst

git_prompt_branch() {
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
  git_prompt_branch
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

PROMPT='%(?:%F{green}➜:%F{red}➜)%f %F{cyan}%c%f${_pgit} '
```

NOTE: Do NOT name these functions `_git_branch`, or anything matching `_git_*` —
zsh's git completion dispatches `git <sub> <TAB>` to `_git_${sub}` and will run
your prompt function under `emulate ksh` instead. Symptom, intermittent:
```
_git_branch:4: parse error: condition expected: 1
__gitcomp_direct:compset:4: can only be called from completion function
```
Leading `_` is the completion namespace generally. Keep prompt functions out.

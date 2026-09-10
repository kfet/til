---
name: shell-zsh-fast-git-prompt
description: "Show the git branch in a zsh prompt by reading .git/HEAD instead of vcs_info. TIL note about shell. Use when the prompt feels laggy, or the user mentions vcs_info, git prompt, or slow prompt."
---

# Fast git branch in a zsh prompt

`vcs_info` supports Mercurial, SVN and Bazaar, and costs it: ~146ms per prompt
on a Raspberry Pi — and ~34ms even when you are *not* in a repo. That is paid
on every Enter, not once at startup. Reading `.git/HEAD` is ~1.4ms.

Goes in `~/.zshrc`. `setopt prompt_subst` is required, and must come before
`PROMPT` is used. If you already have a `precmd`, merge rather than replace —
defining it twice silently drops the first.

`cat ~/.zshrc`:

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
  [[ -f $g ]] && g=${$(<$g)#gitdir: }          # worktrees / submodules
  local head
  head=$(<$g/HEAD) 2>/dev/null || return
  if [[ $head == ref:* ]]; then REPLY=${head##*/}   # branch
  else REPLY=${head[1,7]}                            # detached: short sha
  fi
}

precmd() {
  _git_branch
  if [[ -n $REPLY ]]; then _pgit=" %F{blue}git:(%F{red}${REPLY}%F{blue})%f"
  else _pgit=''; fi
}

PROMPT='%(?:%F{green}➜:%F{red}➜)%f %F{cyan}%c%f${_pgit} '
```

Note `PROMPT` uses single quotes — `${_pgit}` must stay unexpanded until each
prompt is drawn.

Gotcha: do **not** put `%F{...}` inside `${...:+...}` — the `{` closes the
expansion early and you get literal `master)}` in your prompt. Build the
coloured segment in `precmd`, as above.

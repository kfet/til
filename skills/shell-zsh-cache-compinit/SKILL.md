---
name: shell-zsh-cache-compinit
description: "Cache and compile the zsh completion dump so compinit is fast."
---

NOTE: Only useful if your rc owns `compinit`

In `~/.zshrc`, after any `fpath=(...)` lines and before anything that calls `compdef` or defines completions.

```zsh
fpath=(~/.zsh/completions $fpath)      # any extra completion dirs first

autoload -Uz compinit
() { # anonymous, runs immediately, keeps vars in closure
  local dump=${ZDOTDIR:-$HOME}/.zcompdump
  zmodload -F zsh/stat b:zstat 2>/dev/null
  local -a st
  if zstat -A st +mtime "$dump" 2>/dev/null && (( EPOCHSECONDS - st[1] < 86400 )); then # 24h
    compinit -C -d "$dump"
  else
    compinit -i -d "$dump"
    { rm -f "$dump.zwc"; zcompile -R -- "$dump" } &!
  fi
}
```

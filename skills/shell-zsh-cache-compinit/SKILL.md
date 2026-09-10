---
name: shell-zsh-cache-compinit
description: "Cache and compile the zsh completion dump so compinit is fast. TIL note about shell. Use when zsh startup is slow, or the user mentions compinit, zcompdump, or compinit -C."
---

# Cache and compile the zsh completion dump

Plain `compinit` scans and security-audits every `fpath` directory on every
shell start. Run the full version at most daily, otherwise trust the dump.

Goes in `~/.zshrc`. Order matters: **after** any `fpath=(...)` lines and
**before** anything that calls `compdef` or defines completions.

`cat ~/.zshrc`:

```zsh
fpath=(~/.zsh/completions $fpath)      # any extra completion dirs first

autoload -Uz compinit
() {
  local dump=${ZDOTDIR:-$HOME}/.zcompdump
  zmodload -F zsh/stat b:zstat 2>/dev/null
  local -a st
  if zstat -A st +mtime "$dump" 2>/dev/null && (( EPOCHSECONDS - st[1] < 86400 )); then
    compinit -C -d "$dump"
  else
    compinit -i -d "$dump"
    { rm -f "$dump.zwc"; zcompile -R -- "$dump" } &!
  fi
}
```

The `() { ... }` is an anonymous function — it runs immediately and keeps
`$dump` and `$st` out of your shell.

Apply once, then start a new shell to build the dump. Verify it is actually
reused — if the mtime moves on every start it is being regenerated and you get
none of the benefit:

```bash
stat -c %y ~/.zcompdump; zsh -i -c exit; stat -c %y ~/.zcompdump
```

Only useful if your rc owns `compinit`. oh-my-zsh calls `compinit -i -d`
unconditionally and re-autoloads the function itself, so this cannot be
layered underneath it. See also `shell-zsh-skip-global-compinit`.

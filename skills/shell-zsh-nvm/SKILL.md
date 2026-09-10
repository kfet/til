---
name: shell-zsh-nvm
description: "Load nvm in zsh lazily instead of sourcing nvm.sh at every startup. TIL note about shell. Use when setting up node/nvm in zsh, or when a shell is slow to open and nvm is in .zshrc."
---

# Lazy-load nvm in zsh

Sourcing `nvm.sh` at startup is routinely the most expensive line in a
`.zshrc` — measured at ~2s on slow storage, ~515ms via the `zsh-nvm` plugin.
You rarely need nvm itself, only `node` on `PATH`:

```zsh
export NVM_DIR="$HOME/.nvm"
if [[ -s "$NVM_DIR/nvm.sh" ]]; then
  # default node on PATH without sourcing nvm at all
  if [[ -s "$NVM_DIR/alias/default" ]]; then
    _nvm_def=$(<"$NVM_DIR/alias/default")
    for _d in "$NVM_DIR/versions/node/v${_nvm_def#v}"*/bin(N); do
      path=($_d $path); break
    done
    unset _nvm_def _d
  fi
  _nvm_load() {
    unfunction nvm node npm npx 2>/dev/null
    source "$NVM_DIR/nvm.sh"
    [[ -s "$NVM_DIR/bash_completion" ]] && source "$NVM_DIR/bash_completion"
  }
  nvm()  { _nvm_load; nvm "$@" }
  node() { _nvm_load; command node "$@" }
  npm()  { _nvm_load; command npm "$@" }
  npx()  { _nvm_load; command npx "$@" }
fi
```

The shims `unfunction` themselves before delegating, so the real load happens
once per shell and only if used. Verify:

```bash
zsh -i -c 'node -v; nvm current'
```

The nvm installer appends an eager `source` block to `~/.zshrc` — delete it
and use the above.

If you are stuck on the oh-my-zsh `zsh-nvm` plugin, it has a lazy mode, but it
must be set *above* the `plugins=(...)` line:

```zsh
export NVM_LAZY_LOAD=true
export NVM_COMPLETION=false
```

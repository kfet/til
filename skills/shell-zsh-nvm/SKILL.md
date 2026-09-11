---
name: shell-zsh-nvm
description: "Load nvm in zsh lazily instead of sourcing nvm.sh at every startup."
---

In `.zshrc`:
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

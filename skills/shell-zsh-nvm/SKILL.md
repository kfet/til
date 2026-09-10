---
name: shell-zsh-nvm
description: "Load nvm in zsh without paying its ~2s startup cost — lazy shims instead of sourcing nvm.sh. TIL note about shell. Use when setting up node/nvm in zsh, when a shell is slow to open and nvm is in .zshrc, or when the oh-my-zsh zsh-nvm plugin is mentioned."
---

# Lazy-load nvm in zsh

`nvm.sh` is a large shell script. Sourcing it at every shell start is
routinely the single most expensive line in a `.zshrc` — measured at **~2s**
on one machine (direct `source`) and **~515ms** on another (via the `zsh-nvm`
oh-my-zsh plugin). That is paid on every new terminal, tmux pane and ssh
login. Slow storage makes it worse.

You almost never need nvm itself — you need `node` on `PATH`. So put the
default version's bin directory on `PATH` directly, and defer the rest until
something actually calls `nvm`, `node`, `npm` or `npx`.

## The lazy setup (no framework)

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

The shims `unfunction` themselves before delegating, so the cost is paid once
per shell and only if you actually use node.

Verify it still works:

```bash
zsh -i -c 'node -v; nvm current'
```

## Installing nvm itself

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
```

The installer appends an eager `source` block to `~/.zshrc` — delete it and
use the lazy block above instead.

## Do not use the zsh-nvm plugin

The older advice was to clone `lukechilds/zsh-nvm` into
`~/.oh-my-zsh/custom/plugins/` and add it to `plugins=(...)`. That pulls in a
whole framework for one feature, and in its default eager mode the plugin
still cost ~515ms per shell. See `shell-zsh-startup-profiling`.

If you are stuck on oh-my-zsh and cannot remove it, the plugin does support
lazy mode — but it must be set **before** the plugin is sourced, i.e. above
the `plugins=(...)` line:

```zsh
export NVM_LAZY_LOAD=true
export NVM_COMPLETION=false
plugins=(git zsh-nvm)
```

On one machine that alone took startup from 646ms to 164ms. The
framework-free block above is still preferable: no dependency, same
behaviour.

Refs: [nvm](https://github.com/nvm-sh/nvm) ·
[zsh-nvm](https://github.com/lukechilds/zsh-nvm)

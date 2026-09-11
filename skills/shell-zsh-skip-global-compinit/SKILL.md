---
name: shell-zsh-skip-global-compinit
description: "Stop zsh running compinit twice on Debian-family systems."
---

On Debian-family distros, `/etc/zsh/zshrc` runs an unconditional, uncached `compinit` before `~/.zshrc`,
which then runs it again. The escape hatch is documented in that file:

In `~/.zshenv` (not `.zshrc` — the global rc runs first):
```bash
skip_global_compinit=1
```

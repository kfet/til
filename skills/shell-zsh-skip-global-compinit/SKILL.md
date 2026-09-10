---
name: shell-zsh-skip-global-compinit
description: "Stop zsh running compinit twice on Debian-family systems. TIL note about shell. Use when zsh startup is slow, or the user mentions skip_global_compinit, slow shell, or compinit."
---

# Stop zsh running compinit twice

On Debian/Ubuntu/Raspbian, `/etc/zsh/zshrc` runs an unconditional, uncached
`compinit` before your `~/.zshrc` — which then runs it again. The escape hatch
is documented in that file:

```bash
echo 'skip_global_compinit=1' >> ~/.zshenv
```

Must be in `.zshenv`, not `.zshrc` — the global rc runs first.

Worth ~350ms per shell on a Raspberry Pi, ~15ms on x86. Check for a third
`compinit` in your own rc while you are there:

```bash
grep -n compinit ~/.zshrc
```

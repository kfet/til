---
name: shell-zsh-cache-tool-completions
description: "Replace eval-based shell completions with cached files so startup spawns no subprocesses. TIL note about shell. Use when a .zshrc contains eval \"$(tool completion zsh)\", or zsh startup is slow."
---

# Cache tool completions to files

Every `eval "$(tool completion zsh)"` in your rc is a process spawn on every
shell start. Generate them once instead:

```bash
mkdir -p ~/.zsh/completions
uv generate-shell-completion zsh  > ~/.zsh/completions/_uv
uvx --generate-shell-completion zsh > ~/.zsh/completions/_uvx
gh completion -s zsh              > ~/.zsh/completions/_gh
rustup completions zsh            > ~/.zsh/completions/_rustup
kubectl completion zsh            > ~/.zsh/completions/_kubectl
cp ~/.bun/_bun                      ~/.zsh/completions/_bun 2>/dev/null

rm -f ~/.zcompdump*   # force one rebuild so the new files register
```

Then put the directory on `fpath` **before** `compinit` runs:

```zsh
fpath=(~/.zsh/completions $fpath)
```

Re-run after upgrading the tools. On slow storage each `eval` costs
150-600ms warm and several seconds cold.

`direnv hook zsh` is the exception — it must run at startup, and is cheap.

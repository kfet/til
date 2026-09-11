---
name: shell-zsh-cache-tool-completions
description: "Replace eval-based completions with cached files, no subprocesses."
---

Run once. Re-run after upgrading the tools.

```bash
mkdir -p ~/.zsh/completions

# ALL tools which we need to have completions.
# one exceptoin: `direnv` must run at startup
uv generate-shell-completion zsh  > ~/.zsh/completions/_uv
uvx --generate-shell-completion zsh > ~/.zsh/completions/_uvx
gh completion -s zsh              > ~/.zsh/completions/_gh
rustup completions zsh            > ~/.zsh/completions/_rustup
kubectl completion zsh            > ~/.zsh/completions/_kubectl
cp ~/.bun/_bun                      ~/.zsh/completions/_bun 2>/dev/null

rm -f ~/.zcompdump*   # force one rebuild so the new files register
```

In `~/.zshrc`, before `compinit`:
```zsh
fpath=(~/.zsh/completions $fpath)
```

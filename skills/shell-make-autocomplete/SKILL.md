---
name: shell-make-autocomplete
description: "Enable auto completion for Makefile targets. TIL note about shell. Use when working with shell and the user mentions make autocomplete or related topics."
---

# Enable auto completion for Makefile targets

`cat ~/.zshrc`:

```bash
# make completion
zstyle ':completion:*:*:make:*' tag-order 'targets'
autoload -Uz compinit && compinit
```

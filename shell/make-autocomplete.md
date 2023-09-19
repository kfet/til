# Enable auto completion for Makefile targets

`cat ~/.zshrc`:

```bash
# make completion
zstyle ':completion:*:*:make:*' tag-order 'targets'
autoload -Uz compinit && compinit
```

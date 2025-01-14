# Configure remote TERM settings

Fix error "missing or unsuitable terminal: xterm-ghostty"

```
infocmp -x | ssh YOUR-SERVER -- tic -x -
```

Alternatively for a quick workaround
```
export TERM=xterm-256color
```

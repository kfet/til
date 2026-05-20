---
name: ghostty-config-term
description: "Configure remote TERM settings to work with Ghostty. TIL note about ghostty. Use when working with ghostty and the user mentions config TERM or related topics."
---

# Configure remote TERM settings to work with Ghostty

Fix error "missing or unsuitable terminal: xterm-ghostty"

```bash
infocmp -x | ssh YOUR-SERVER -- tic -x -
```

Alternatively for a quick workaround
```bash
export TERM=xterm-256color
```

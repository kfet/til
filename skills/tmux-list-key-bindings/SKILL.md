---
name: tmux-list-key-bindings
description: "List tmux key bindings. TIL note about tmux. Use when working with tmux and the user mentions list key bindings or related topics."
---

# List tmux key bindings

Here's how to list all the current key-bindings of tmux.

Best used when piped to a viewer or editor like `vi` or `less` for easy search.

```
tmux list-keys
```

For quick access from withint a `tmux` session:

```
<prefix>:list-keys
```

or just

```
<prefix>?
```

---
name: tmux-conf-scroll-buffer-size
description: "Increase tmux scroll buffer size. TIL note about tmux. Use when working with tmux and the user mentions conf scroll buffer size or related topics."
---

# Increase tmux scroll buffer size

Set scroll-buffer size to 50000 lines

`$ cat ~/.tmux.conf`

```
# scroll buffer size
set-option -g history-limit 50000
```

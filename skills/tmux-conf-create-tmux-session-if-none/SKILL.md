---
name: tmux-conf-create-tmux-session-if-none
description: "Create a new tmux session only if one does not exist. TIL note about tmux. Use when working with tmux and the user mentions conf create tmux session if none or related topics."
---

# Create a new tmux session only if one does not exist

`cat ~/.tmux.conf`
```
# if run as "tmux attach", create a session if one does not already exist
new-session -n $HOST
```

## Bind function keys for window management

Add this to the tmux configuration to use F2/3/4 and alt(opt)-left/right keys

`cat ~/.tmux.conf`

```
# bind function keys for window management
bind-key -n F2 new-window
bind-key -n F3 previous-window
bind-key -n M-Left previous-window
bind-key -n F4 next-window
bind-key -n M-Right next-window
```

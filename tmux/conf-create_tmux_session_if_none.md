# Create a new tmux session only if one does not exist

`cat ~/.tmux.conf`
```
# if run as "tmux attach", create a session if one does not already exist
new-session -n $HOST
```

# Fix Shift+Enter in Ghostty + tmux

Ghostty uses the kitty keyboard protocol and sends `\e[13;2u` for Shift+Enter.
By default, tmux swallows this and sends a plain Enter to the inner application.

## Ghostty config

Make Ghostty explicitly send the CSI u sequence for Shift+Enter:

`~/.config/ghostty/config` or `~/Library/Application Support/com.mitchellh.ghostty/config`

```
keybind = shift+enter=text:\x1b[13;2u
```

## tmux config

`~/.tmux.conf`

```
# Pass through extended keys (kitty protocol) to inner applications
set -s extended-keys always
set -as terminal-features 'xterm-ghostty*:extkeys'
```

- `extended-keys always` makes tmux unconditionally forward CSI u key sequences to applications inside it. With `on` (instead of `always`), tmux only forwards them if the inner application explicitly requests them.
- The `terminal-features` line tells tmux the outer Ghostty terminal supports extended keys.

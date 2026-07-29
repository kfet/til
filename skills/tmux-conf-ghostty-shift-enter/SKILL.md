---
name: tmux-conf-ghostty-shift-enter
description: "Fix Shift+Enter in Ghostty + tmux. TIL note about tmux. Use when working with tmux and the user mentions conf ghostty shift enter or related topics."
---

# Fix Shift+Enter in Ghostty + tmux

Ghostty uses the kitty keyboard protocol and sends `\e[13;2u` for Shift+Enter.
By default, tmux swallows this and sends a plain Enter to the inner application.

For the Ghostty side, see: `ghostty/config-shift_enter.md`.

## tmux config

`~/.tmux.conf`

```tmux
# Pass through extended keys (kitty protocol) to inner applications
set -s extended-keys always
set -as terminal-features 'xterm-ghostty*:extkeys'
```

- `extended-keys always` makes tmux unconditionally forward CSI u key sequences to applications inside it. With `on` (instead of `always`), tmux only forwards them if the inner application explicitly requests them.
- The `terminal-features` line tells tmux the outer Ghostty terminal supports extended keys.

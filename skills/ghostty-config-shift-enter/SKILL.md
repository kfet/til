---
name: ghostty-config-shift-enter
description: "Configure Ghostty Shift+Enter for tmux. TIL note about ghostty. Use when working with ghostty and the user mentions config shift enter or related topics."
---

# Configure Ghostty Shift+Enter for tmux

Ghostty uses the kitty keyboard protocol and can send `\e[13;2u` for Shift+Enter.

`~/.config/ghostty/config` or `~/Library/Application Support/com.mitchellh.ghostty/config`

```
keybind = shift+enter=text:\x1b[13;2u
keybind = shift+space=text:\x20
```

---
name: ai-pi-coding-agent
description: "Install the Pi coding agent. TIL note about ai. Use when working with ai and the user mentions pi coding agent or related topics."
---

# Install the Pi coding agent

Install
```bash
bun install -g @mariozechner/pi-coding-agent
```

Configure Ghostty key bindings (in Ghostty press cmd+,)
```
## Add to ghostty config
keybind = alt+backspace=text:\x1b\x7f
keybind = shift+enter=text:\n
```

More details on the project found here:
* https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent

For installing `Bun` see:
* `../nodejs/bun.md`

---
name: shell-llm
description: "Install the LLM CLI tool. TIL note about shell. Use when working with shell and the user mentions llm or related topics."
---

# Install the LLM CLI tool

Detailed guildes [here](https://llm.datasette.io)

Using pipx:
```bash
pipx install llm
```

Additionally, to setup and use as default Claude-3.5-Haiku, have ready an Anthropic API key.
```bash
llm install llm-claude-3
llm keys set claude
llm models default claude-3.5-haiku
```

---
name: shell-ripgrep
description: "Installing and Using Ripgrep on macOS. TIL note about shell. Use when working with shell and the user mentions ripgrep or related topics."
---

# Installing and Using Ripgrep on macOS

## Installation

```bash
brew install ripgrep
```

## Basic Usage

Search for pattern in current directory:
```bash
rg "pattern"
```

Search in specific file or directory:
```bash
rg "pattern" path/to/file
rg "pattern" path/to/directory
```

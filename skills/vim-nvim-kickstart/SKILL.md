---
name: vim-nvim-kickstart
description: "Nvim Kickstart. TIL note about vim. Use when working with vim and the user mentions nvim kickstart or related topics."
---

# NeoVim kickstart

Quickly setup a new NeoVim installation.

Follow the instructions on the [kickstart.nvim](https://github.com/nvim-lua/kickstart.nvim) page.

As of 2/22/2024 for Linux/Mac it boils down to the following.

Get the script in the `.config/nvim` directory (after backup of any previous config)
```bash
git clone https://github.com/nvim-lua/kickstart.nvim.git "${XDG_CONFIG_HOME:-$HOME/.config}"/nvim
```

Start NeoVim
```bash
nvim
```

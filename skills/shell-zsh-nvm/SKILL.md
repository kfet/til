---
name: shell-zsh-nvm
description: "Install and maintain nvm using the oh-my-zsh zsh-nvm plugin. TIL note about shell. Use when working with shell and the user mentions zsh nvm or related topics."
---

# Install and maintain nvm using the oh-my-zsh zsh-nvm plugin

Clone zsh-nvm
```
git clone https://github.com/lukechilds/zsh-nvm ~/.oh-my-zsh/custom/plugins/zsh-nvm
```

Add `zsh-nvm` to the plugins list

`cat ~/.zshrc`:
```
plugins=(git zsh-nvm)
```

Restart zsh

Refs: [Install Nvm as a Oh-My-Zsh Plugin](https://blog.rylander.io/2017/11/13/install-nvm-as-a-oh-my-zsh-plugin/)

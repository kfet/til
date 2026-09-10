---
name: shell-ohmyzsh-install
description: "Install Oh My Zsh, and why you might not want to. TIL note about shell. Use when working with shell and the user mentions ohmyzsh install or related topics. See also shell-zsh-startup-profiling before adopting it."
---

# Install Oh My Zsh

https://ohmyz.sh

```bash
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

Note the installer **changes your login shell to zsh**. That part is usually
what you actually wanted; oh-my-zsh itself is a separate question.

## Before you adopt it

See `shell-zsh-startup-profiling`. Measured findings that are easy to get
wrong by assumption:

- It ships **no git completion**. `_git` comes with zsh itself, at
  `/usr/share/zsh/functions/Completion/Unix/_git`. The git plugin is aliases
  and helper functions only.
- It ships **no autosuggestions or syntax highlighting** — the two additions
  most people actually want. Those are separate repos you can `source`
  directly in four lines, no framework required.
- It runs `compinit` **unconditionally and uncached**, and re-autoloads the
  function itself, so you cannot make it use `compinit -C`. On slow storage
  that alone is most of your startup time.
- Sourcing its ~23 lib and plugin files costs real time on SD-card or
  spinning-disk machines (hundreds of ms); on an SSD it is negligible.

Audit before committing to it, or before ripping it out:

```bash
# what you actually type, vs what the framework defines
sed 's/^: [0-9]*:[0-9]*;//' ~/.zsh_history | awk '{print $1}' \
  | sort | uniq -c | sort -rn | head -40
```

It is common to find a double-digit number of aliases in real use out of the
229 it defines.

## If you do install it

Apply at least these two fixes from `shell-zsh-startup-profiling` — they are
independent of the framework and can be worth over a second on a Raspberry Pi:

```bash
# 1. Debian/Ubuntu/Raspbian run their own compinit in /etc/zsh/zshrc,
#    before your .zshrc — so it happens twice.
echo 'skip_global_compinit=1' >> ~/.zshenv

# 2. skip compaudit's recursive scan (set before oh-my-zsh.sh is sourced)
#    ZSH_DISABLE_COMPFIX=true
```

And never put `eval "$(tool completion zsh)"` in your rc — cache those to
files under `~/.zsh/completions` instead.

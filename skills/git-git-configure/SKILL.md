---
name: git-git-configure
description: "Git configure defaults. TIL note about git. Use when working with git and the user mentions git configure or related topics."
---

# Git configure defaults

Specify `--rebase` by default when doing `git pull`

```bash
git config --global pull.rebase true
```

Useful aliases `co` -> `checkout`, `cl` -> `clone`

```bash
git config --global alias.co checkout
git config --global alias.cl clone
git config --global alias.wt worktree
```

Set pager to `bat`, if you have it installed

```bash
git config --global core.pager bat
```

Enable [`rerere`](https://git-scm.com/book/en/v2/Git-Tools-Rerere)

```bash
git config --global rerere.enabled true
```

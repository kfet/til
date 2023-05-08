## Git configure defaults

Specify `--rebase` by default when doing `git pull`

```
git config --global pull.rebase true
```

Useful aliases `co` -> `checkout`, `cl` -> `clone`

```
git config --global alias.co checkout
git config --global alias.cl clone
git config --global alias.wt worktree
```

Set pager to `bat`, if you have it installed
```
git config --global core.pager bat
```

---
name: shell-dust
description: "Install dust, a more intuitive du. TIL note about shell. Use when working with shell and the user mentions dust, disk usage or related topics."
---

# Install dust

## Summary

dust is a faster, more intuitive `du`: it shows which directories use the most disk space as a tree with bars.

More details on the [github repo](https://github.com/bootandy/dust)

## Details

Install dust
```bash
curl -sSfL https://raw.githubusercontent.com/bootandy/dust/refs/heads/master/install.sh | sh
```

Show disk usage of the current directory
```bash
dust
```

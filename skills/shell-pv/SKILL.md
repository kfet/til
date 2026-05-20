---
name: shell-pv
description: "Install and use pipe-viewer (pv). TIL note about shell. Use when working with shell and the user mentions pv or related topics."
---

# Install and use pipe-viewer (pv)

Use in place of `cat`, `cp` to show progress when operating on large files

```bash
brew install pv
```

```bash
cat /dev/urandom | pv --size 100M > /dev/null
```

```bash
pv /path/to/large-file > /path/to/destination
```

Ref: [ivarch.com: Pipe Viewer](http://www.ivarch.com/programs/pv.shtml)

See Also: similr [pv in node.js](https://github.com/roccomuso/pv)

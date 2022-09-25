# Install and use pipe-viewer (pv)

Use in place of `cat`, `cp` to who progress, when operating on large files

```
brew install pv
```

```
cat /dev/urandom | pv --size 100M > /dev/null
```

Ref: [ivarch.com: Pipe Viewer](http://www.ivarch.com/programs/pv.shtml)

See Also: similr [pv in node.js](https://github.com/roccomuso/pv)

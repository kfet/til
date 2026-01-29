# Install Bun as a Node.js-free JS/TS runtime

## Summary

Install [Bun](https://bun.com/docs/installation) as a standalone JS/TS runtime that requires no Node.js installation. Since Bun is a drop-in replacement for Node.js, a simple symlink is all that's needed.

## Install Bun

```bash
curl -fsSL https://bun.com/install | bash
```

NOTE: requires `unzip`

## Running globally installed packages without Node.js

Bun is a drop-in replacement for Node.js. If a globally installed package shim tries to invoke `node`, just symlink `bun` as `node`:

```bash
ln -sf ~/.bun/bin/bun ~/.bun/bin/node
```

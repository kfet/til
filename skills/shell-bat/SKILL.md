---
name: shell-bat
description: "Use bat instead of cat. TIL note about shell. Use when working with shell and the user mentions bat or related topics."
---

# Use bat instead of cat

Use the [bat](https://github.com/sharkdp/bat) tool as a drop-in replacement of `cat`.

Installation:
https://github.com/sharkdp/bat#installation

* macOs: `brew install bat`
* ubuntu: `apt install bat`
* AL2: Install binary from the [bat releases page](https://github.com/sharkdp/bat/releases):
```bash
wget https://github.com/sharkdp/bat/releases/download/v0.20.0/bat-v0.20.0-i686-unknown-linux-musl.tar.gz
tar xvf bat-v0.20.0-i686-unknown-linux-musl.tar.gz
cp bat-v0.20.0-i686-unknown-linux-musl/bat ~/bin && chmod a+x ~/bin/bat
```

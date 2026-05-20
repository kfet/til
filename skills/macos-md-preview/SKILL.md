---
name: macos-md-preview
description: "Enable MD quicklook preview. TIL note about macos. Use when working with macos and the user mentions md preview or related topics."
---

# Enable MD quicklook preview


Install [QLMarkdown](https://github.com/sbarex/QLMarkdown)
```bash
brew install --cask qlmarkdown
```

Enable running QLMarkdown
```bash
xattr -r -d com.apple.quarantine "/Applications/QLMarkdown.app"
```

Open the QLMarkdown app and adjust settings to liking

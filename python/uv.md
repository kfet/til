# Install uv/uvx

[uv](https://docs.astral.sh/uv/) An extremely fast Python package and project manager, written in Rust.

Detailed installation instructions can be found here: [installation](https://docs.astral.sh/uv/getting-started/installation/)

install:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

or using brew:
```bash
brew install uv
```

enable shell auto-completion (zsh):
```bash
echo 'eval "$(uv generate-shell-completion zsh)"' >> ~/.zshrc
echo 'eval "$(uvx --generate-shell-completion zsh)"' >> ~/.zshrc
source ~/.zshrc
```

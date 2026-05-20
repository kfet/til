# Shell completion for `til`

Lightweight, dependency-free completion scripts that delegate to the CLI's
hidden `til _complete` helper. The helper enumerates current subcommands,
skill slugs, and executable section names, so the completion stays correct
when the CLI grows new commands or the repository changes.

## Bash

```bash
# one-shot for this shell
source /path/to/til/completions/til.bash

# persistent (bash-completion v2)
mkdir -p ~/.local/share/bash-completion/completions
ln -sf /path/to/til/completions/til.bash \
       ~/.local/share/bash-completion/completions/til
```

## Zsh

```zsh
# add the completion dir to fpath in ~/.zshrc, before `compinit`:
fpath=(/path/to/til/completions $fpath)
autoload -Uz compinit && compinit

# or symlink into an existing completions directory
ln -sf /path/to/til/completions/_til ~/.zsh/completions/_til
```

## What gets completed

| Position                  | Completed candidates              |
|---------------------------|-----------------------------------|
| first arg                 | subcommands                       |
| `til --repo-path …`       | directory                         |
| `til show <TAB>`          | skill slugs                       |
| `til validate <TAB>`      | skill slugs                       |
| `til execute <TAB>`       | skill slugs                       |
| `til execute slug <TAB>`  | executable section names for slug |
| `til config <TAB>`        | directory                         |

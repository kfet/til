# TIL

kfet's "Today I Learned" (TIL) repository

TIL entries are little nuggets of knowledge, which at some point in time I considered interesting enough to keep around.

Entries are packaged as [Agent Skills](https://agentskills.io/specification) under `skills/{topic}-{name}/SKILL.md`. Each skill is a plain Markdown file with a small YAML frontmatter (`name`, `description`) so it can be consumed by skill-aware agents as well as read directly.

## Install

### Homebrew (macOS, Linux)

```bash
brew install kfet/til/til
```

The Homebrew formula installs a bundled snapshot of the `skills/` tree and sets
`til` to read from that snapshot by default. Update it with:

```bash
brew update
brew upgrade til
```

### Install script

From a local clone:

```bash
./install.sh
```

Or directly from GitHub:

```bash
curl -sSL https://raw.githubusercontent.com/kfet/til/main/install.sh | bash
```

The installer prompts to drop bash/zsh completion under the right
`fpath` / `bash-completion` directory; pass `--completion=yes` or
`--completion=no` to skip the prompt.

## CLI overview

Once installed:

```bash
til list                # list every skill
til search <term>       # full-text search
til show <slug>         # render a skill (uses glow/bat when stdout is a TTY)
til show --plain <slug> # raw markdown (also when NO_COLOR is set or piped)
til execute <slug> <section>   # run code blocks from a `(executable)` section
til validate            # check every skill against the Agent Skill spec
til update              # git pull the skills repo
```

`til show` auto-picks a renderer in this order: whatever `TIL_RENDERER`
is set to, then `glow`, then `bat`. With none installed it just prints
plain text.

## Release

Push a `vX.Y.Z` tag to create a GitHub release and render `Formula/til.rb` into
the `kfet/homebrew-til` tap. The release workflow needs a `HOMEBREW_TAP_TOKEN`
secret with write access to that tap.

## License

MIT — see [LICENSE](LICENSE).

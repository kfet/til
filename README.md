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

It also offers to install [airan](https://github.com/kfet/airan), which
only `til run` needs — pass `--airan=yes` or `--airan=no` to skip that
prompt. Everything else works without it.

### Uninstall

```bash
~/.til-repo/install.sh --uninstall            # CLI, completions, config, repo
~/.til-repo/install.sh --uninstall --keep-repo   # keep the skills clone
```

Add `--yes` to skip the confirmation. A Homebrew-installed `til` is
detected and refused — remove that one with `brew uninstall til`.

## CLI overview

Once installed:

```bash
til list                # list every skill
til search <term>       # full-text search
til show <slug>         # render a skill (uses glow/bat when stdout is a TTY)
til show --plain <slug> # raw markdown (also when NO_COLOR is set or piped)
til path <slug>         # print the absolute path to that skill's SKILL.md
til execute <slug> <section>   # mechanically run a `(executable)` section's shell blocks
til run <slug>          # hand the whole skill to an AI agent to apply it here
til validate            # check every skill against the Agent Skill spec
til update              # pull the skills repo AND refresh the til CLI
til update --no-cli     # skills only, leave the installed CLI alone
til update --cli        # force the CLI reinstall even if it looks current
```

`til execute` and `til run` are deliberately different: `execute` is
mechanical (run these shell blocks, with a confirmation prompt), `run` is
agentic (wrap the skill in an "apply this to the current host, verify,
report what changed" instruction and dispatch it to an AI coding agent
via [airan](https://github.com/kfet/airan)). `run` pins no backend, so
airan resolves `$AIRAN_BACKEND` then its configured default.

`til show` auto-picks a renderer in this order: whatever `TIL_RENDERER`
is set to, then `bat`, then `glow`. With none installed it just prints
plain text.

## Release

Push a `vX.Y.Z` tag to create a GitHub release and render `Formula/til.rb` into
the `kfet/homebrew-til` tap. The release workflow needs a `HOMEBREW_TAP_TOKEN`
secret with write access to that tap.

## License

MIT — see [LICENSE](LICENSE).

---
name: shell-zsh-measure-startup
description: "Measure and profile zsh startup time. TIL note about shell. Use when a shell feels slow to open, or the user mentions zprof, profiling zsh, or slow startup."
---

# Measure and profile zsh startup

Median of 5, portable (macOS has no `/usr/bin/time -f`):

```zsh
zsh -c 'zmodload zsh/datetime
for i in {1..5}; do s=$EPOCHREALTIME; zsh -i -c exit >/dev/null 2>&1; e=$EPOCHREALTIME
  t+=( $(( (e-s)*1000 )) ); done
t=( ${(on)t} ); printf "%.0fms median\n" $t[3]'
```

To profile, make `zmodload zsh/zprof` the first line of `~/.zshrc` and `zprof`
the last.

Three traps that produce numbers that are simply wrong:

- **Profiling in a scratch `ZDOTDIR` with no zcompdump** forces a full
  completion rebuild, inventing a bottleneck that never occurs in real use.
- **A leaked `ZDOTDIR` export** makes "before" and "after" measure the same
  config. Wrap comparisons in `env -u ZDOTDIR`.
- **Machine load.** Check `/proc/loadavg` and let it settle; a busy
  single-core box can read 2x its idle time.

`zprof` counts only functions — if the total far exceeds the profile, the rest
is fork/exec and parsing.

Always assert correctness beside timing. A change that "speeds up" the shell
by silently breaking completions looks like a win in a benchmark:

```bash
zsh -i -c 'echo "aliases=$(alias|wc -l) git=${_comps[git]:-MISSING}"'
zsh -i -c exit 2>&1 | head        # must be empty
```

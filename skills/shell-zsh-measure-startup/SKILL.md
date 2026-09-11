---
name: shell-zsh-measure-startup
description: "Measure and profile zsh startup time."
---

Median of 5, portable (macOS has no `/usr/bin/time -f`):

```zsh
zsh -c 'zmodload zsh/datetime
for i in {1..5}; do s=$EPOCHREALTIME; zsh -i -c exit >/dev/null 2>&1; e=$EPOCHREALTIME
  t+=( $(( (e-s)*1000 )) ); done
t=( ${(on)t} ); printf "%.0fms median\n" $t[3]'
```

To profile, make `zmodload zsh/zprof` the first line of `~/.zshrc` and `zprof` the last.

NOTE: beware of wrong measurements:
- In a scratch `ZDOTDIR` with no zcompdump forces a full completion rebuild
- Leaked `ZDOTDIR` export makes "before" and "after" measure the same config. Wrap comparisons in `env -u ZDOTDIR`.
- Machine load. Check `/proc/loadavg` (Linux) or `sysctl -n vm.loadavg` (macOs) and let it settle

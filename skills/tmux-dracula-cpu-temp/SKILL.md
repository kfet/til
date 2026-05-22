---
name: tmux-dracula-cpu-temp
description: "Show CPU temperature in the tmux status bar via the Dracula theme, with dynamic color based on the value (cold/normal/warm/hot), in an update-safe way. macOS (Apple Silicon) version using smctemp. Use when working with tmux, dracula/tmux, or the user mentions adding a CPU temp segment to the tmux status line on a Mac."
---

# Show Mac CPU temp in the tmux status bar (Dracula, colored, update-safe)

The `dracula/tmux` theme ships widgets for `cpu-usage` and `ram-usage`
but **not** CPU temperature. Patching `dracula.sh` works but TPM
updates (`prefix + U`) will clobber the edit.

The update-safe pattern: keep dracula stock and **append** an extra
segment to `status-right` in your own `.tmux.conf`, *after* the
`run '~/.tmux/plugins/tpm/tpm'` line. `run-shell` is synchronous, so
by the time tpm returns, dracula has already populated `status-right`
and a trailing `set -ag status-right "..."` sticks.

The script emits its **own** `#[fg=...,bg=...]` directive so the
background color changes with the temperature.

## 1. Install smctemp

On Apple Silicon, `osx-cpu-temp` and `istats` don't work.
Use [`smctemp`](https://github.com/narugit/smctemp) — a lightweight
CLI that reads CPU temperature directly from the SMC:

```bash
brew tap narugit/tap
brew install narugit/tap/smctemp
```

`smctemp -c` prints just the CPU temp as a number (e.g. `52.3`).

### Why smctemp instead of macmon?

We originally used [`macmon`](https://github.com/vladkens/macmon), but
it polls Apple's IOReport framework at a 200ms interval
(`macmon pipe -s 1 -i 200`), which causes **~35% CPU usage** — far too
heavy for a status-bar widget that refreshes every 5 seconds.

`smctemp -c` does a single direct SMC register read and exits
immediately, with negligible CPU overhead.

## 2. Wrapper script

`~/.tmux/scripts/cpu_temp.sh`:

```bash
#!/usr/bin/env bash
# Print colored CPU temp segment for tmux status bar (macOS, Apple Silicon).
# Uses smctemp (lightweight SMC reader) instead of macmon.
set -eu

NA='#[fg=#282a36,bg=#6272a4] |🌡 n/a '

if ! command -v smctemp >/dev/null 2>&1; then
  printf '%s' "$NA"; exit 0
fi

raw=$(smctemp -c 2>/dev/null)

if [ -z "${raw:-}" ]; then
  printf '%s' "$NA"; exit 0
fi

t=$(printf '%.0f' "$raw")

# Mac CPUs run hotter than SBCs — bands shifted up.
if   [ "$t" -lt 60 ]; then bg='#8be9fd'   # cyan   — cold
elif [ "$t" -lt 80 ]; then bg='#50fa7b'   # green  — normal
elif [ "$t" -lt 95 ]; then bg='#ffb86c'   # orange — warm
else                       bg='#ff5555'   # red    — hot
fi

printf '#[fg=#282a36,bg=%s] |🌡 %s°C ' "$bg" "$t"
```

```bash
chmod +x ~/.tmux/scripts/cpu_temp.sh
```

## 3. Wire it into `~/.tmux.conf`

At the very bottom, **after** the tpm `run` line:

```tmux
# Initialize TMUX plugin manager (keep this line at the very bottom of tmux.conf)
run '~/.tmux/plugins/tpm/tpm'

# Append CPU temp segment to status-right (after dracula has set it).
# Script emits its own color based on temp value. Survives TPM updates.
set -ag status-right "#(~/.tmux/scripts/cpu_temp.sh)"
```

Reload:

```bash
tmux source-file ~/.tmux.conf
```

The dracula refresh rate (`@dracula-refresh-rate`, default 5s) drives
how often the temp updates.

## Why not patch `dracula.sh`?

Editing `~/.tmux/plugins/tmux/scripts/dracula.sh` to add a `cpu-temp`
case works, but TPM's update step runs `git pull` in the plugin
checkout, so local edits create merge conflicts or get lost. Keeping
the segment in your own `.tmux.conf` plus a script under
`~/.tmux/scripts/` puts the customisation entirely in files TPM never
touches.

## Tip: how tmux interprets `#[...]` from `#(...)` output

tmux re-evaluates the stdout of `#(command)` as a format string by
default, so `#[fg=...,bg=...]` directives emitted by the script are
honoured. That's what lets the script set its own background color
dynamically.

## Related

See `linux-tmux-dracula-cpu-temp` for the Linux SBC variant (Raspberry
Pi, Orange Pi) which reads `/sys/class/thermal/thermal_zone0/temp`
instead of using macmon.

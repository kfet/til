---
name: tmux-dracula-cpu-temp
description: "Show Apple Silicon CPU temperature in the tmux status bar via the Dracula theme, in an update-safe way. Use when working with tmux, dracula/tmux, or the user mentions adding CPU temp / hardware sensors to the tmux status line on macOS."
---

# Show Mac CPU temp in the tmux status bar (Dracula, update-safe)

The `dracula/tmux` theme ships widgets for `cpu-usage` and `ram-usage`
but **not** CPU temperature. Patching `dracula.sh` to add a `cpu-temp`
plugin case works, but TPM updates (`prefix + U`) will clobber the
edit.

The update-safe pattern: keep dracula stock and **append** an extra
segment to `status-right` in your own `.tmux.conf`, *after* the
`run '~/.tmux/plugins/tpm/tpm'` line. `run-shell` is synchronous, so
by the time tpm returns, dracula has already populated `status-right`
and a trailing `set -ag status-right "..."` sticks.

## 1. Install a sudoless temp source

On Apple Silicon, `osx-cpu-temp` and `istats` don't work. Use
[`macmon`](https://github.com/vladkens/macmon) — sudoless, brew-installable:

```bash
brew install macmon
```

Quick test (single sample, JSON):

```bash
macmon pipe -s 1 -i 200
```

The CPU temp lives at `temp.cpu_temp_avg`.

## 2. Wrapper script

`~/.tmux/scripts/cpu_temp.sh`:

```bash
#!/usr/bin/env bash
# Print Mac (Apple Silicon) CPU temperature for tmux status bar.
set -eu

if ! command -v macmon >/dev/null 2>&1; then
  echo "n/a"; exit 0
fi

temp=$(macmon pipe -s 1 -i 200 2>/dev/null \
  | sed -n 's/.*"cpu_temp_avg":\([0-9.]*\).*/\1/p' \
  | head -1)

[ -z "${temp:-}" ] && { echo "n/a"; exit 0; }
printf '%.0f°C\n' "$temp"
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
# Survives TPM updates: dracula's own files are untouched.
# Colors match dracula: bg=red (#ff5555), fg=dark_gray (#282a36).
set -ag status-right "#[fg=#282a36,bg=#ff5555] |🌡 #(~/.tmux/scripts/cpu_temp.sh) "
```

Reload:

```bash
tmux source-file ~/.tmux.conf
```

The dracula refresh rate (`@dracula-refresh-rate`, default 5s) drives
how often the temp updates.

## Why not patch `dracula.sh`?

Editing `~/.tmux/plugins/tmux/scripts/dracula.sh` to add a `cpu-temp`
case works (you can model it on the `cpu-usage` case and gate colors
behind `@dracula-cpu-temp-colors`), but TPM's update step runs
`git pull` in the plugin checkout, so any local edits create merge
conflicts or get lost. Keeping the segment in your own `.tmux.conf`
plus a script under `~/.tmux/scripts/` keeps the customisation entirely
in files TPM never touches.

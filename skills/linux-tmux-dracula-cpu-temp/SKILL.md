---
name: linux-tmux-dracula-cpu-temp
description: "Show CPU temperature in the tmux status bar via the Dracula theme, with dynamic color based on the value, on Linux SBCs (Raspberry Pi, Orange Pi, generic Linux). Update-safe — uses /sys/class/thermal/thermal_zone0/temp and does not patch the dracula plugin. Use when working with tmux on a Pi / Orange Pi / Linux box and the user mentions adding a CPU temp segment to the tmux status line."
---

# Show Linux SBC CPU temp in the tmux status bar (Dracula, colored, update-safe)

Companion to the macOS version (`tmux-dracula-cpu-temp`). The
mechanism is the same — append a `status-right` segment after the
tpm `run` line so dracula stays untouched — but the temp source is
the kernel sysfs thermal zone, which exists on every modern Linux
SBC and most generic Linux servers (KVM guests usually don't expose
it).

Tested on:
- Raspberry Pi Zero W (armv6, BCM2835)
- Raspberry Pi Zero 2 W (aarch64, BCM2710A1)
- Orange Pi Zero 2 W (aarch64, Allwinner H618)

## 1. Verify the thermal zone

```bash
cat /sys/class/thermal/thermal_zone0/temp
# e.g. 49388  (millidegrees Celsius → 49.4°C)
```

If this is missing, the box doesn't expose CPU temperature (typical
for cloud KVM guests like Oracle Cloud, RackNerd, etc.). On RPi you
can also use `vcgencmd measure_temp`, but the sysfs path is
universal.

## 2. Wrapper script

`~/.tmux/scripts/cpu_temp.sh` (POSIX `sh`, no bashisms — works on
busybox / dash too):

```bash
#!/bin/sh
# Print colored CPU temp segment for tmux status bar (Linux sysfs).
# Dracula palette: dark_gray=#282a36, cyan=#8be9fd, green=#50fa7b,
#                  orange=#ffb86c, red=#ff5555, comment=#6272a4.

f=/sys/class/thermal/thermal_zone0/temp
if [ ! -r "$f" ]; then
  printf '#[fg=#282a36,bg=#6272a4] |🌡 n/a '
  exit 0
fi

t=$(awk '{printf "%.0f", $1/1000}' "$f")

if   [ "$t" -lt 50 ]; then bg='#8be9fd'   # cyan   — cold
elif [ "$t" -lt 65 ]; then bg='#50fa7b'   # green  — normal
elif [ "$t" -lt 75 ]; then bg='#ffb86c'   # orange — warm
else                       bg='#ff5555'   # red    — hot
fi

printf '#[fg=#282a36,bg=%s] |🌡 %s°C ' "$bg" "$t"
```

```bash
chmod +x ~/.tmux/scripts/cpu_temp.sh
```

Bands chosen for passively-cooled SBCs:
- `<50°C` cold (cyan)
- `50–64°C` normal (green)
- `65–74°C` warm (orange)
- `≥75°C` hot (red) — RPi soft-throttles at 80°C, so 75 is a sane warning band.

## 3. Wire it into `~/.tmux.conf`

At the very bottom, after the tpm `run` line:

```tmux
run '~/.tmux/plugins/tpm/tpm'

# Append CPU temp segment to status-right (after dracula has set it).
# Script emits its own color based on temp value. Survives TPM updates.
set -ag status-right "#(~/.tmux/scripts/cpu_temp.sh)"
```

## 4. Reload (and clean up duplicates if needed)

```bash
tmux source-file ~/.tmux.conf
```

### Gotcha: duplicated segments after deploy

If `b0o/tmux-autoreload` is enabled (very common in dracula setups)
it will detect the conf edit and re-source in parallel with your
manual `source-file`. Both runs race past dracula's
`set -g status-right ""` reset, leaving you with 2× or 3× of each
segment. Fix:

```bash
tmux set -g status-right ""
tmux source-file ~/.tmux.conf
```

Verify only one of each appears:

```bash
tmux show -gv status-right | grep -oE 'cpu_info|ram_info|cpu_temp' | sort | uniq -c
# expect:
#   1 cpu_info
#   1 cpu_temp
#   1 ram_info
```

## Fleet deploy via Tailscale

For a fleet of SBCs reachable via Tailscale SSH, this idempotent
snippet works on each host (run inside an `ssh "$host" "$DEPLOY"` for
each box). The `cpu_temp.sh` body is the script from §2 — embed it
inline or scp it over.

```bash
mkdir -p ~/.tmux/scripts
cat > ~/.tmux/scripts/cpu_temp.sh <<'EOF'
# … script from §2 …
EOF
chmod +x ~/.tmux/scripts/cpu_temp.sh

if grep -q 'cpu_temp.sh' ~/.tmux.conf; then
  sed -i 's|^set -ag status-right.*cpu_temp\.sh.*|set -ag status-right "#(~/.tmux/scripts/cpu_temp.sh)"|' ~/.tmux.conf
else
  printf '\nset -ag status-right "#(~/.tmux/scripts/cpu_temp.sh)"\n' >> ~/.tmux.conf
fi

if tmux ls >/dev/null 2>&1; then
  tmux set -g status-right ""
  tmux source-file ~/.tmux.conf
fi
```

## Related

See `tmux-dracula-cpu-temp` for the macOS / Apple Silicon variant
(uses `macmon` instead of sysfs, with higher temp bands).

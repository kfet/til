---
name: linux-tmux-dracula-cpu-temp
description: "Show CPU temperature in the tmux status bar via the Dracula theme, with dynamic color based on the value, on Linux (desktops, servers, SBCs). Update-safe — uses /sys/class/thermal/ sysfs and does not patch the dracula plugin. Use when working with tmux on any Linux box and the user mentions adding a CPU temp segment to the tmux status line."
---

# Show Linux CPU temp in the tmux status bar (Dracula, colored, update-safe)

Companion to the macOS version (`tmux-dracula-cpu-temp`). The
mechanism is the same — append a `status-right` segment after the
tpm `run` line so dracula stays untouched — but the temp source is
the kernel sysfs thermal zone, which exists on most Linux systems
(desktops, servers, and SBCs alike). KVM guests usually don't
expose it.

Tested on:
- Raspberry Pi Zero W (armv6, BCM2835)
- Raspberry Pi Zero 2 W (aarch64, BCM2710A1)
- Orange Pi Zero 2 W (aarch64, Allwinner H618)

## 1. Find the right thermal zone

The mapping of `thermal_zone0`, `thermal_zone1`, etc. is **not stable
or standardized** across systems. On one machine `thermal_zone0` might
be the CPU package; on another it could be the ACPI chassis sensor,
the WiFi card, or a battery sensor. Don't assume `thermal_zone0` is
always the CPU.

To find what each zone represents, check its `type`:

```bash
for z in /sys/class/thermal/thermal_zone*; do
    echo "$z: $(cat $z/type) = $(cat $z/temp)"
done
```

The temperature value is in millidegrees Celsius (e.g. `45000` =
45.0°C).

Look for a type like `x86_pkg_temp`, `cpu-thermal`, `acpitz`, or
similar — that's the one to use. The script below defaults to
`thermal_zone0`; adjust the path if your CPU is on a different zone.

If no thermal zone exists at all, the box doesn't expose CPU
temperature (typical for cloud KVM guests like Oracle Cloud,
RackNerd, etc.). On RPi you can also use `vcgencmd measure_temp`,
but the sysfs path is universal.

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
  printf '#[fg=#282a36,bg=#6272a4] |🌡n/a'
  exit 0
fi

t=$(awk '{printf "%.0f", $1/1000}' "$f")

if   [ "$t" -lt 50 ]; then bg='#8be9fd'   # cyan   — cold
elif [ "$t" -lt 65 ]; then bg='#50fa7b'   # green  — normal
elif [ "$t" -lt 75 ]; then bg='#ffb86c'   # orange — warm
else                       bg='#ff5555'   # red    — hot
fi

printf '#[fg=#282a36,bg=%s] |🌡%s°C' "$bg" "$t"
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

## Gotcha: emoji width on narrow terminals (phone SSH)

The `🌡` (and the dracula `💻` left-icon) are **emoji** whose rendered
width disagrees between tmux and many terminals:

- **tmux** measures the segment with its own `wcwidth` and counts each
  emoji as **1 cell**.
- Lots of terminals -- notably mobile SSH clients (Termius, Blink) --
  render emoji as **2 cells**.

On a wide screen nobody notices. On a narrow one (a ~40-column phone
SSH session) it bites: tmux computes the status as *fitting* in 40
columns and draws the whole line without truncating, but the terminal
paints it 1-2 cells wider than tmux thought. The overflow spills past
the last column and, because the status row has autowrap, **every
5-second status redraw scrolls the screen by a line**.

The cheap, robust fix is to make the segment narrow enough that even at
2-cells-per-emoji it stays under the screen width: **drop the spare
spaces** around the value. This skill's script uses the tight form
` |🌡%s°C` (no space after the emoji, no trailing space)
instead of the looser ` |🌡 %s°C ` which is 2 cells wider.
Each space removed shaves one cell off *both* the tmux-perceived and
the terminal-rendered width, so trimming two spaces buys a safe margin.

Verify on the actual narrow terminal: with the status drawn, the bottom
row should sit fully within the screen, no glyph clipped at the right
edge and no per-redraw scroll. Don't trust tmux's own width math here --
it's the *terminal's* emoji rendering that decides whether it fits.

## Related

See `tmux-dracula-cpu-temp` for the macOS / Apple Silicon variant
(uses `smctemp` instead of sysfs, with higher temp bands).

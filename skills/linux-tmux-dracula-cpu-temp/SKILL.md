#!/usr/bin/env airan
---
name: linux-tmux-dracula-cpu-temp
description: "Show CPU temperature in the tmux status bar via the Dracula theme, with dynamic color based on the value, on Linux (desktops, servers, SBCs, Intel Macs). Update-safe — reads /sys/class/thermal/ with a /sys/class/hwmon/ fallback (coretemp/k10temp) and does not patch the dracula plugin. Use when working with tmux on any Linux box and the user mentions adding a CPU temp segment to the tmux status line."
---

# Show Linux CPU temp in the tmux status bar (Dracula, colored, update-safe)

Companion to the macOS version (`tmux-dracula-cpu-temp`). The
mechanism is the same — append a `status-right` segment after the
tpm `run` line so dracula stays untouched — but the temp source is
kernel sysfs: the ACPI thermal zone where it exists, otherwise a
hwmon driver. KVM guests usually expose neither.

Tested on:
- Raspberry Pi Zero W (armv6, BCM2835)
- Raspberry Pi Zero 2 W (aarch64, BCM2710A1)
- Orange Pi Zero 2 W (aarch64, Allwinner H618)
- Mac mini Mid-2010 (x86_64, Core 2 Duo) running Ubuntu 24.04 —
  **no `/sys/class/thermal/` at all**, hwmon fallback required

## 1. Find the temperature source

Two independent sysfs interfaces can expose CPU temperature, and
**you cannot assume the first one exists**:

- `/sys/class/thermal/thermal_zone*` — the ACPI/devicetree thermal
  framework. Present on SBCs and most ACPI x86 systems.
- `/sys/class/hwmon/hwmon*` — per-driver hardware monitoring
  (`coretemp` on Intel, `k10temp` on AMD, `cpu_thermal` on some SoCs).

### Apple hardware has no thermal zones

Intel Macs running Linux expose temperature **only** through hwmon
(`coretemp` for the CPU, `applesmc` for the SMC's board/fan sensors) —
`/sys/class/thermal/` is entirely absent. A thermal-zone-only script
silently prints `n/a` forever on these boxes. Load the modules and
make them persist:

```bash
sudo modprobe coretemp
sudo modprobe applesmc          # Apple hardware only: fans + board sensors
printf 'coretemp\napplesmc\n' | sudo tee /etc/modules-load.d/sensors.conf
```

### Find the right thermal zone

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

### Find the right hwmon device

If there are no thermal zones (or none of them is the CPU), enumerate
hwmon instead — each has a `name` identifying its driver:

```bash
for h in /sys/class/hwmon/hwmon*; do
    echo "$h: $(cat $h/name 2>/dev/null)"
    ls $h | grep -E 'temp[0-9]+_input'
done
```

`coretemp` (Intel), `k10temp` (AMD), `cpu_thermal` and `zenpower` are
CPU sensors; `nouveau`/`amdgpu` are the GPU and `applesmc` is board/fan
telemetry — don't use those for a CPU segment. Note `coretemp` often
starts at `temp2_input` (temp1 is the package on some CPUs, per-core on
others); any of them is close enough for a status bar.

Values from both interfaces are in millidegrees Celsius (e.g. `45000`
= 45.0°C), so the same arithmetic works for either.

If neither interface exists the box doesn't expose CPU temperature
(typical for cloud KVM guests like Oracle Cloud, RackNerd, etc.). On
RPi you can also use `vcgencmd measure_temp`, but sysfs is universal.

## 2. Wrapper script

`~/.tmux/scripts/cpu_temp.sh` (POSIX `sh`, no bashisms — works on
busybox / dash too). It tries the thermal zone first and falls back to
a CPU hwmon device, so the same script works on SBCs, ACPI x86 boxes
and Intel Macs alike:

```bash
#!/bin/sh
# Print colored CPU temp segment for tmux status bar (Linux sysfs).
# Source order: ACPI thermal_zone0 -> hwmon (coretemp/k10temp/cpu_thermal).
# Dracula palette: dark_gray=#282a36, cyan=#8be9fd, green=#50fa7b,
#                  orange=#ffb86c, red=#ff5555, comment=#6272a4.

f=""
[ -r /sys/class/thermal/thermal_zone0/temp ] && f=/sys/class/thermal/thermal_zone0/temp

if [ -z "$f" ]; then
  for h in /sys/class/hwmon/hwmon*; do
    [ -r "$h/name" ] || continue
    case "$(cat "$h/name")" in
      coretemp|k10temp|cpu_thermal|zenpower)
        for c in "$h"/temp*_input; do
          [ -r "$c" ] && f="$c" && break
        done
        ;;
    esac
    [ -n "$f" ] && break
  done
fi

if [ -z "$f" ]; then
  printf '#[fg=#282a36,bg=#6272a4] |n/a'
  exit 0
fi

t=$(awk '{printf "%.0f", $1/1000}' "$f")

if   [ "$t" -lt 50 ]; then bg='#8be9fd'; ico='🥶'   # cyan   cold
elif [ "$t" -lt 65 ]; then bg='#50fa7b'; ico='😎'   # green  normal
elif [ "$t" -lt 75 ]; then bg='#ffb86c'; ico='🥵'   # orange warm
else                       bg='#ff5555'; ico='🔥'   # red    hot
fi

printf '#[fg=#282a36,bg=%s] |%s%s°C' "$bg" "$ico" "$t"
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

This one bites hard. On a ~40-column phone SSH session the status line
starts wrapping its last 1-2 characters onto a second row, and **every
5-second redraw adds another wrapped row** until the screen is a stack
of half-drawn status bars.

Root cause: **tmux and your terminal disagree on how wide an emoji is.**
tmux measures the status with its own Unicode width table; some emoji it
counts as **1 cell** while your terminal renders them as **2**. tmux
thinks the line fits, doesn't truncate, and the terminal then paints it
1 cell too wide -- and because the status row sits at the bottom with
autowrap on, it wraps and scroll-accumulates on every refresh.

It is **not** all emoji -- only the ones with Unicode
`Emoji_Presentation=No` (legacy "text-presentation" pictographs):
`🌡 ☀ ❄ ♨ ✈ ☁ ❤ ✏`. tmux follows the spec and
counts these **1 cell**; terminals render them as 2. Emoji with
`Emoji_Presentation=Yes` (`🔥 🥵 🥶 😎 💻 🧊 …`) are
counted **2 by tmux**, matching the terminal -- those are safe.

The thermometer `🌡` (U+1F321) is one of the bad ones, which is why an
earlier version of this skill overflowed. **The fix: use an
`Emoji_Presentation=Yes` glyph instead.** The script above picks a
width-2 face per temperature band (🥶/😎/🥵/🔥), so tmux and the
terminal always agree and the status never overflows.

### Things that do NOT work

- **Variation Selector-16 (U+FE0F)**: appending `️` to force emoji
  presentation does *not* change tmux's width count (verified on tmux
  3.6b -- `🌡️` still measures width 1).
- **Trimming spaces**: shaving a space compensates for *one* bad emoji
  but is fragile -- add another text-presentation emoji and it breaks
  again. Fix the glyph, not the spacing.

### Probe any glyph's tmux width

Stash the string in a user option and pad it with `#{p<N>:...}`, which
uses tmux's own width math (a bare literal after `p:` is treated as a
variable name, so the option indirection is required):

```bash
tmux set -g @m '🌡'
tmux display -p '[#{p8:#{@m}}]'   # width = 8 - (trailing spaces)
tmux set -gu @m
```

Width 1 = will overflow on a 2-cell-rendering terminal; width 2 = safe.

### The general cure (terminal side)

The disagreement is really the *terminal* violating Unicode's
default-presentation rule. Many terminals (Blink, Termius, WezTerm,
kitty) expose a Unicode-width / "ambiguous = narrow" setting. Making the
terminal spec-compliant renders text-presentation emoji as 1 cell too --
then tmux and terminal agree for **every** emoji and you can use any
glyph, thermometer included.

## Related

See `tmux-dracula-cpu-temp` for the macOS / Apple Silicon variant
(uses `smctemp` instead of sysfs, with higher temp bands).

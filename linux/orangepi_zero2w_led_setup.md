# Orange Pi Zero 2W - LED Boot Indicator Setup

Configures the green user LED:
- **Blinks on SD card activity** during boot
- **Solid on** once boot is complete

Same idea as the Pi Zero 2W recipe, but Orange Pi has no `config.txt`, so the
boot-time trigger is set via an early systemd unit instead of a dtparam.

## Hardware notes (Zero 2W specific)

- User LED node: `/sys/class/leds/green_led` (not `ACT` / `led0`).
- Red LED next to USB-C is the **power LED**, hardwired to 5V — not
  software-controllable.
- `/sys/class/leds/100m_link` and `100m_act` exist in the device tree but
  the Zero 2W has no ethernet port, so they're not wired to any physical
  LED. Ignore them.

## Setup

### 1. Create `/etc/systemd/system/led-boot-activity.service`:
```ini
[Unit]
Description=Set green LED to mmc0 trigger early in boot
DefaultDependencies=no
After=local-fs.target
Before=basic.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo mmc0 > /sys/class/leds/green_led/trigger'
RemainAfterExit=yes

[Install]
WantedBy=sysinit.target
```

### 2. Create `/etc/systemd/system/led-boot-done.service`:
```ini
[Unit]
Description=Set green LED solid on after boot
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo default-on > /sys/class/leds/green_led/trigger'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

### 3. Enable both:
```bash
sudo systemctl daemon-reload
sudo systemctl enable led-boot-activity.service led-boot-done.service
sudo systemctl start  led-boot-activity.service led-boot-done.service
```

## Inspect / play

```bash
# What's currently driving the LED:
cat /sys/class/leds/green_led/trigger | tr ' ' '\n' | grep '\['

# List of available triggers (load timer module first if you want timer):
sudo modprobe ledtrig-timer
cat /sys/class/leds/green_led/trigger
```

## Available LED Triggers
- `none` - LED off
- `heartbeat` - Blinks like a heartbeat (kernel default on Orange Pi)
- `mmc0` / `mmc1` - Blinks on SD / eMMC activity
- `cpu`, `cpu0`..`cpuN` - CPU activity
- `default-on` - Always on
- `timer` - Custom blink via `delay_on` / `delay_off` (needs `ledtrig-timer`)
- `netdev` - Bind to a netdev (`device_name`, `link`, `tx`, `rx`)

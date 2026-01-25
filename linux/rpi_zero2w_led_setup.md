# Raspberry Pi Zero 2 W - LED Boot Indicator Setup

Configures LED behavior:
- **Blinks on SD card activity** during boot
- **Solid on** once boot is complete

## Setup

### 1. Add to `/boot/firmware/config.txt`:
```
dtparam=act_led_trigger=mmc0
```

### 2. Create `/etc/systemd/system/led-boot-done.service`:
```ini
[Unit]
Description=Set ACT LED solid on after boot
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo default-on > /sys/class/leds/ACT/trigger || echo default-on > /sys/class/leds/led0/trigger'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

### 3. Enable the service:
```bash
sudo systemctl enable led-boot-done.service
```

## Available LED Triggers
- `none` - LED off
- `heartbeat` - Blinks like a heartbeat
- `mmc0` - Blinks on SD card activity
- `cpu` - Blinks based on CPU activity
- `default-on` - Always on

# Optimizing Ubuntu 24.04 on Raspberry Pi Zero 2W

Ubuntu 24.04 on a Pi Zero 2W consumes significantly more resources than Raspbian out of the box (~260 MB vs ~144 MB RSS). This guide documents optimizations to reduce memory and CPU usage on a headless setup.

---

Before proceeding make sure to apply `tmux/attach_on_ssh.md` and `tmux/conf-create_tmux_session_if_none.md`, which will allow long running tasks to continue even if the ssh gets disconnected.

---

## Phase 1: Disable Unnecessary Services

```bash
# Firmware update daemon - not useful on Pi, ~39 MB RAM
sudo systemctl disable --now fwupd.service

# Firmware refresh timer (keeps triggering fwupd)
sudo systemctl disable --now fwupd-refresh.timer

# Authorization manager - not needed if you always use sudo
sudo systemctl disable --now polkit.service
sudo systemctl mask polkit.service

# Automatic updates - manage manually on a Pi
sudo systemctl disable --now unattended-upgrades.service

# Disk manager - ~7 MB RAM (skip if you need USB auto-mount)
sudo systemctl disable --now udisks2.service

# Avahi/mDNS - not needed with Tailscale for discovery
sudo systemctl disable --now avahi-daemon.service avahi-daemon.socket

# Serial console - not needed if SSH-only access
sudo systemctl disable --now serial-getty@ttyS0.service
sudo systemctl mask serial-getty@ttyS0.service

# TTY1 console - headless, no monitor
sudo systemctl mask getty@tty1.service

# Duplicate wpa_supplicant D-Bus service (netplan runs its own via netplan-wpa-wlan0)
# WiFi config: edit /boot/firmware/network-config on SD card (see ubuntu_rpi_offline_wifi_config.md)
sudo systemctl disable --now wpa_supplicant.service

# Crash reporter - not useful on Pi
sudo systemctl disable --now apport.service apport-forward.socket
sudo systemctl mask apport.service

# rsyslog - redundant with journald
sudo systemctl disable --now rsyslog.service rsyslog.socket
```

---

## Phase 2: Disable Unnecessary Timers

```bash
# System stats collection (runs every 10 min)
sudo systemctl disable --now sysstat-collect.timer sysstat-summary.timer

# MOTD news fetching from internet
sudo systemctl disable --now motd-news.timer

# Update notifier timers
sudo systemctl disable --now update-notifier-download.timer update-notifier-motd.timer

# Man page indexing - wastes CPU
sudo systemctl disable --now man-db.timer
```

---

## Phase 3: Disable MOTD Scripts

These run on **every SSH login** and spawn heavy processes:

```bash
# Landscape sysinfo - spawns Python, uses ~39 MB RAM!
sudo chmod -x /etc/update-motd.d/50-landscape-sysinfo

# MOTD news - fetches from internet
sudo chmod -x /etc/update-motd.d/50-motd-news

# Fwupd MOTD - triggers firmware daemon
sudo chmod -x /etc/update-motd.d/85-fwupd
```

---

## Phase 4: Disable Unused Sockets

```bash
# LVM/device-mapper sockets - not using LVM
# Skip if you want LVM support
# sudo systemctl mask dm-event.socket lvm2-lvmpolld.socket

# iSCSI socket - not using network storage
sudo systemctl mask iscsid.socket

# RF kill socket - not toggling wifi/bluetooth
sudo systemctl mask systemd-rfkill.socket

# Legacy init compatibility
sudo systemctl mask systemd-initctl.socket

# System extensions - overlays read-only OS images with additional files
# Safe to disable unless using systemd-sysext for OS layering
sudo systemctl mask systemd-sysext.socket

# LXD installer
sudo systemctl disable --now lxd-installer.socket

# UUID daemon - provides centralized UUID generation
# Most apps use libuuid directly; safe to disable unless specific software requires it
sudo systemctl disable --now uuidd.socket
```

---

## Phase 5: Blacklist Unused Kernel Modules

Create `/etc/modprobe.d/blacklist-bloat.conf`:

```bash
sudo tee /etc/modprobe.d/blacklist-bloat.conf << 'EOF'
# BTRFS - not using, ext4 only
blacklist btrfs

# RAID - not using on SD card
blacklist raid0
blacklist raid1
blacklist raid10
blacklist raid456
blacklist md_mod

# iSCSI / multipath - server stuff
blacklist iscsi_tcp
blacklist libiscsi
blacklist scsi_transport_iscsi
blacklist dm_multipath
EOF
```

Note: Modules may still load from initramfs on first boot. Full effect after `sudo update-initramfs -u`.

---

## Phase 6: Limit Journald Memory

Create `/etc/systemd/journald.conf.d/limit.conf`:

```bash
sudo mkdir -p /etc/systemd/journald.conf.d
sudo tee /etc/systemd/journald.conf.d/limit.conf << 'EOF'
[Journal]
RuntimeMaxUse=10M
EOF
```

**Note**: `SystemMaxUse` defaults to 10% of filesystem or 4GB max - reasonable for SD cards with plenty of space. Adding `MaxLevelStore=warning` would save more space but discards info/debug/notice logs.

---

## Phase 7: Enable Swap and Tune VM Settings

The Pi Zero 2W has only 512 MB RAM. A swap file prevents OOM kills during memory spikes.

```bash
# Create a 1GB swap file
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make persistent across reboots
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

```bash
# Lower swappiness for low RAM systems (default is 60)
echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/99-swappiness.conf
sudo sysctl -w vm.swappiness=10
```

**Note**: `swappiness=10` keeps the system preferring RAM and only swaps under pressure. On an SD card, minimizing swap writes extends card lifespan.

---

## Phase 8: Optional Package Removal

These packages can be removed to save disk space:

```bash
sudo apt remove --purge \
  modemmanager \
  multipath-tools \
  open-iscsi \
  btrfs-progs \
  landscape-common \
  apport apport-symptoms python3-apport

sudo apt autoremove --purge
```

---

## Final Service List (12 services)

After optimization, these services remain:

| Service | Purpose | RAM |
|---------|---------|-----|
| tailscaled | Tailscale VPN | ~41 MB |
| systemd-journald | System logging | ~15 MB |
| systemd-resolved | DNS (needed for Tailscale MagicDNS) | ~12 MB |
| systemd-networkd | Network config | ~9 MB |
| systemd-logind | Login management | ~8 MB |
| systemd-timesyncd | NTP time sync | ~7 MB |
| systemd-udevd | Device management | ~7 MB |
| sshd | SSH server | ~7 MB |
| netplan-wpa-wlan0 | WiFi WPA | ~10 MB |
| dbus | System message bus | ~4 MB |
| cron | Scheduled tasks | ~2 MB |
| user@1000 | User session | ~11 MB |

---

## Verification Commands

```bash
# Check swap
swapon --show

# Check memory usage
free -h

# Total RSS memory by all processes
ps aux | awk '{sum+=$6} END {print "Total RSS: " sum/1024 " MB"}'

# Top memory consumers
ps aux --sort=-%mem | head -20

# List running services
systemctl list-units --type=service --state=running

# List active timers
systemctl list-timers

# Count loaded kernel modules
lsmod | wc -l

# Check for bloat modules still loaded
lsmod | grep -E 'btrfs|bluetooth|raid|dm_mod|fuse'
```

---

## Why Keep These Services

| Service | Why Keep |
|---------|----------|
| **systemd-resolved** | Tailscale MagicDNS requires it |
| **systemd-networkd** | Netplan/Ubuntu networking requires it |
| **systemd-logind** | SSH session management |
| **cron** | Scheduled tasks |

---

## What NOT to Disable

- **systemd-resolved** - Tailscale MagicDNS breaks without it
- **systemd-networkd** - Network won't work (Ubuntu uses netplan)
- **systemd-udevd** - Device hotplug breaks
- **dbus** - Many services require D-Bus
- **ssh** - You'll lock yourself out!
- Personal choices: bluetooth, fuse, LVM

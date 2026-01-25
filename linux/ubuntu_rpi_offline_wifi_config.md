# Offline WiFi Configuration for Ubuntu on Raspberry Pi

Ubuntu on Raspberry Pi uses netplan for network configuration, stored on the ext4 root partition which macOS cannot read natively. This guide enables offline WiFi configuration via the FAT32 boot partition.

## The Problem

- **Boot partition** (`/boot/firmware/`): FAT32 - readable by macOS
- **Root partition** (`/`): ext4 - not readable by macOS without third-party tools
- Ubuntu's netplan config lives on the root partition at `/etc/netplan/50-cloud-init.yaml`
- The `network-config` file on the boot partition is only processed by cloud-init on first boot

## Solution

Create a systemd service that copies `network-config` from the boot partition to netplan on every boot.

### Step 1: Create the Boot Service

```bash
sudo tee /etc/systemd/system/apply-boot-network.service << 'EOF'
[Unit]
Description=Apply network-config from boot partition
Before=network-pre.target
Wants=network-pre.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c "if [ -f /boot/firmware/network-config ]; then cp /boot/firmware/network-config /etc/netplan/50-cloud-init.yaml && netplan generate; fi"
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable apply-boot-network.service
```

### Step 2: Use Plain-Text Password in network-config

Edit `/boot/firmware/network-config` to use a plain-text password (netplan accepts both plain-text and PSK hashes):

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp6: true
      optional: true
  wifis:
    wlan0:
      dhcp4: true
      regulatory-domain: "CA"
      access-points:
        "YourSSID":
          password: "YourPlainTextPassword"
      optional: true
```

## Changing WiFi Settings Offline

1. Remove SD card from Pi
2. Insert into Mac (only the boot partition will mount)
3. Edit `network-config` - change SSID and/or password:
   ```yaml
         "NewNetworkName":
           password: "NewPassword"
   ```
4. Eject and insert SD card back into Pi
5. Boot - the service applies changes before networking starts

## Summary

| File | Location | Purpose |
|------|----------|---------|
| `network-config` | Boot partition (FAT32) | Edit this offline from macOS |
| `50-cloud-init.yaml` | Root partition (ext4) | Copied from network-config on boot |
| `apply-boot-network.service` | systemd | Syncs boot config to netplan |

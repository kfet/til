---
name: shell-docker-run-as-systemd-service
description: "Run a docker container as a systemd service. TIL note about shell. Use when working with shell and the user mentions docker run as systemd service or related topics."
---

# Run a docker container as a systemd service

Wrap the `docker run` in a script, then point a unit at the script. Use
`--rm` so a restart never collides with a leftover container, and let systemd
own the restart policy rather than docker.

Example for the `linuxserver/transmission` image. Substitute your own user and
paths — `$USER`/`$HOME` here, literal values in the unit file:

```bash
cat ~/bin/transmission.sh
#!/bin/sh
docker run --rm \
  -v "$HOME/Downloads/transmission/config:/config" \
  -v "$HOME/Downloads/transmission:/downloads" \
  -v "$HOME/Downloads/transmission/watch:/watch" \
  -e PGID="$(id -g)" -e PUID="$(id -u)" \
  -p 9091:9091 \
  -p 51413:51413 \
  -p 51413:51413/udp \
  --name transmission \
  linuxserver/transmission
```

The unit file cannot expand `$HOME`, so write the absolute path there:

```ini
# /etc/systemd/system/transmission.service
[Unit]
Description=Transmission Torrent Client
After=docker.service
Requires=docker.service

[Service]
ExecStart=/bin/sh -c '/home/YOUR_USER/bin/transmission.sh'
ExecStop=/usr/bin/docker stop transmission
Restart=always
RestartSec=5
User=YOUR_USER
Group=YOUR_USER

[Install]
WantedBy=multi-user.target
```

```bash
chmod +x ~/bin/transmission.sh
sudo systemctl daemon-reload
sudo systemctl enable --now transmission
systemctl status transmission
```

Notes:

- `After=/Requires=docker.service` stops the unit racing the docker daemon at
  boot, which otherwise fails on the first start after a reboot.
- `ExecStop` matters because `docker run` in the foreground does not always
  forward SIGTERM to the container.
- For a rootless alternative, a `~/.config/systemd/user/` unit plus
  `loginctl enable-linger $USER` avoids needing `User=` at all.

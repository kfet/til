# Run a docker container as a systemd service

Example for transmission client linuxserver/transmission:
```bash
cat ~/bin/transsmission.sh
docker run --rm \
-v /home/kfet/Downloads/transmission/config:/config \
-v /home/kfet/Downloads/transmission:/downloads \
-v /home/kfet/Downloads/transmission/watch:/watch \
-e PGID=1000 -e PUID=1000 \
-p 9091:9091 -p 51413:51413 \
-p 51413:51413/udp \
--name transmission \
linuxserver/transmission
```

```bash
cat /etc/systemd/system/transmission.service
[Unit]
Description=Transmission Torrent Client

[Service]
ExecStart=/bin/sh -C '/home/kfet/bin/transmission'
Restart=always
User=kfet
Group=kfet

[Install]
WantedBy=multi-user.target
```

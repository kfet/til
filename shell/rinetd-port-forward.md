# Use rinetd for permanent TCP port forwarding

```bash
sudo apt install rinetd
```

```bash
cat /etc/rinetd.conf

#...
# Add this line to bind to all interfaces:
0.0.0.0 8097 remote-server 8096
```

```bash
sudo systemctl reload rinetd
```
